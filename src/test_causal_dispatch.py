import unittest
import numpy as np
import pandas as pd
from causal_dispatch import replay

class CausalChecks(unittest.TestCase):
    def test_midnight_reserve_and_recharge(self):
        times=pd.date_range('2026-07-03 23:00',periods=8,freq='h')
        r=replay([[6,0,0,0,0,0,0,0]],times,2,[5],[4],eta=1)
        self.assertAlmostEqual(r['soc_end'][0,0],1)
        self.assertAlmostEqual(r['soc_start'][0,1],1)
        self.assertAlmostEqual(r['soc_end'][0,2],5)
        self.assertTrue(r['summary']['overnight_recharge'][-1]['all_sites_full_at_0600'])
        self.assertEqual(r['summary']['hours_above_cap'],0)
    def test_capacity_failure_is_reported(self):
        times=pd.date_range('2026-07-03',periods=3,freq='h')
        r=replay([[5,5,0]],times,2,[4],[10],eta=1)
        self.assertEqual(r['summary']['hours_above_cap'],1)
        self.assertAlmostEqual(r['summary']['worst_miss_kw'],2.8)
    def test_home_no_export(self):
        times=pd.date_range('2026-07-03',periods=2,freq='h')
        r=replay([[0,0],[5,0]],times,2,[10,0],[10,0],eta=1)
        self.assertEqual(r['summary']['hours_above_cap'],1)
        self.assertAlmostEqual(r['summary']['worst_miss_kw'],3)
        self.assertAlmostEqual(r['discharge'].sum(),0)
    def test_future_does_not_change_past(self):
        times=pd.date_range('2026-07-01',periods=4,freq='h')
        a=replay([[5,0,1,2]],times,3,[8],[3])
        b=replay([[5,0,20,20]],times,3,[8],[3])
        for key in ['grid','charge','discharge','soc_end']:
            np.testing.assert_allclose(a[key][:,:2],b[key][:,:2])
    def test_missing_hour_carries_state(self):
        times=pd.date_range('2026-07-01',periods=3,freq='h')
        r=replay([[5,np.nan,0]],times,3,[8],[3])
        self.assertEqual(r['summary']['missing_hours'],1)
        self.assertAlmostEqual(r['soc_end'][0,1],r['soc_end'][0,0])
        self.assertEqual(r['charge'][0,1]+r['discharge'][0,1],0)
    def test_efficiency_and_shared_headroom(self):
        times=pd.date_range('2026-07-01',periods=3,freq='h')
        r=replay([[4,0,0],[4,0,0]],times,4,[5,5],[4,4],eta=.9)
        self.assertAlmostEqual(r['soc_end'][:,0].sum(),10-4/.9)
        self.assertLessEqual(r['grid'].sum(axis=0).max(),4+1e-8)
        self.assertTrue(np.all(r['discharge'][:,0]<=np.array([4,4])))
    def test_recharge_extension_is_not_scored(self):
        times=pd.date_range('2026-07-04 22:00',periods=8,freq='h')
        score=times<pd.Timestamp('2026-07-05')
        r=replay([[0,0,20,20,20,20,20,20]],times,3,[5],[2],score_mask=score)
        self.assertEqual(r['summary']['observed_hours'],2)
        self.assertEqual(r['summary']['hours_above_cap'],0)
        self.assertFalse(r['summary']['overnight_recharge'][-1]['all_sites_full_at_0600'])

if __name__=='__main__': unittest.main()
