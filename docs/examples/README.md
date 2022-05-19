# molpro-python usage examples

## Extract total energy from a calculation

```python
from molpro import OutputFileParser

def main():
    parser = OutputFileParser()
    output = parser.parse("path/to/file.out")

    if len(output.errors) > 0 or len(output.warnings) > 0:
        print("Detected errors or warnings -> Aborting")
        return
    
    if not output.calculation_finished:
        print("Calculation hasn't finished yet")
        return
    
    # We assume that the relevant calculation was the last
    # program that has been executed
    print("Total energy: " + str(output.programs[-1].output.total_energy))
    print("Used method:  " + output.programs[-1].name)


if __name__ == "__main__":
    main()

```
