import json

from bounded.sinks.csv import CsvSink
from bounded.sinks.jsonl import JsonlSink


def test_csv_sink_writes_header_once_and_appends_rows(tmp_path):
    sink = CsvSink(tmp_path)

    sink.write(["Company", "Summary"], [["Acme", "makes widgets"]], destination="companies")
    sink.write(["Company", "Summary"], [["Globex", "makes gadgets"]], destination="companies")

    content = (tmp_path / "companies.csv").read_text(encoding="utf-8").splitlines()
    assert content == [
        "Company,Summary",
        "Acme,makes widgets",
        "Globex,makes gadgets",
    ]


def test_csv_sink_separates_destinations_into_separate_files(tmp_path):
    sink = CsvSink(tmp_path)
    sink.write(["a"], [["1"]], destination="one")
    sink.write(["a"], [["2"]], destination="two")

    assert (tmp_path / "one.csv").exists()
    assert (tmp_path / "two.csv").exists()


def test_jsonl_sink_appends_one_record_per_row(tmp_path):
    sink = JsonlSink(tmp_path)

    sink.write(["Company", "Summary"], [["Acme", "makes widgets"]], destination="companies")
    sink.write(["Company", "Summary"], [["Globex", "makes gadgets"]], destination="companies")

    lines = (tmp_path / "companies.jsonl").read_text(encoding="utf-8").splitlines()
    records = [json.loads(line) for line in lines]

    assert records == [
        {"Company": "Acme", "Summary": "makes widgets"},
        {"Company": "Globex", "Summary": "makes gadgets"},
    ]
