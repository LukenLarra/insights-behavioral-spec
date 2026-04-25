# Copyright © 2024, Red Hat, Inc.
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

"""Common subprocess utilities shared across BDD step files."""

import os
import shutil
import subprocess


def terminate_process(process: subprocess.Popen) -> None:
    """Terminate a subprocess and wait until it is fully stopped."""
    if process.poll() is not None:
        return

    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def resolve_binary(binary: str) -> str:
    """Return the real path of the binary, following symlinks.

    Handles absolute paths, relative paths that exist from CWD,
    and names/relative paths that must be looked up on PATH.
    """
    if os.path.isabs(binary) or os.path.exists(binary):
        return os.path.realpath(binary)
    found = shutil.which(os.path.basename(binary))
    return os.path.realpath(found if found else binary)
