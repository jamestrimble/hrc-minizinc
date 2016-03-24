# Hospitals/Residents with Couples Modelled using MiniZinc

The Python program `hrc-to-minizinc.py` reads an HRC instance from standard input, and outputs a `.dzn` file to be used with `hrc.mzn`. The program has a required command-line argument: an integer specifying how many blocking pairs the solution should have. To find a stable solution, this should be set to 0. To find a solution with as few blocking pairs as possible, run the program multiple times, setting the argument to 0, 1, ... on successive runs.

Example (to find a solution with exactly one blocking pair, and as many matched residents as possible):

```
python hrc-to-minizinc.py 1 < INSTANCE.txt
```

`hrc-to-minizinc.py` has a flag `--no-presolve` to disable presolve. This usually makes the MiniZinc model much harder to solve.
