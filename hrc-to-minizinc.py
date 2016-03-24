import argparse
import sys

import hrc_instance
            
def main(lines, max_bp, quiet, presolve):
    instance = hrc_instance.Instance(lines, max_bp, presolve)
    instance.write_dzn()
    #instance.write(quiet)

if __name__=="__main__":
    parser = argparse.ArgumentParser("Translate a MIN BP HRC instance to .opb format")
    parser.add_argument("max_bp", type=int,
            help="The maximum permitted number of blocking pairs")
    parser.add_argument("--quiet", "-q", action="store_true", required=False,
            help="Suppress most comments in output")
    parser.add_argument("--flatzinc", "-f", action="store_true", required=False,
            help="Output FlatZinc")
    parser.add_argument("--no-presolve", action="store_true", required=False,
            help="Disable presolve")
    args = parser.parse_args()
    
    main([line.strip() for line in sys.stdin.readlines() if line.strip()],
            args.max_bp, args.quiet, not args.no_presolve)
