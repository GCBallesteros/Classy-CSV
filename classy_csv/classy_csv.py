import csv
import dataclasses as dc
import io
from typing import Any, Callable, Iterator, Type, TypeVar, overload

# TODO: docstring for dumps
# TODO: We need tests

__all__ = ["CSVLine", "CSVColumns", "csvfield", "load", "loads", "dump", "dumps"]


def _check_all_annotations_are_list(row_class) -> bool:
    # Check they are all lists as required
    for col in dc.fields(row_class):
        if not _check_if_is_generic_list(col.type):
            return False
    return True


def _unwrap_list(list_generic):
    return list_generic.__args__[0]


def _check_if_is_generic_list(maybe_generic_list) -> bool:
    try:
        origin = maybe_generic_list.__origin__
    except Exception:
        origin = None

    if origin is not None:
        if origin is list:
            pass
        else:
            return False
    else:
        return False
    return True


@dc.dataclass
class CSVLine:
    """
    A base dataclass for representing a single line in a CSV file.

    Attributes of the dataclass should correspond to columns in the CSV file.
    Each attribute can have an optional parser function defined via the
    `csvfield` function which will be applied to the corresponding columns
    value upon initialization. If no parser is specified, the value will be
    kept as a string.

    Example
    -------
    ```python
    import dataclasses as dc
    from pathlib import Path
    from classy_csv import CSVLine, csvfield, dump, load

    @dc.dataclass
    class Example(CSVLine):
        filename: str
        temp: int = csvfield(parser=int, serializer=lambda x: str(float(x)))

    rows = [
        Example(filename="file1.csv", temp=42),
        Example(filename="file2.csv", temp=36)
    ]

    # Serialize to CSV
    with Path("./example.csv").open(mode="w", newline="") as csvfile:
        dump(csvfile, rows)

    # Deserialize from CSV
    with Path("./example.csv").open(mode="r", newline="") as csvfile:
        loaded_rows = load(csvfile, Example)
    ```
    """

    def __post_init__(self):
        for field_ in dc.fields(self):
            field_name = field_.name
            if "_parser" in field_.metadata:
                parser = field_.metadata["_parser"]
            else:
                parser = lambda x: x  # noqa: E731

            setattr(self, field_name, parser(getattr(self, field_name)))

            if not isinstance(getattr(self, field_name), field_.type):
                e_ = f"Parsed value for {field_name} didn't match the expected type {field_.type}"
                raise ValueError(e_)

    def serialized_dict(self) -> dict[str, str]:
        fields = dc.fields(self)
        serializers = {}
        for f in fields:
            if "_serializer" in f.metadata:
                serializer = f.metadata["_serializer"]
            else:
                serializer = lambda x: str(x)  # noqa: E731
            serializers[f.name] = serializer

        return {f.name: serializers[f.name](getattr(self, f.name)) for f in fields}


@dc.dataclass
class CSVColumns:
    def __post_init__(self):
        for field_ in dc.fields(self):
            field_name = field_.name
            if "_parser" in field_.metadata:
                parser = field_.metadata["_parser"]
            else:
                parser = lambda x: x  # noqa: E731

            if _check_if_is_generic_list(field_.type):
                inner_type = _unwrap_list(field_.type)
            else:
                raise ValueError("Value should be list")

            setattr(self, field_name, [parser(x) for x in getattr(self, field_name)])

            for x in getattr(self, field_name):
                if not isinstance(x, inner_type):
                    e_ = f"Parsed value for {field_name} didn't match the expected type {inner_type}"
                    raise ValueError(e_)

    def __iter__(self) -> Iterator[dict[str, Any]]:
        fields = dc.fields(self)

        some_attr = fields[0].name
        n_elements = len(getattr(self, some_attr))

        for i in range(n_elements):
            yield {f.name: getattr(self, f.name)[i] for f in fields}

    def serializer_iterator(self) -> Iterator[dict[str, str]]:
        fields = dc.fields(self)

        serializers = {}
        for f in fields:
            if "_serializer" in f.metadata:
                serializer = f.metadata["_serializer"]
            else:
                serializer = str
            serializers[f.name] = serializer

        some_attr = fields[0].name
        n_elements = len(getattr(self, some_attr))

        for i in range(n_elements):
            yield {
                f.name: serializers[f.name](getattr(self, f.name)[i]) for f in fields
            }


T = TypeVar("T", bound="CSVLine")
U = TypeVar("U", bound="CSVColumns")


def csvfield(
    parser: Callable[[Any], Any] = lambda x: x,
    serializer: Callable[[Any], str] = lambda x: str(x),
    **kwargs,
) -> Any:
    """
    Additional configuration for annotations of CSVLine and CSVColumns.

    This function works similarly to `dataclasses.field` but provides additional
    parameters for parsing and serializing CSV data specific to `CSVLine` and `CSVColumns`.

    Parameters
    ----------
    parser
        A function that takes the output from the Python standard library `csv`
        reader and post-processes it to match the expected type for the
        corresponding class attribute.

    serializer
        A function that turns the value back into a string for dumping it into a
        CSV text file. Defaults to `str`.

    **kwargs
    Additional keyword arguments passed directly to the underlying `dataclasses.field` call.

    Returns
    -------
    A configured dataclass field with metadata for parsing and serializing.

    Example
    -------
    ```python
    @dataclass
    class Example(CSVLine):
        name: str
        age: int = csvfield(parser=int, serializer=str)
        score: float = csvfield(parser=float, serializer=lambda x: f"{x:.2f}")
    ```
    In this example, the `age` field will be parsed as an integer and
    serialized as a string, while the `score` field will be parsed as a float
    and serialized as a string with two decimal places.
    """
    if "metadata" not in kwargs:
        metadata = {}
    else:
        metadata = kwargs["metadata"]

    return dc.field(
        **kwargs,
        metadata=metadata | {"_parser": parser, "_serializer": serializer},
    )


@overload
def load(csvfile: io.TextIOWrapper, row_class: Type[T]) -> list[T]: ...


@overload
def load(csvfile: io.TextIOWrapper, row_class: Type[U]) -> U: ...


def load(csvfile: io.TextIOWrapper, row_class: Type[T] | Type[U]) -> list[T] | U:
    """
    Load a CSV file given a definition of its columns as a CSVLine or CSVColumns.

    Parameters
    ----------
    csvfile
        A file handle to a text CSV file opened in read mode.

    row_class
        The dataclass type defining the structure of the CSV file. This can be a
        subclass of either `CSVLine` or `CSVColumns`.

        - If a subclass of `CSVLine` is provided, the function returns a list of instances
          of that class, with each instance representing a row in the CSV file.
        - If a subclass of `CSVColumns` is provided, the function returns a single instance
          of that class, where each attribute is a list containing the values of the respective
          column in the CSV file.

    Returns
    -------
    list[CSVLine] | CSVColumns
        A list of instances of the provided `CSVLine` subclass or a single instance of the provided
        `CSVColumns` subclass.

    Raises
    ------
    ValueError
        - If the CSV file does not have the expected columns as defined in the `row_class`.
        - If the provided `row_class` is a subclass of `CSVColumns` and not all annotations are lists
          as expected.

    Example
    -------
    ```python
    @dataclass
    class Example(CSVLine):
        filename: str
        temp: int = csvfield(parser=int)

    rows = [
        Example(filename="file1.csv", temp=42),
        Example(filename="file2.csv", temp=36)
    ]

    # Serialize to CSV
    with open("example.csv", mode="w", newline="") as csvfile:
        dump(csvfile, rows)

    # Deserialize from CSV
    with open("example.csv", mode="r", newline="") as csvfile:
        loaded_rows = load(csvfile, Example)

    print(loaded_rows)
    # [Example(filename='file1.csv', temp=42), Example(filename='file2.csv', temp=36)]

    @dataclass
    class ExampleCols(CSVColumns):
        filename: list[str] = csvfield(parser=str)
        temp: list[int] = csvfield(parser=int)

    # Deserialize as CSVColumns
    with open("example.csv", mode="r", newline="") as csvfile:
        loaded_cols = load(csvfile, ExampleCols)

    print(loaded_cols)
    # ExampleCols(filename=['file1.csv', 'file2.csv'], temp=[42, 36])
    ```
    """
    expected_columns = [f.name for f in dc.fields(row_class)]
    reader = csv.DictReader(csvfile)

    if reader.fieldnames is None or set(expected_columns) != set(reader.fieldnames):
        raise ValueError(
            f"CSV file does not have the expected columns: {expected_columns}"
        )

    if issubclass(row_class, CSVLine):
        rows = [row_class(**x) for x in reader]

        return rows

    elif issubclass(row_class, CSVColumns):
        if not _check_all_annotations_are_list(row_class):
            e_ = f"All fields of {row_class} should be list"
            raise ValueError(e_)

        csv_columns: dict[str, list[Any]] = {col: [] for col in expected_columns}
        for row in reader:
            for col in expected_columns:
                csv_columns[col].append(row[col])

        return row_class(**csv_columns)


@overload
def loads(csvfile: str, row_class: Type[T]) -> list[T]: ...


@overload
def loads(csvfile: str, row_class: Type[U]) -> U: ...


def loads(csvfile: str, row_class: Type[T] | Type[U]) -> list[T] | U:
    """Load data from CSV formatted string.

    See `load` for more details.
    """
    return load(io.StringIO(csvfile), row_class)


def dump(csvfile: io.TextIOWrapper, rows: list[T] | CSVColumns) -> None:
    """
    Serialize to CSV formatted file.

    Parameters
    ----------
    dump
        A file handle to a text file. It has to be opened using the `newline=""`
        argument.
    rows
        The data to serialize. This can be a list of instances of a `CSVLine` subclass
        or a single instance of a `CSVColumns` subclass.

    Returns
    -------
        A string containing the CSV formatted data.

    Example
    -------
    ```python
    @dataclass
    class Example(CSVLine):
        filename: str
        temp: int = csvfield(parser=int, serializer=lambda x: str(float(x)))

    rows = [
        Example(filename="file1.csv", temp=42),
        Example(filename="file2.csv", temp=36)
    ]

    with Path("./example").open(mode="w", newline="") as csvfile:
        dump(csvfile, rows)
    # File ./example
    # filename,temp
    # file1.csv,42.0
    # file2.csv,36.0
    ```
    """
    if isinstance(rows, list):
        row_class = type(rows[0])

        expected_columns = [f.name for f in dc.fields(row_class)]
        csvwriter = csv.DictWriter(csvfile, fieldnames=expected_columns)
        csvwriter.writeheader()
        for row in rows:
            if not isinstance(row, row_class):
                e_ = f"One of the rows is not of type {row_class}"
                raise ValueError(e_)
            out_dict = row.serialized_dict()
            csvwriter.writerow(out_dict)

    elif isinstance(rows, CSVColumns):
        expected_columns = [f.name for f in dc.fields(rows)]
        csvwriter = csv.DictWriter(csvfile, fieldnames=expected_columns)
        csvwriter.writeheader()

        for row in rows.serializer_iterator():
            csvwriter.writerow(row)


def dumps(rows: list[T] | CSVColumns) -> str:
    csv_output = io.StringIO()
    dump(csv_output, rows)

    return csv_output.getvalue()


if __name__ == "__main__":
    from pathlib import Path

    @dc.dataclass
    class Example(CSVLine):
        filename: str
        temp: int = csvfield(parser=int, serializer=lambda x: str(float(x)))

    @dc.dataclass
    class ExampleCol(CSVColumns):
        filename: list[str] = csvfield(parser=str)
        temp: list[float] = csvfield(parser=float, serializer=lambda x: str(float(x)))

    rows = [
        Example(filename="asdf", temp=6),
        Example(filename="ssdf", temp=5),
        Example(filename="dsdf", temp=4),
        Example(filename="fsdf", temp=3),
    ]
    with Path("./example").open(mode="w", newline="") as csvfile:
        dump(csvfile, rows)
    with Path("./example").open(mode="r", newline="") as csvfile:
        asF = load(csvfile, ExampleCol)
        print(asF)
    with Path("./example2").open(mode="w", newline="") as csvfile:
        dump(csvfile, asF)
