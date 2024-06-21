# Classy CSV

**Classy CSV is the easiest way to parse your CSV files; you are just one
`dataclass` away from your data.**

The main use case for Classy CSV is to serialize and deserialize tabular data
produced internally by applications you are in control of. By creating a
dataclass that describes the structure of your CSV data, you can seamlessly
convert between CSV files and Python objects.

Data will be read in a _struct-of-arrays_ or _array-of-structs_ manner
depending on your data representation. See the API section for more details.

## Goals and Non-Goals

### Goals
- **Ease of Use:** The primary goal of Classy CSV is to provide a simple and
intuitive way to parse and serialize CSV files using Python's built-in
`dataclass` mechanism.
- **Type Safety and Compatibility:** Classy CSV is designed to play nicely with
type hints, linters, and language server protocols such as pyright and mypy.
This ensures that the code you write is type-safe and can be checked with
standard Python tooling.
- **Zero Dependencies:** Zero worries about dependency issues.

### Non-Goals
- **Performance:** Classy CSV is not optimized for high performance. It is
intended to be used with small CSV files.
- **Error Handling:** Classy CSV is not designed to deal gracefully with malformed
CSV files. It assumes that the input CSV files are well-formed.

## API

Classy CSV exposes the following functions:

- **CSVLine:** A base dataclass for representing a single line in a CSV file.
Each attribute of the dataclass corresponds to a column in the CSV file.
Optional parsers and serializers can be defined for each attribute.
- **CSVColumns:** A base dataclass for representing columns in a CSV file as
lists. Each attribute of the dataclass corresponds to a column in the CSV file
and must be a list. Optional parsers and serializers can be defined for each
attribute. Loaded data using a column format based on this class will be
returned in a _struct-of-arrays_ style.
- **csvfield:** A helper function to add parser and serializer configurations
to fields in `CSVLine` and `CSVColumns`. It works similarly to
`dataclass.field` but provides additional parameters for parsing and
serializing CSV data. It also accepts all the parameters that `field` accepts.
- **dump:** Serialize data to a CSV formatted file. The data can be a list of
`CSVLine` objects or a single `CSVColumns` object.
- **load:** Load data from a CSV formatted file into a list of `CSVLine`
objects or a single `CSVColumns` object, depending on the provided dataclass
type.
- **dumps** and **loads:** Same as `dump` and `load` but instead of writing
into a file handle or reading from it they produce and load from string
representations.

## Example

```python
from pathlib import Path
import dataclasses as dc
from classy_csv import CSVLine, CSVColumns, csvfield, dump, load, loads, dumps

@dc.dataclass
class CustomerData(CSVLine):
    name: str
    age: int = csvfield(parser=int)
    height_m: float = csvfield(parser=float, serializer=lambda x: f"{x:.2f}")
    weight_kg: float = csvfield(parser=float)

rows = [
    CustomerData(name="Jane", age=42, height_m=1.65, weight_kg=58),
    CustomerData(name="Joe", age=36, height_m=1.75, weight_kg=75),
]

# It's important to open files with `newline=""`!
with Path("./example.csv").open(mode="w", newline="") as csvfile:
    dump(csvfile, rows)

with Path("./example.csv").open(mode="r", newline="") as csvfile:
    loaded_rows = load(csvfile, CustomerData)

print(loaded_rows)
# Output: [
#  CustomerData(name='Jane', age=42, height_m=1.65, weight_kg=58),
#  CustomerData(name='Joe', age=36, height_m=1.75, weight_kg=75),
# ]
```

More examples can be found under the `examples/` folder.
