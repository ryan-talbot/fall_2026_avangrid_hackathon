"""One-command local audit, hand tests, and showcase replay."""
import unittest
from inventory import inventory, materials
from test_model import HandCases
from showcase import main, arguments
from report import report

if __name__=='__main__':
    args=arguments()
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(HandCases))
    if not result.wasSuccessful(): raise SystemExit(1)
    inventory()
    materials()
    dest=main(args.ids_config,args.output_dir,args.check_inputs_only)
    if not args.check_inputs_only: report(dest)
