import unittest
from harbor_pulse.review import fit,predict,pilot_planning,sensitivity
class ReviewTests(unittest.TestCase):
    def test_regression_recovers_known_linear_signal(self):
        x=[[1,i,i*i] for i in range(12)];y=[2+3*i-.5*i*i for i in range(12)]
        self.assertLess(max(abs(a-b) for a,b in zip(predict(x,fit(x,y)),y)),1e-9)
    def test_singular_design_is_visible(self):
        with self.assertRaises(ValueError):fit([[1,1],[1,1]],[2,3])
    def test_zero_realization_has_no_savings_and_capex_is_separate(self):
        r=sensitivity([dict(Vehicles=100,DelayMinutes=10)])['grid'][0]
        self.assertEqual(r['preferred'],'Do not implement')
        self.assertEqual(r['options'][0]['annual_net'],-45000)
        self.assertEqual(r['options'][0]['year_one_cash'],-80000)
    def test_pilot_null_and_alternative_are_distinguished(self):
        r=pilot_planning(500)
        null=next(x for x in r['planning'] if x['post_days']==28 and x['effect_minutes']==0)
        strong=next(x for x in r['planning'] if x['post_days']==28 and x['effect_minutes']==6)
        self.assertLess(null['rejection_rate'],.10);self.assertGreater(strong['rejection_rate'],.95)
        self.assertLess(r['placebo_95'][0],0);self.assertGreater(r['placebo_95'][1],0)
