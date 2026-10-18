"""System inventory collector: local-only hardware/OS/package snapshot.

Writes JSON or CSV to stdout or a local file. Makes no network connections.
Uses psutil when installed; falls back to the standard library otherwise.
Hostname is excluded by default (use --include-hostname to add it).
"""
import argparse
import csv
import io
import json
import os
import platform
import shutil
import sys
from importlib import metadata

try:
    import psutil
except ImportError:  # pragma: no cover
    psutil = None


def os_info(include_hostname=False):
    info = {"system": platform.system(), "release": platform.release(),
            "version": platform.version(), "machine": platform.machine(),
            "python": platform.python_version()}
    if include_hostname:
        info["hostname"] = platform.node()
    return info


def cpu_info():
    info = {"logical_cores": os.cpu_count()}
    if psutil:
        info["physical_cores"] = psutil.cpu_count(logical=False)
    return info


def memory_info():
    if psutil:
        vm = psutil.virtual_memory()
        return {"total_gb": round(vm.total / 1024**3, 2),
                "available_gb": round(vm.available / 1024**3, 2)}
    return {"total_gb": None, "available_gb": None}


def disk_info(path=None):
    path = path or os.path.abspath(os.sep)
    u = shutil.disk_usage(path)
    return {"path": path, "total_gb": round(u.total / 1024**3, 2),
            "used_gb": round(u.used / 1024**3, 2),
            "free_gb": round(u.free / 1024**3, 2)}


def python_packages():
    pkgs = {}
    for d in metadata.distributions():
        name = d.metadata["Name"]
        if name:
            pkgs[name] = d.version
    return dict(sorted(pkgs.items(), key=lambda kv: kv[0].lower()))


def collect(include_hostname=False, include_packages=True):
    data = {"os": os_info(include_hostname), "cpu": cpu_info(),
            "memory": memory_info(), "disk": disk_info()}
    if include_packages:
        data["python_packages"] = python_packages()
    return data


def flatten(data, prefix=""):
    """Flatten nested dict to (key, value) rows for CSV."""
    rows = []
    for k, v in data.items():
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            rows.extend(flatten(v, key + "."))
        else:
            rows.append((key, v))
    return rows


def to_csv(data):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["key", "value"])
    w.writerows(flatten(data))
    return buf.getvalue()


def main(argv=None):
    ap = argparse.ArgumentParser(description="Collect a local system inventory.")
    ap.add_argument("--format", choices=["json", "csv"], default="json")
    ap.add_argument("--output", help="write to this local file instead of stdout")
    ap.add_argument("--include-hostname", action="store_true")
    ap.add_argument("--no-packages", action="store_true", help="omit the installed Python package list")
    ap.add_argument("--force", action="store_true", help="overwrite --output if it already exists")
    args = ap.parse_args(argv)
    data = collect(args.include_hostname, not args.no_packages)
    text = json.dumps(data, indent=2) if args.format == "json" else to_csv(data)
    if args.output:
        if os.path.exists(args.output) and not args.force:
            print(f"error: {args.output} exists (use --force to overwrite)", file=sys.stderr)
            return 2
        try:
            fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)  # owner-only
            with os.fdopen(fd, "w", newline="") as f:
                f.write(text)
        except OSError as e:
            print(f"error: cannot write {args.output}: {e}", file=sys.stderr)
            return 2
    else:
        sys.stdout.write(text + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
