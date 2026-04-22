#!/usr/bin/env python3
"""Free ports listed in the free_ports field of a BDD config YAML."""

import re
import subprocess
import sys


def get_free_ports(config_path: str) -> list[str]:
    with open(config_path) as f:
        content = f.read()
    match = re.search(r"free_ports\s*:\s*([0-9, ]+)", content)
    if not match:
        return []
    return match.group(1).replace(",", " ").split()


def free_port(port: str) -> None:
    result = subprocess.run(["fuser", "-k", f"{port}/tcp"], capture_output=True)
    if result.returncode == 0:
        print(f"Freed port {port}")
    else:
        print(f"Port {port} was not in use")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <bdd-config.yml>")
        sys.exit(1)

    for port in get_free_ports(sys.argv[1]):
        free_port(port)
