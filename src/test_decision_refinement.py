import unittest
import numpy as np
from decision_refinement import interval_winner,enumerate_home

def point(shared,home):
    return {'options':{name:{'installed_cost_interval':{'lower':cost,'upper':cost,'certified_minimum_cost':True}}
                       for name,cost in [('shared',shared),('home',home)]}}

class DecisionEvidenceChecks(unittest.TestCase):
    def test_endpoint_agreement_does_not_prove_interval(self):
        # Homes win at both ends, but monotone costs could be shared=11,
        # home=18 in the middle; therefore no whole-interval certificate.
        self.assertIsNone(interval_winner(point(10,9),point(20,19)))
    def test_cross_endpoint_certificate(self):
        self.assertEqual(interval_winner(point(10,30),point(20,40)),'shared_win')
        self.assertEqual(interval_winner(point(30,10),point(40,20)),'home_win')
        self.assertEqual(interval_winner(point(30,30),point(30,30)),'tie')
    def test_cost_ordered_placement_proof(self):
        # Separate household peaks force a battery at each site. One module
        # each suffices, with two zero-load recharge hours after every peak.
        x=np.zeros((3,9));x[0,0]=4;x[1,3]=4;x[2,6]=4
        r=enumerate_home(x,2,(),30,max_cost=34500)
        self.assertTrue(r['complete']);self.assertEqual(r['result']['cost'],34500)
        self.assertEqual(r['result']['units'].tolist(),[1,1,1])
        self.assertLessEqual(r['result']['grid'].sum(axis=0).max(),2+1e-6)

if __name__=='__main__':unittest.main()
