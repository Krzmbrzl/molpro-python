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


## Usage

In order to parse a Molpro output file, use the `OutputFileParser` class, which will return an object of type `MolproOutput` that makes the parsed
information available as member variables.
```python
from molpro import OutputFileParser

parser = OutputFileParser()

output = parser.parse("my_output.out")
# Could also directly feed a file-handle or the content of an output file as a string into this method

if output.calculation_finished:
    print("Calculation finished")

if len(output.errors) == 0:
	print("No errors encountered"):
else:
	print("Encountered the following errors:")
	for currentError in output.errors:
		print("  - " + currentError)
```

For more detailed information, please refer to the [docs](docs/) subdirectory.
