import os.path
import shutil
from argparse import Namespace
from pathlib import Path
from typing import Dict, Tuple

from colorama import Fore

from parts2kicad.term import PRE, clash_input, ClashHandling, PRE2


def process_3dmodels(args: Namespace, target: Path, models: Dict[Tuple[str, str], bytes]) -> Dict[str, Dict[str, Path]]:
    target_models = target.with_suffix(".3dshapes")
    if not os.path.exists(target_models):
        os.mkdir(target_models)

    result = {}

    print("\n 📦 3D Models ...")
    if not models:
        print(f"{PRE}No models to process.")
    else:
        for (zip_hash, name), data in models.items():
            target_file = target_models / name

            clash_handling = None
            if os.path.exists(target_file):
                clash_handling = clash_input(args, f"{PRE}{Fore.MAGENTA}{name} already exists, what to do?{Fore.RESET}")
                if clash_handling == ClashHandling.CANCEL:
                    exit(1)
            else:
                print(f"{PRE}{Fore.MAGENTA}{name}{Fore.RESET}")

            if not os.path.exists(target_file) or clash_handling == ClashHandling.OVERWRITE:
                open(target_file, 'w+b').write(data)
                if zip_hash not in result:
                    result[zip_hash] = {}
                result[zip_hash][name] = target_file

                if clash_handling:
                    print(f"{PRE2}[ Overwritten ]")
                else:
                    print(f"{PRE2}[ Written ]")

    return result





