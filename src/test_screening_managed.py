import json
import unittest
import numpy as np
import pandas as pd
from screening import ev_events,weather_features,RULES
from managed_charging import schedule,build_jobs

class ScreeningManagedChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.rules=json.loads(RULES.read_text())
    def test_plateau_component(self):
        x=np.ones(48); x[18:21]=5
        events=ev_events(x,self.rules)
        self.assertEqual(len(events),1)
        self.assertEqual(events[0]['start_slot'],18)
        self.assertEqual(events[0]['duration_hours'],3)
        self.assertAlmostEqual(events[0]['estimated_kwh'],12)
        self.assertEqual(ev_events(np.ones(48),self.rules),[])
        x[19]=np.nan
        self.assertEqual(ev_events(x,self.rules),[])
    def test_daily_weather_signal(self):
        hdd=np.tile(np.arange(20),19)[:365].astype(float)
        cdd=np.maximum(np.roll(hdd,7)-12,0)
        weekend=np.tile([0,0,0,0,0,1,1],53)[:365]
        y=1+.08*hdd+.04*cdd+.2*weekend
        result=weather_features(np.repeat(y,24),np.column_stack([hdd,cdd,weekend]),self.rules)
        self.assertAlmostEqual(result['heating_slope_kw_per_f'],.08)
        self.assertAlmostEqual(result['cooling_slope_kw_per_f'],.04)
        self.assertGreater(result['heating_score'],60)
    def test_deadline_energy_and_rebound(self):
        times=pd.date_range('2026-07-01',periods=48,freq='h')
        x=np.ones((1,48)); x[0,18:21]=5
        original=np.r_[np.full(3,2.),np.zeros(9)]
        shifted,metrics,audit=schedule(x,times,[{'home':0,'hours':list(range(18,30)),'original_mobile':original,'power_kw':2}],3)
        self.assertAlmostEqual(metrics['shifted_kwh'],6,places=6)
        self.assertAlmostEqual(shifted.sum(),x.sum())
        self.assertLessEqual(shifted.max(),3+1e-6)
        self.assertEqual(audit[0]['ready_by'],'2026-07-02 06:00:00')
        np.testing.assert_allclose(shifted[0,:18],x[0,:18])
        np.testing.assert_allclose(shifted[0,30:],x[0,30:])
    def test_no_unnecessary_shift(self):
        times=pd.date_range('2026-07-01',periods=48,freq='h')
        x=np.ones((1,48)); x[0,18:21]=5
        original=np.r_[np.full(3,2.),np.zeros(9)]
        _,metrics,_=schedule(x,times,[{'home':0,'hours':list(range(18,30)),'original_mobile':original,'power_kw':2}],6)
        self.assertAlmostEqual(metrics['shifted_kwh'],0,places=6)
    def test_ready_by_can_leave_cap_miss(self):
        times=pd.date_range('2026-07-01',periods=48,freq='h')
        x=np.ones((1,48)); x[0,28:30]=5
        shifted,metrics,audit=schedule(x,times,[{'home':0,'hours':[28,29],'original_mobile':[2.,2.],'power_kw':2}],3)
        self.assertAlmostEqual(metrics['shifted_kwh'],0)
        self.assertGreater((shifted-3).max(),0)
        self.assertAlmostEqual(audit[0]['energy_error_kwh'],0)
    def test_missing_night_excluded(self):
        x=np.ones((1,8760)); start=6552+18
        x[0,start:start+3]=5; x[0,6552+24]=np.nan
        features=pd.DataFrame({'CUSTOMER_NUMBER':[42],'managed_charging_offer':[True]})
        event={'CUSTOMER_NUMBER':42,'start_slot':start,'duration_hours':3,'baseline_kw':1.,'component_kw':4.}
        _,_,jobs,context=build_jobs(x,[42],features,[event],self.rules)
        self.assertEqual(len(jobs),0)
        self.assertEqual(context['excluded_incomplete_night_windows'],1)

if __name__=='__main__': unittest.main()
