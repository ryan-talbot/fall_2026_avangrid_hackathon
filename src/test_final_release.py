import json
import tempfile
import unittest
from pathlib import Path
from final_analysis import crf
from load_data import raw_fingerprint,validate_cache_guard

class FinalReleaseChecks(unittest.TestCase):
    def test_annual_cost_equivalence(self):
        # At 0% and 15 years, $9,000 up front is $600/year.
        self.assertAlmostEqual((60000-51000)*crf(0,15),600)
        # A recurring $1,000 at 10% over two years has PV 1,735.54.
        self.assertAlmostEqual(1000/crf(.1,2),1000/1.1+1000/1.1**2)
        for rate in [0,.05,.08]:
            maximum=60000-500/crf(rate,15)
            self.assertAlmostEqual(maximum*crf(rate,15)+500,60000*crf(rate,15))
    def test_changed_ami_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d);raw=folder/'input.zip';raw.write_bytes(b'original')
            guard=folder/'guard.json';guard.write_text(json.dumps({'raw_zip_stat':raw_fingerprint(folder)}))
            validate_cache_guard(folder,guard)
            raw.write_bytes(b'changed size')
            with self.assertRaisesRegex(ValueError,'AMI input files changed'):
                validate_cache_guard(folder,guard)

if __name__=='__main__':unittest.main()
