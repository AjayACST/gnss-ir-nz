import os
import shutil
from pathlib import Path

file_name = "25maytest.log"
files_path = Path("../data/new").rglob("250525*.LOG")

#sort by name
files_path = sorted(files_path, key=lambda x: x.name)

with open("../data/" + file_name, "wb") as f:
    for file in files_path:
        with open(file, "rb") as f2:
            shutil.copyfileobj(f2, f)
        f2.close()
f.close()