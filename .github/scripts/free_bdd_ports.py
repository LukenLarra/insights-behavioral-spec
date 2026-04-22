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


def stop_docker_containers_on_port(port: str) -> bool:
    result = subprocess.run(
        ["docker", "ps", "--format", "{{.ID}}\t{{.Ports}}"],
        capture_output=True,
        text=True,
    )
    freed = False
    for line in result.stdout.splitlines():
        parts = line.split("\t", 1)
        if len(parts) != 2:
            continue
        container_id, ports = parts
        if f":{port}->" in ports or f"0.0.0.0:{port}" in ports:
            subprocess.run(["docker", "stop", container_id], capture_output=True)
            print(f"Stopped Docker container {container_id} using port {port}")
            freed = True
    return freed


def free_port(port: str) -> None:
    freed_by_docker = stop_docker_containers_on_port(port)

    result = subprocess.run(["fuser", "-k", f"{port}/tcp"], capture_output=True)
    freed_by_fuser = result.returncode == 0

    if not freed_by_docker and not freed_by_fuser:
        print(f"Port {port} was not in use")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <bdd-config.yml>")
        sys.exit(1)

    for port in get_free_ports(sys.argv[1]):
        free_port(port)
