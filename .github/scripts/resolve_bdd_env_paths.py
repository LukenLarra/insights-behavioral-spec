#!/usr/bin/env python3
"""Resolve relative paths in a BDD config's env block to absolute paths and
write them to $GITHUB_ENV so subsequent workflow steps can use them."""

import os
import sys

import yaml


def resolve(workspace: str, spec_dir: str, value: str) -> str | None:
    if value.startswith("insights-behavioral-spec/"):
        return os.path.join(workspace, value)
    if value.startswith("./"):
        return os.path.join(spec_dir, value[2:])
    return None


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: resolve_bdd_env_paths.py <config_path>", file=sys.stderr)
        sys.exit(1)

    config_path = sys.argv[1]
    workspace = os.environ["GITHUB_WORKSPACE"]
    spec_dir = os.path.join(workspace, "insights-behavioral-spec")

    with open(config_path) as f:
        config = yaml.safe_load(f)

    entries = (config.get("tests") or {}).get("env") or {}

    with open(os.environ["GITHUB_ENV"], "a") as gh_env:
        for key, raw_value in entries.items():
            resolved = resolve(workspace, spec_dir, str(raw_value))
            if resolved is None:
                continue
            if not os.path.exists(resolved):
                print(f"WARNING: resolved path does not exist: {key}={resolved}")
            else:
                print(f"Resolved {key}={resolved}")
            gh_env.write(f"{key}={resolved}\n")


if __name__ == "__main__":
    main()
