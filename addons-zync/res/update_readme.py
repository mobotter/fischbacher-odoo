#!/usr/bin/env python3
import os
from pathlib import Path

current = Path(".")
if current.name == "res":
    current = current.parent
os.chdir(current)

MANIFEST = eval(Path("MANIFEST").read_text())
requirements_txt = Path("requirements.txt").read_text().splitlines()[2:]

README = Path("res/README.template").read_text()
README = README.replace(
    "__ADDONS_PATHS__",
    "\n".join(
        map(
            lambda x: f"  * {x}",
            filter(lambda x: x.strip() != ".", MANIFEST["addons_paths"]),
        )
    ),
)

README = README.replace(
    "__REQUIREMENTS__",
    "\n".join(map(lambda x: f"  * {x}", filter(lambda x: x, requirements_txt))),
)

Path("README.md").write_text(README)
