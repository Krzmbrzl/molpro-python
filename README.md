# molpro-python
Python scripts and modules facilitating the use of the Molpro quantum chemistry program package

To make use of these scripts and modules, clone this repository to your local machine and then add the `modules` directory to your `PYTHONPATH` and
the `bin` directory to your `PATH`. Assuming you have cloned this repo to `~/molpro-python`, add the following to your `.bashrc`:
```bash
export PATH="$HOME/molpro-python/bin:$PATH"
export PYTHONPATH="$HOME/molpro-python/modules:$PYTHONPATH"
```

## Running tests

In order to run the test cases, use the `run_tests.py` script. This will allow you to run the tests, without having to modify your `PYTHONPATH`
beforehand.
