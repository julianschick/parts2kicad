import os
from argparse import Namespace
from pathlib import Path
from typing import Optional

from colorama import Fore

from mouser2kicad import sexp
from mouser2kicad.term import clash_input, PRE, ClashHandling, PRE2


def process_fprints(args: Namespace, target: Path, fprints: dict[tuple[str, str], bytes], paths_to_models: dict[str, dict[str, Path]]):
    target_fprints = target.with_suffix(".pretty")
    if not os.path.exists(target_fprints):
        os.mkdir(target_fprints)

    print("\n 👣 Footprints ...")
    if not fprints:
        print(f"{PRE}No footprints to process.")
    else:
        for (zip_hash, name), data in fprints.items():
            target_file = target_fprints / name

            path3d: Optional[Path] = None
            if zip_hash in paths_to_models:
                if len(paths_to_models[zip_hash]) == 1:
                    path3d = next(iter(paths_to_models[zip_hash].values()))
                else:
                    if name in paths_to_models[zip_hash]:
                        path3d = paths_to_models[zip_hash][name]

            if path3d:
                rel_path3d = path3d.relative_to(target_fprints, walk_up=True)

                s = sexp.read_from_string(data.decode('utf8'))
                if not s[0].is_list() or not s[0][0].is_token_lower('module'):
                    raise Exception("Not a KiCad Footprint model")

                model = [x for x in s[0] if x.is_list() and x[0].is_token_lower('model')]
                for m in model:
                    m[1].content = str(rel_path3d)
                    m[1].quoted = True
                data = s.write_string().encode('utf8')


            clash_handling = None
            if os.path.exists(target_file):
                clash_handling = clash_input(args, f"{PRE}{Fore.MAGENTA}{name} already exists, what to do?{Fore.RESET}")
                if clash_handling == ClashHandling.CANCEL:
                    exit(1)
            else:
                print(f"{PRE}{Fore.MAGENTA}{name}{Fore.RESET}")

            if not os.path.exists(target_file) or clash_handling == ClashHandling.OVERWRITE:
                open(target_file, 'w+b').write(data)

                if clash_handling:
                    print(f"{PRE2}[ Overwritten ]")
                else:
                    print(f"{PRE2}[ Written ]")
