import argparse
import os
import re
import sys
from typing import Optional
from zipfile import ZipFile
import sexpdata
from sexpdata import Symbol

import requests
from io import BytesIO



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

def handle_symbol(args: argparse.Namespace, data: bytes):
    if not os.path.exists(args.target):
        print(f"Target symbol library '{args.target}' does not exist and will be created.")

        d1 = sexpdata.load(open('/home/julian/kicad-import/SamacSys_Parts_.kicad_sym'))
        d2 = sexpdata.loads(data.decode('utf-8'))

        for x in d1:
            print(x)

        symbols_d2 = [x for x in d2 if x[0] == Symbol('symbol')]
        for symbol_d2 in symbols_d2:
            d1.append(symbol_d2)


        sexpdata.dump(d1, open('/home/julian/kicad-import/SamacSys_Parts_.kicad_sym', 'w'))

    print(data)
    pass

def handle_fprint(args: argparse.Namespace, data: bytes, path3d: Optional[str]):
    print(data)
    pass

def handle_3d(args: argparse.Namespace, data: bytes) -> str:


    pass

def main(args: argparse.Namespace):
    with ZipFile(args.zip) as z:
        symbols = {n.group(1): z.open(n.group(0), 'r').read() for n in [SYM_PATTERN.match(n) for n in z.namelist()] if n }
        fprints = {n.group(1): z.open(n.group(0), 'r').read() for n in [FPRINT_PATTERN.match(n) for n in z.namelist()] if n}
        models = {n.group(1): z.open(n.group(0), 'r').read() for n in [MOD3D_PATTERN.match(n) for n in z.namelist()] if n}

        if not symbols and not fprints and not models:
            print("Found no data. Exiting.", file=sys.stderr)
            exit(1)

        artifacts = { "symbols" : symbols, "footprints" : fprints, "3D models": models}
        chosen_artifacts = {}

        for msg_name, data in artifacts.items():
            if data:
                print(f"Found {msg_name}:")
                keylist = list(data.keys())

                nr = 1
                for a in keylist:
                    print(f" * ({nr}) {a}")
                    nr += 1

                if len(keylist) > 1:
                    try:
                        chosen = int(input(f"Which one should I take? Enter a number from 1 to {len(keylist)}"))
                    except ValueError:
                        print("Not a valid number. Exiting.", file=sys.stderr)
                        exit(1)

                    if chosen < 0 or chosen > len(keylist):
                        print(f"Not a number between 1 and {len(keylist)}. Exiting.", file=sys.stderr)
                        exit(1)
                else:
                    chosen = 1

                chosen_artifacts[msg_name] = artifacts[msg_name][keylist[chosen - 1]]

        if "symbols" in chosen_artifacts:
            handle_symbol(args, chosen_artifacts["symbols"])
        if "3D models" in chosen_artifacts:
            path_to_3d_model = handle_3d(args, chosen_artifacts["3D models"])
        if "footprints" in chosen_artifacts:
            handle_fprint(args, chosen_artifacts["footprints"], path_to_3d_model)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a zip file.")
    parser.add_argument('-z', '--zip', type=str, required=True, help="Path to the zip file")
    parser.add_argument('-t', '--target', type=str, required=True, help="Path to the target *.kicad_sym library")
    main(parser.parse_args())