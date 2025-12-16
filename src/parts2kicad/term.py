from argparse import Namespace
from enum import Enum
from typing import Final

MAIN_L1_MID: Final[str] = " ├──"
MAIN_L1_END: Final[str] = " └──"
MAIN_L2_MID: Final[str] = " │  "
MAIN_L2_END: Final[str] = "    "

PRE: Final[str] =  "    * "
PRE2: Final[str] = "        └── "

class ClashHandling(Enum):
    SKIP = 0
    OVERWRITE = 1
    CANCEL = 2


def clash_input(args: Namespace, question: str) -> ClashHandling:
    if args.overwrite_all:
        print(f"{question} (s)kip (default) / (o)verwrite / (c)ancel > overwrite")
        return ClashHandling.OVERWRITE
    if args.skip_all:
        print(f"{question} (s)kip (default) / (o)verwrite / (c)ancel > skip")
        print(f"{PRE2}[ Skipped ]")
        return ClashHandling.SKIP

    user_input = input(
        f"{question} (s)kip (default) / (o)verwrite / (c)ancel > "
    )

    if user_input == "o" or user_input == "overwrite":
        return ClashHandling.OVERWRITE
    elif user_input == "c" or user_input == "cancel":
        print(f"{PRE2}[ Cancelled ]")
        return ClashHandling.CANCEL
    else:
        print(f"{PRE2}[ Skipped ]")
        return ClashHandling.SKIP

