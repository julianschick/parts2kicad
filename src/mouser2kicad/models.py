import os.path
import shutil
from pathlib import Path

from mouser2kicad.term import PRE, clash_input, ClashHandling, PRE2


def process_3dmodels(target: Path, symbols: dict[tuple[str, str], bytes]):
    target_models = target.with_suffix(".3dshapes")
    print(target_models)
    print(symbols.keys())

    print("\n 📦 3D Models ...")

    for (zip_hash, name), data in symbols.items():
        target_file = target_models / name

        clash_handling = None
        if os.path.exists(target_file):
            clash_handling = clash_input(f"{PRE}{name} already exists, what to do?")
            if clash_handling == ClashHandling.CANCEL:
                exit(1)

        if not os.path.exists(target_file) or clash_handling == ClashHandling.OVERWRITE:
            open(target_file, 'wb').write(data)

            if clash_handling:
                print(f"{PRE2} [ Overwritten ]")
            else:
                print(f"{PRE2} [ Written ]")





