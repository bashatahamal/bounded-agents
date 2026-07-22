import base64
import json

import pytest

from bounded.credentials import load_json_credentials


def test_load_json_credentials_from_raw_json_string():
    raw = json.dumps({"type": "service_account", "project_id": "x"})
    assert load_json_credentials(raw) == {"type": "service_account", "project_id": "x"}


def test_load_json_credentials_from_base64_string():
    payload = {"type": "service_account", "project_id": "x"}
    encoded = base64.b64encode(json.dumps(payload).encode("utf-8")).decode("ascii")
    assert load_json_credentials(encoded) == payload


def test_load_json_credentials_from_file_path(tmp_path):
    payload = {"type": "service_account", "project_id": "x"}
    path = tmp_path / "creds.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    assert load_json_credentials(str(path)) == payload


def test_load_json_credentials_raises_on_garbage():
    with pytest.raises(ValueError):
        load_json_credentials("not json, not a path, not base64 json {{{")


def test_load_json_credentials_raises_when_json_is_not_an_object():
    with pytest.raises(ValueError):
        load_json_credentials("[1, 2, 3]")
