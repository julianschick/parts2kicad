import argparse
import os
import pathlib
import re
from pathlib import Path
from typing import Optional
from zipfile import ZipFile

from colorama import Fore, Style

from mouser2kicad import sexp
from mouser2kicad.fprints import process_fprints
from mouser2kicad.models import process_3dmodels
from mouser2kicad.symbols import process_symbols
from mouser2kicad.util import err

#320776

# r = requests.get(
#     "https://ms.componentsearchengine.com/ga/model.php?fmt3d=stp&partID=423264",
#     auth=(user, pass)
# )
#
# if r.status_code == 200:
#     data = BytesIO(r.content).read()
#     with open('test.zip', 'wb') as f:
#         f.write(data)

SYM_PATTERN = re.compile(r'[^/]+/[Kk]i[Cc]ad/([^/]+\.kicad_sym)')
FPRINT_PATTERN = re.compile(r'[^/]+/[Kk]i[Cc]ad/([^/]+\.kicad_mod)')
MOD3D_PATTERN = re.compile(r'[^/]+/3[Dd]/([^/]+\.stp)')

def handle_fprint(args: argparse.Namespace, name: str, data: bytes, path3d: Optional[Path]):
    target = Path(args.target).with_suffix(".pretty")

    if not os.path.exists(target):
        os.mkdir(target)
    if os.path.exists(target) and not os.path.isdir(target):
        raise Exception(f"'{target}' is expected to be a directory.")

    if path3d:
        rel_path3d = path3d.relative_to(target, walk_up=True)

        s = sexp.read_from_string(data.decode('utf8'))
        if not s[0].is_list() or not s[0][0].is_token_lower('module'):
            raise Exception("Not a KiCad Footprint model")

        model = [x for x in s[0] if x.is_list() and x[0].is_token_lower('model')]
        for m in model:
            m[1].content = str(rel_path3d)
            m[1].quoted = True

        data = s.write_string().encode('utf8')


    fprint_file_path = target / name
    open(fprint_file_path, 'wb').write(data)


def handle_3d(args: argparse.Namespace, name: str, data: bytes) -> Path:
    target = Path(args.target).with_suffix(".3dshapes")

    if not os.path.exists(target):
        os.mkdir(target)
    if os.path.exists(target) and not os.path.isdir(target):
        raise Exception(f"'{target}' is expected to be a directory.")

    model_file_path = target / name
    open(model_file_path, 'wb').write(data)
    return model_file_path


def main():
    print(f"{Fore.GREEN}~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~{Fore.RESET}")
    print(f"{Fore.GREEN}~~ Welcome to m2k 'mouser2kicad' ~~{Fore.RESET}")
    print(f"{Fore.GREEN}~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~{Fore.RESET}", flush=True)

    parser = argparse.ArgumentParser(
        prog="m2k",
        description="Extract symbols, footprints and 3D models from a zip file and "
                    "integrate them into the respective KiCad libraries."
    )
    parser.add_argument(
        '-t', '--target', type=pathlib.Path, required=True,
        help="Path to the target *.kicad_sym library. If the library is foo.kicad_sym, "
             "the footprints go to the folder foo.pretty and the 3D models to the folder foo.3dshapes."
    )
    parser.add_argument('ZIP', nargs='*', type=pathlib.Path, help="Zip files to read.")
    args = parser.parse_args()

    if args.target.suffix != '.kicad_sym':
        err("The target path must have the extension '.kicad_sym'.", recoverable=False)

    if not args.ZIP:
        print("No zip archives passed, nothing to do.")
        exit(0)

    print(f"{Style.BRIGHT}Reading zip archives...{Style.NORMAL}")

    symbols: dict[str, bytes] = {}
    fprints: dict[str, bytes] = {}
    models: dict[str, bytes] = {}


    for i in range(0, len(args.ZIP)):
        zpath = args.ZIP[i]
        l1char = " ├──" if i < len(args.ZIP) - 1 else " └──"
        l2char = " │  " if i < len(args.ZIP) - 1 else "    "
        print(f"{l1char} {Fore.MAGENTA}{zpath}{Fore.RESET}")

        if not os.path.exists(zpath) or not os.path.isfile(zpath):
            print(f"{l2char}    └── {Fore.RED}Not found in filesystem.{Fore.RESET}")
        elif not os.access(zpath, os.R_OK):
            print(f"{l2char}    └── {Fore.RED}Not readable.{Fore.RESET}")
        else:
            try:
                with ZipFile(zpath) as z:
                    new_symbols = {n.group(1): z.open(n.group(0), 'r').read() for n in
                                   [SYM_PATTERN.match(n) for n in z.namelist()] if n}
                    new_fprints = {n.group(1): z.open(n.group(0), 'r').read() for n in
                                   [FPRINT_PATTERN.match(n) for n in z.namelist()] if n}
                    new_models = {n.group(1): z.open(n.group(0), 'r').read() for n in
                                  [MOD3D_PATTERN.match(n) for n in z.namelist()] if n}

                    skipped = Fore.RED + " (Ignored, already found in another zip file)" + Fore.RESET
                    if new_symbols:
                        w = min(40, max(
                            [len(k) for k in new_symbols.keys()] \
                          + [len(k) for k in new_fprints.keys()] \
                          + [len(k) for k in new_models.keys()]
                        ))
                    else:
                        w = 40

                    subelements = \
                        [f"[ 🪧 Symbol    ] {x:<{w}} {skipped if x in symbols else ""}" for x in new_symbols.keys()] + \
                        [f"[ 👣 Footprint ] {x:<{w}} {skipped if x in fprints else ""}" for x in new_fprints.keys()] + \
                        [f"[ 📦 3D Model  ] {x:<{w}} {skipped if x in models else ""}" for x in new_models.keys()]

                    for j in range(0, len(subelements)):
                        l3char = " ├──" if j < len(subelements) - 1 else " └──"
                        print(f"{l2char}   {l3char} {Fore.BLUE}{subelements[j]}{Fore.RESET}")

                    for s in new_symbols.keys():
                        if s not in symbols:
                            symbols[s] = new_symbols[s]

                    for f in new_fprints.keys():
                        if f not in fprints:
                            fprints[f] = new_fprints[f]

                    for m in new_models.keys():
                        if m not in models:
                            models[m] = new_models[m]
            except Exception as e:
                print(f"{l2char}    └── {Fore.RED}Error opening file: {e}.{Fore.RESET}")

    process_symbols(args.target, symbols)
    paths_to_models = process_3dmodels(args.target, models)
    process_fprints(args.target, fprints, paths_to_models)

    print("")
    exit(0)


if __name__ == "__main__":
    main()