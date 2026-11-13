import unittest
import numpy as np
from model import diversity, dispatch, home_cost_bound, home_design

class HandCases(unittest.TestCase):
    def test_site_bound(self):
        x=np.eye(3)*4
        self.assertEqual(home_cost_bound(x,2),{'modules':3,'sites':3,'cost':34500})
        self.assertEqual(home_cost_bound(x,2,export=True),{'modules':1,'sites':1,'cost':11500})
    def test_enumeration_replay(self):
        r=home_design([[0,0,0],[4,0,0]],2)
        self.assertEqual(r['cost'],11500)
        self.assertEqual(r['units'].tolist(),[0,1])
        self.assertLessEqual(r['grid'].sum(axis=0).max(),2+1e-7)
        self.assertAlmostEqual(r['soc'][1,-1],10.08)
    def test_energy_bound(self):
        # Eight 2kW deficits need 16 AC kWh; two modules provide only
        # 20.16*.8*sqrt(.894) = 15.25 AC kWh above reserve.
        r=home_design([[5]*8+[0]*4,[5]*8+[0]*4],8)
        self.assertEqual(r['cost'],31500)
        self.assertEqual(sum(r['units']),3)
        self.assertEqual(r['necessary_equipment_bound']['sites'],2)
        checks=r['necessary_equipment_bound']['aggregate_energy_checks']
        self.assertEqual([(v['modules'],v['feasible']) for v in checks],[(1,False),(2,False),(3,True)])
    def test_diversity(self):
        self.assertEqual(diversity([[4,0],[0,4]]),2)
        self.assertEqual(diversity([[4,0],[4,0]]),1)
    def test_reserve(self):
        self.assertFalse(dispatch([[6,0]],2,energy=[4],power=[10],reserve=.2,eta=1)['feasible'])
        r=dispatch([[5,0]],2,energy=[4],power=[10],reserve=.2,eta=1)
        # Cap leaves only 2kWh recharge, insufficient for 3kWh discharge.
        self.assertFalse(r['feasible'])
        r=dispatch([[5,0,0]],2,energy=[4],power=[10],reserve=.2,eta=1)
        self.assertTrue(r['feasible']); self.assertAlmostEqual(r['soc'][0,0],1)
    def test_no_export(self):
        # Battery at empty home cannot shave its neighbor without export.
        self.assertFalse(dispatch([[0,0],[4,0]],2,energy=[4,0],power=[4,0],eta=1)['feasible'])
        self.assertTrue(dispatch([[0,0],[4,0]],2,energy=[4,0],power=[4,0],eta=1,export=True)['feasible'])
    def test_midnight_and_losses(self):
        # 23:00 demand, midnight and 01:00 recharge. AC efficiency .81.
        r=dispatch([[4,0,0]],2,energy=[5],power=[2],eta=.9)
        self.assertTrue(r['feasible'])
        self.assertAlmostEqual(r['soc'][0,0],5-2/.9)
        self.assertAlmostEqual(r['charge'][0,1:].sum(),2/.81)
        self.assertAlmostEqual(r['soc'][0,-1],5)
        self.assertLessEqual(r['grid'].max(),2+1e-7)
    def test_power(self):
        self.assertFalse(dispatch([[4,0,0]],2,energy=[20],power=[1],eta=1)['feasible'])
    def test_design_and_gaps(self):
        for mode,expected in [('home',11500),('shared',18250)]:
            r=dispatch([[4,0,0,4,0,0]],2,optimize=mode,breaks=[3])
            self.assertEqual(r['status'],0)
            self.assertEqual(r['cost'],expected)
            self.assertEqual(r['units'].tolist(),[1])
            self.assertAlmostEqual(r['soc'][0,2],r['energy_kwh'][0])
            self.assertLess(r['max_balance_residual_kwh'],1e-8)

if __name__=='__main__': unittest.main()
