"""Parse BDD config files and generate a GitHub Actions job matrix.

Scans all ``*-framework.yml`` files under the given config directory,
extracts service metadata from each one, and writes a JSON matrix and a
``has_services`` flag to ``$GITHUB_OUTPUT`` so the calling workflow can
conditionally fan out to per-service jobs.
"""

import glob
import json
import os
import re
from dataclasses import asdict, dataclass


def extract(content: str, field: str) -> str | None:
    """Extract a scalar YAML field value from raw file content.

    Supports double-quoted, single-quoted, and bare (unquoted) values.
    Returns ``None`` when the field is not present.
    """
    pattern = r"^\s*" + re.escape(field) + r'\s*:\s*(?:"([^"]+)"|\'([^\']+)\'|([^\s\n]+))'
    match = re.search(pattern, content, re.MULTILINE)
    if match:
        return match.group(1) or match.group(2) or match.group(3)
    return None


@dataclass
class ServiceConfig:
    """All metadata needed to run BDD tests for a single service.

    Using a dataclass instead of a plain dict ensures every consumer of the
    matrix sees the same set of fields and their expected types.
    """

    repo: str
    service: str
    config: str
    profile: str
    build_go: bool
    service_package: str
    binary_repo: str


def build_matrix(config_dir: str = "bdd-configs") -> list[ServiceConfig]:
    """Return a :class:`ServiceConfig` list built from ``*-framework.yml`` files.

    Files that are missing either ``repo`` or ``service`` are silently skipped.
    """
    services = []
    for file in glob.glob(os.path.join(config_dir, "*-framework.yml")):
        with open(file, encoding="utf-8") as f:
            content = f.read()

        repo = extract(content, "repo")
        service = extract(content, "service")

        if repo and service:
            build_go = str(extract(content, "build_go") or "").lower() == "true"
            binary_repo = extract(content, "binary_repo") or ""

            services.append(
                ServiceConfig(
                    repo=repo,
                    service=service,
                    config=os.path.basename(file),
                    profile=extract(content, "docker_profile") or "",
                    build_go=build_go,
                    service_package="" if build_go else repo,
                    binary_repo=binary_repo,
                )
            )
    return services


def write_github_output(services: list[ServiceConfig]) -> None:
    """Serialise the matrix and write it to ``$GITHUB_OUTPUT``."""
    matrix_json = json.dumps({"include": [asdict(s) for s in services]})
    has_services = "true" if services else "false"

    print(f"Generated matrix: {matrix_json}")

    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as out:
        out.write(f"matrix={matrix_json}\n")
        out.write(f"has_services={has_services}\n")


if __name__ == "__main__":
    write_github_output(build_matrix())
