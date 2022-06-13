# molpro-python parser framework

## General idea

The general idea of this parser framework that generally Molpro output files have two structural levels: The global structure, indicating e.g. where
different program outputs start and begin, and the local structure which is unique for each individual program run through Molpro.

Likewise, the parser framework mirrors this split in responsibility. The `OutputFileParser` class is responsible for recognizing the output's global
structure. The most important pieces of information it extracts is where the different program outputs start and end and how long each of these
programs took (CPU time + wall time). It also tries to recognize some common error and warning reporting patterns used in Molpro outputs in order to
detect these in a program-independent manner.

Once the global structure has been parsed, the `OutputFileParser` will automatically delegate the parsing of each individual program output by means
of a dedicated parser. These parsers are specifically crafted for each program so that they understand the exact output format for that particular
program. Their job is to extract the detailed information provided by the program (e.g. resulting total and correlation energy, runtime per iteration,
etc.).


## Usage

In order to use the parser framework to parse a Molpro output file, you have to create a `MolproOutputParser` and call `parse` on it. As an argument
you can either pass a path to a file, an opened file handle or a string representing the file's content.
```python
from molpro import OutputFileParser

def main():
    parser = OutputFileParser()
    output = parser.parse("./path_to_my_output_file.out")
```

Calling this function will either raise a `MolproError`, in case the provided output file could not be parsed or it will return an object of type
`MolproOutput`. It contains member fields for all information that was extracted during parsing the output. You can find a full list of member fields
[here](../../modules/molpro/MolproOutput.py) but the most important ones are
- `calculation_finished`: Boolean flag indicating whether the calculation whose output has been parsed has already completed. Note: The parsers are
  specifically crafted to fully support parsing incomplete outputs (outputs of calculations that are still running).
- `version`: The version of Molpro that has been used to generate this output.
- `errors`: A list of errors that Molpro has emitted during the calculation.
- `warnings`: A list of warnings that Molpro has emitted during the calculation.
- `point_group`: The point group of the molecule that has been calculated. Note that the parser currently assumes that the point group does not change
  throughout the calculation. If it did, then this field would hold the _last_ used point group.
- `programs`: A list of individual programs that have been executed in this Molpro calculation. These objects of type `Proram` will hold the
  corresponding parsed output of the respective program run.

Every entry in `output.programs` is of type `Program` which itself has a member `output` which will hold the parsed contents of this program's output.
Note that this only applies if there was a dedicated parser available for this particular program. If not, this field will be `None`.

Each of the individual program's outputs is represented as a `ParserData` object. More specifically, each program-specific parser will also produce a
program-specific output object. So a `CMRCC_Parser` will produce a `CMRCC_Data` object, a `RHF_Parser` will produce a `RHF_Data` object and so on. To
see which fields are available in the different `ParserData` subclasses, have a look at the respective `*_Data` classes.

Available program parsers:
| **Program** | **Parser**                                             | **Data object**                                     |
| ----------- | ------------------------------------------------------ | --------------------------------------------------- |
| CCSD        | [CCSD_Parser](../../modules/molpro/CCSD_Parser.py)     | [CCSD_Data](../../modules/molpro/CCSD_Data.py)      |
| CIC         | [CIC_Parser](../../modules/molpro/CIC_Parser.py)       | [CIC_Data](../../modules/molpro/CIC_Data.py)        |
| CMRCC       | [CMRCC_Parser](../../modules/molpro/CMRCC_Parser.py)   | [CMRCC_Data](../../modules/molpro/CMRCC_Data.py)    |
| MULTI       | [MULTI_Parser](../../modules/molpro/MULTI_Parser.py)   | [MULTI_Data](../../modules/molpro/MULTI_Data.py)    |
| RHF         | [RHF_Parser](../../modules/molpro/RHF_Parser.py)       | [RHF_Data](../../modules/molpro/RHF_Data.py)        |
| SEWARD      | [SEWARD_Parser](../../modules/molpro/SEWARD_Parser.py) | [SEWARD_Data](../../modules/molpro/SEWARD_Data.py)  |


## Duck-typing

Wherever possible (and sensible), the `*_Data` classes support [duck typing](https://realpython.com/lessons/duck-typing/). That means that e.g. the
`CCSD_Data` and the `CMRCC_Data` both have member fields `total_energy` and `correlation_energy` so if you know that the current data object is one of
the two, you can just access this member field and not worry about which type the data object actually is of.


## Writing new program parsers

When implementing a new program parser, orient yourself at the existing implementations. It is important that your parser class inherits from
`ProgramParser` and your data class inherits from `ProgramData`. Furthermore, the parser class requires a `@register_program_parser` annotation in
order for the `OutputFileParser` to be aware of the parser's existence.

For actual parsing there are several utility methods available in the `utils` package. In particular it contains a method for generically parsing what
is referred to as "iteration tables" (aka the tables where a method prints some stats for every iteration).
