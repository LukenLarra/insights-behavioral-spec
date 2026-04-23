import glob
import json
import os
import re


def extract(content, field):
    pattern = r"^\s*" + re.escape(field) + r'\s*:\s*(?:"([^"]+)"|\'([^\']+)\'|([^\s\n]+))'
    match = re.search(pattern, content, re.MULTILINE)
    if match:
        return match.group(1) or match.group(2) or match.group(3)
    return None


services = []
for file in glob.glob("bdd-configs/*-framework.yml"):
    with open(file, encoding="utf-8") as f:
        content = f.read()

    repo = extract(content, "repo")
    service = extract(content, "service")

    if repo and service:
        build_go = str(extract(content, "build_go") or "").lower() == "true"
        binary_repo = extract(content, "binary_repo") or ""

        services.append(
            {
                "repo": repo,
                "service": service,
                "config": os.path.basename(file),
                "profile": extract(content, "docker_profile") or "",
                "build_go": build_go,
                "service_package": "" if build_go else repo,
                "binary_repo": binary_repo,
            }
        )

matrix_json = json.dumps({"include": services})
has_services = "true" if services else "false"

print(f"Generated matrix: {matrix_json}")

with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as out:
    out.write(f"matrix={matrix_json}\n")
    out.write(f"has_services={has_services}\n")
