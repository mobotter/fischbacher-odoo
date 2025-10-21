# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from pathlib import Path
import inspect
import os
from pathlib import Path

current_dir = Path(
    os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
)

IGNORED = ["__init__.py", "test_1.py"]


for file in current_dir.glob("**/tests/*.py"):
    if file.name in IGNORED:
        continue
