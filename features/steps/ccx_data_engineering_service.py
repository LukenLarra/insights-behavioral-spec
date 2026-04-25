# Copyright © 2023, José Luis Segura Lucas, Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Implementation of test steps that run CCX Upgrade Risk Inference Service."""

import os
import subprocess
import sys

import requests
from behave import given, when
from common_http import check_service_started
from src.process_output import path_from_context
from src.process_utils import terminate_process as _terminate_process


@given("The CCX Data Engineering Service is running on port {port:d} with envs")
def start_ccx_upgrades_data_eng(context, port):
    """Run ccx-upgrades-data-eng for a test and prepare its stop."""
    params = [
        sys.executable,
        "-m",
        "uvicorn",
        "ccx_upgrades_data_eng.main:app",
        "--port",
        str(port),
        "--log-config",
        "logging.yaml",
    ]
    env = os.environ.copy()

    for row in context.table:
        var, val = row["variable"], row["value"]
        env[var] = val

    stdout_path = path_from_context(context, "ccx-upgrades-data-eng", "stdout")
    stderr_path = path_from_context(context, "ccx-upgrades-data-eng", "stderr")

    stdout_file = stdout_path.open("w")
    stderr_file = stderr_path.open("w")
    context.add_cleanup(stdout_file.close)
    context.add_cleanup(stderr_file.close)

    data_eng_path = os.getenv("PATH_TO_LOCAL_DATA_ENG_SERVICE")
    if not data_eng_path:
        github_workspace = os.environ.get("GITHUB_WORKSPACE")
        candidate_paths = [
            os.path.join(os.getcwd(), "ccx-upgrades-data-eng"),
            os.path.abspath(os.path.join(os.getcwd(), "..", "ccx-upgrades-data-eng")),
        ]
        if github_workspace:
            candidate_paths.insert(0, os.path.join(github_workspace, "ccx-upgrades-data-eng"))

        for candidate in candidate_paths:
            if os.path.isdir(candidate):
                data_eng_path = candidate
                break

    popen = subprocess.Popen(
        params,
        stdout=stdout_file,
        stderr=stderr_file,
        env=env,
        cwd=data_eng_path,
    )
    assert popen is not None

    try:
        check_service_started(context, "localhost", port, attempts=15, seconds_between_attempts=1)
    except Exception:
        logs = (
            f"--- STDOUT ---\n{stdout_path.read_text()}\n--- STDERR ---\n{stderr_path.read_text()}"
        )
        msg = f"No service seem to be available at http://localhost:{port}\n{logs}"
        raise Exception(msg) from None
    context.add_cleanup(lambda: _terminate_process(popen))


@given("The mock RHOBS Service is running on port {port:d}")
def start_rhobs_mock_service(context, port):
    """Run RHOBS service mock for a test and prepare its stop."""
    mock_dir = os.path.join(
        os.environ.get("GITHUB_WORKSPACE", os.getcwd()),
        "insights-behavioral-spec",
        "mocks",
        "rhobs",
    )

    params = [
        sys.executable,
        "-m",
        "uvicorn",
        "rhobs_service:app",
        "--port",
        str(port),
        "--app-dir",
        mock_dir,
    ]

    stdout_path = path_from_context(context, "", "rhobs-mock-stdout")
    stderr_path = path_from_context(context, "", "rhobs-mock-stderr")

    stdout_file = stdout_path.open("w")
    stderr_file = stderr_path.open("w")

    context.add_cleanup(stdout_file.close)
    context.add_cleanup(stderr_file.close)

    env = os.environ.copy()

    popen = subprocess.Popen(params, stdout=stdout_file, stderr=stderr_file, env=env)
    assert popen is not None

    # time.sleep(0.5)
    check_service_started(context, "localhost", port, attempts=10, seconds_between_attempts=1)
    context.add_cleanup(lambda: _terminate_process(popen))
    context.mock_rhobs = popen
    context.mock_rhobs_port = port


@when("I stop the mock RHOBS Service")
def stop_rhobs_mock_service(context):
    """Stop mocked RHOBS service."""
    _terminate_process(context.mock_rhobs)


@when("The mock RHOBS Service doesn't find the queried clusters")
def empty_rhobs_mock_service(context):
    """Make mocked RHOBS service return 500 Not found on any query."""
    response = requests.post(
        f"http://localhost:{context.mock_rhobs_port}/clusters_not_found",
        params={"activate": True},
    )
    assert response.status_code == 204
