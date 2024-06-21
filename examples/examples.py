from pathlib import Path
import dataclasses as dc
from classy_csv import CSVLine, CSVColumns, csvfield, dump, load, loads, dumps


# Example 1: CSVLine
@dc.dataclass
class ExampleLine(CSVLine):
    filename: str
    temp: int = csvfield(parser=int)


def example_csvline():
    rows = [
        ExampleLine(filename="file1.csv", temp=42),
        ExampleLine(filename="file2.csv", temp=36),
    ]

    with Path("./example.csv").open(mode="w", newline="") as csvfile:
        dump(csvfile, rows)

    with Path("./example.csv").open(mode="r", newline="") as csvfile:
        loaded_rows = load(csvfile, ExampleLine)
    print("Deserialized CSVLine from example.csv:", loaded_rows)


# Example 2: CSVColumns
@dc.dataclass
class ExampleCols(CSVColumns):
    filename: list[str] = csvfield(parser=str)
    temp: list[int] = csvfield(parser=int)


def example_csvcolumns():
    # Deserialize from CSV file
    with Path("./example.csv").open(mode="r", newline="") as csvfile:
        loaded_cols = load(csvfile, ExampleCols)
    print("Deserialized CSVColumns from example.csv:", loaded_cols)

    # Serialize to another CSV file
    with Path("./example2.csv").open(mode="w", newline="") as csvfile:
        dump(csvfile, loaded_cols)


# Example 3: Working with CSV Strings
def example_csvstrings():
    rows = [
        ExampleLine(filename="file1.csv", temp=42),
        ExampleLine(filename="file2.csv", temp=36),
    ]

    # Serialize to CSV string
    csv_str = dumps(rows)
    print("Serialized CSVLine to string:")
    print(csv_str)

    # Deserialize from CSV string
    csv_data = "filename,temp\ntest.csv,25\nanother.csv,30\n"
    loaded_rows = loads(csv_data, ExampleLine)
    print("Deserialized CSVLine from string:", loaded_rows)


def run_examples():
    example_csvline()
    example_csvcolumns()
    example_csvstrings()


if __name__ == "__main__":
    run_examples()
