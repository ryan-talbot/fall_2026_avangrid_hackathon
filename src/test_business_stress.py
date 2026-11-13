import unittest
from business_stress import cost_interval,outcome

class BoundChecks(unittest.TestCase):
    def test_shared_fixed_fee_and_lattice(self):
        # Six 5-kWh blocks cost 19500, plus 15000 fixed. The dual bound
        # includes a small power/throughput tie penalty, not another site fee.
        r={'status':1,'feasible':True,'cost':34500,'mip_dual_bound':19500.2,'max_cap_miss_kw':0,'max_simultaneous_kw':0}
        interval=cost_interval('shared',r,2208)
        self.assertEqual((interval['lower'],interval['upper']),(34500,34500))
    def test_home_bound_rounds_conservatively(self):
        r={'status':1,'feasible':True,'cost':40000,'mip_dual_bound':31500.2,'max_cap_miss_kw':0,'max_simultaneous_kw':0}
        interval=cost_interval('home',r,2208)
        self.assertEqual(interval['lower'],31500)
        self.assertFalse(interval['certified_minimum_cost'])
    def test_straddling_intervals_unresolved(self):
        shared={'lower':34500,'upper':34500,'certified_minimum_cost':True,'proven_infeasible':False}
        home={'lower':31500,'upper':40000,'certified_minimum_cost':False,'proven_infeasible':False}
        self.assertEqual(outcome(shared,home),'unresolved')
        home['lower']=35000
        self.assertEqual(outcome(shared,home),'shared_win')
    def test_simultaneous_incumbent_not_physical_upper(self):
        r={'status':1,'feasible':True,'cost':40000,'mip_dual_bound':31000,'max_cap_miss_kw':0,'max_simultaneous_kw':1}
        self.assertIsNone(cost_interval('home',r,2208)['upper'])

if __name__=='__main__':unittest.main()
