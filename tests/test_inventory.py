import json
import socket
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import inventory as inv


def test_collect_has_sections():
    d = inv.collect()
    assert {"os", "cpu", "memory", "disk", "python_packages"} <= set(d)
    assert d["disk"]["total_gb"] > 0


def test_hostname_excluded_by_default():
    assert "hostname" not in inv.collect()["os"]
    assert "hostname" in inv.collect(include_hostname=True)["os"]


def test_json_serializable():
    json.dumps(inv.collect())


def test_csv_flatten():
    out = inv.to_csv({"a": {"b": 1}, "c": 2})
    assert out.splitlines() == ["key,value", "a.b,1", "c,2"]


def test_no_network_used(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("network used")
    monkeypatch.setattr(socket.socket, "connect", boom)
    inv.collect()


def test_output_file(tmp_path):
    f = tmp_path / "inv.json"
    inv.main(["--output", str(f)])
    assert "os" in json.loads(f.read_text())
