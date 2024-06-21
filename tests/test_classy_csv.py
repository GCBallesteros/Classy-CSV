import dataclasses as dc
import io

from classy_csv import CSVColumns, CSVLine, csvfield, dump, dumps, loads


@dc.dataclass
class SampleLine(CSVLine):
    filename: str
    temp: int = csvfield(parser=int, serializer=lambda x: str(float(x)))


@dc.dataclass
class SampleColumns(CSVColumns):
    filename: list[str] = csvfield(parser=str)
    temp: list[int] = csvfield(parser=int)


def test_csvline_serialization():
    obj = SampleLine(filename="test.csv", temp=25)
    assert obj.serialized_dict() == {"filename": "test.csv", "temp": "25.0"}


def test_csvline_loads():
    csv_data = "filename,temp\ntest.csv,25\nanother.csv,30\n"
    rows = loads(csv_data, SampleLine)
    assert len(rows) == 2
    assert rows[0] == SampleLine(filename="test.csv", temp=25)
    assert rows[1] == SampleLine(filename="another.csv", temp=30)


def test_csvcolumns_serialization():
    obj = SampleColumns(filename=["test.csv", "another.csv"], temp=[25, 30])
    serialized_rows = list(obj.serializer_iterator())
    assert serialized_rows == [
        {"filename": "test.csv", "temp": "25"},
        {"filename": "another.csv", "temp": "30"},
    ]


def test_csvcolumns_loads():
    csv_data = "filename,temp\ntest.csv,25\nanother.csv,30\n"
    cols = loads(csv_data, SampleColumns)
    assert cols.filename == ["test.csv", "another.csv"]
    assert cols.temp == [25, 30]


def test_dump_csvline():
    rows = [
        SampleLine(filename="test.csv", temp=25),
        SampleLine(filename="another.csv", temp=30),
    ]
    buffer = io.StringIO()
    dump(buffer, rows)
    expected_output = "filename,temp\r\ntest.csv,25.0\r\nanother.csv,30.0\r\n"
    assert buffer.getvalue() == expected_output


def test_dump_cscolumns():
    cols = SampleColumns(filename=["test.csv", "another.csv"], temp=[25, 30])
    buffer = io.StringIO()
    dump(buffer, cols)
    expected_output = "filename,temp\r\ntest.csv,25\r\nanother.csv,30\r\n"
    assert buffer.getvalue() == expected_output


def test_dumps_csvline():
    rows = [
        SampleLine(filename="test.csv", temp=25),
        SampleLine(filename="another.csv", temp=30),
    ]
    csv_result = dumps(rows)
    expected_output = "filename,temp\r\ntest.csv,25.0\r\nanother.csv,30.0\r\n"
    assert csv_result == expected_output


def test_dumps_csvcolumns():
    cols = SampleColumns(filename=["test.csv", "another.csv"], temp=[25, 30])
    csv_result = dumps(cols)
    expected_output = "filename,temp\r\ntest.csv,25\r\nanother.csv,30\r\n"
    assert csv_result == expected_output


def test_csvfield():
    @dc.dataclass
    class ExampleLine(CSVLine):
        name: str
        age: int = csvfield(parser=int, serializer=str)
        score: float = csvfield(parser=float, serializer=lambda x: f"{x:.2f}")

    # NOTE: The following line raises a pyright type error but that's okay, we
    # want to check robustness also in this case.
    obj = ExampleLine(name="John", age="25", score="85.567")
    assert obj.age == 25
    assert obj.score == 85.567
    assert obj.serialized_dict() == {"name": "John", "age": "25", "score": "85.57"}
