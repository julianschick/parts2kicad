import os
from argparse import Namespace
from pathlib import Path
from typing import Final, Optional

from colorama import Fore

from parts2kicad import sexp, VERSION
from parts2kicad.term import PRE, PRE2, clash_input, ClashHandling
from parts2kicad.util import err
from parts2kicad.sexp import Node, Whitespace

INITIAL_SEXP: Final[str] = f'(kicad_symbol_lib (version 20200101) (generator "parts2kicad v{VERSION}")\r\n)'


def is_symbol(node: Node, sname: Optional[str] = None) -> bool:
    # noinspection PyTypeChecker
    return node.is_list() \
        and len(node) > 1 \
        and node[0].is_token_lower('symbol') \
        and (sname is None or str(node[1]) == sname)


def process_symbols(args: Namespace, target: Path, symbols: dict[tuple[str, str], bytes]):
    print("\n 🪧 Symbols ...")
    if not symbols:
        print(f"{PRE}No symbols to process.")
    else:
        if not os.path.exists(target):
            print(f"{PRE}Target symbol library '{target}' does not exist and will be created.")
            lib = sexp.read_from_string(INITIAL_SEXP)
        else:
            lib = sexp.read_from_file(target)

        if not lib[0].is_list() or not lib[0][0].is_token_lower('kicad_symbol_lib'):
            err(f"{PRE}Target does not seem to be a well-formed KiCad symbol library.")
            exit(1)

        syms_in_lib: set[str] = {str(s[1]) for s in lib[0].subnodes if is_symbol(s)}

        for (sym_ziphash, sym_fname), sym_data in symbols.items():
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

                clash_handling = None

                if symbol_name in syms_in_lib:
                    clash_handling = clash_input(args, f"{PRE}{Fore.MAGENTA}{symbol_name} already in lib, what to do?{Fore.RESET}")
                    if clash_handling == ClashHandling.CANCEL:
                        exit(1)
                else:
                    print(f"{PRE}{Fore.MAGENTA}{symbol_name}{Fore.RESET}")

                if clash_handling == ClashHandling.OVERWRITE:
                    index = next((i for i, x in enumerate(lib[0].subnodes) if is_symbol(x, sname=symbol_name)))
                    lib[0].subnodes[index] = sym
                    print(f"{PRE2}[ Overwritten ]")

                if not clash_handling:
                    if ws_before:
                        lib[0].subnodes.append(ws_before)
                    lib[0].subnodes.append(sym)
                    if ws_after:
                        lib[0].subnodes.append(ws_after)

                    print(f"{PRE2}[ Inserted ]")

        lib.write(open(target, 'wb'))
