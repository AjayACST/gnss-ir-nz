import os
import shutil
from pathlib import Path

file_name = "fiel1350.25.A"
files_path = Path("../data/new").rglob("*.LOG")

#sort by name
files_path = sorted(files_path, key=lambda x: x.name)

with open("../data/new/" + file_name, "wb") as f:
    for file in files_path:
        with open(file, "rb") as f2:
            shutil.copyfileobj(f2, f)
        f2.close()
f.close()