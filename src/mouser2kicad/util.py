import sys

from colorama import Fore


def err(msg: str, recoverable=True):
    print(f'{Fore.RED}{msg}{Fore.RESET}', file=sys.stderr)
    if not recoverable:
        exit(1)