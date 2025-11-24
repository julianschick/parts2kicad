import os
from pathlib import Path
from typing import Final, Optional

from mouser2kicad import sexp, VERSION
from mouser2kicad.util import err
from mouser2kicad.sexp import Node, Whitespace

PRE: Final[str] =  "  * "
PRE2: Final[str] = "      └── "

def is_symbol(node: Node, sname: Optional[str] = None) -> bool:
    return node.is_list() and len(node) > 1 and node[0].is_token_lower('symbol') and (sname is None or str(node[1]) == sname)


def process_symbols(target: Path, symbols: dict[str, bytes]):
    print("\nSymbols...")
    if not symbols:
        print(f"{PRE}No symbols to process.")
    else:
        if not os.path.exists(target):
            print(f"{PRE}Target symbol library '{target}' does not exist and will be created.")
            lib = sexp.read_from_string(f'(kicad_symbol_lib (version 20200101) (generator "mouser2kicad v{VERSION}")\r\n)')
        else:
            lib = sexp.read_from_file(target)

        if not lib[0].is_list() or not lib[0][0].is_token_lower('kicad_symbol_lib'):
            err(f"{PRE}Target does not seem to be a well-formed KiCad symbol library.")
            exit(1)

        syms_in_lib: set[str] = {str(s[1]) for s in lib[0].subnodes if is_symbol(s)}

        for (sym_fname, sym_data) in symbols.items():
            d = sexp.read_from_string(sym_data.decode('utf8'))
            if not d[0].is_list() or not d[0][0].is_token_lower('kicad_symbol_lib'):
                raise Exception("Input is not a KiCad Symbol Library.")

            syms_to_add: list[tuple[Optional[Whitespace], Node, Optional[Whitespace]]] = []

            for i in range(0, len(d[0].subnodes)):
                s = d[0].subnodes[i]
                if s.is_list() and s[0].is_token_lower('symbol'):
                    if i - 1 > 0 and d[0].subnodes[i - 1].is_whitespace():
                        ws_before = d[0].subnodes[i - 1].only_indentation()
                    else:
                        ws_before = None
                    if i + 1 < len(d[0].subnodes) and d[0].subnodes[i + 1].is_whitespace():
                        ws_after = d[0].subnodes[i + 1]
                    else:
                        ws_after = None

                    syms_to_add.append((ws_before, s, ws_after))


            for ws_before, sym, ws_after in syms_to_add:
                symbol_name = str(sym[1])

                clash = symbol_name in syms_in_lib
                overwrite = False

                if clash:
                    user_input = input(f"{PRE}{symbol_name} already in lib, what to do? skip (default) / overwrite / cancel ")

                    if user_input == "o" or user_input == "overwrite":
                        overwrite = True
                    elif user_input == "c" or user_input == "cancel":
                        print(f"{PRE2}[ Cancelled ]")
                        exit(0)
                    if not overwrite:
                        print(f"{PRE2}[ Skipped ]")

                if clash and overwrite:
                    lib[0].subnodes[:] = [x for x in lib[0].subnodes if not is_symbol(x, sname=symbol_name)]

                if not clash or clash and overwrite:
                    if ws_before and not clash:
                        lib[0].subnodes.append(ws_before)
                    lib[0].subnodes.append(sym)
                    if ws_after and not clash:
                        lib[0].subnodes.append(ws_after)

                    print(f"{PRE2} [ {"Overwritten" if clash else "Inserted"} ]")


        lib.write(open(target, 'wb'))