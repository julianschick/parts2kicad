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


def clash_input(question: str) -> ClashHandling:
    user_input = input(
        f"{question}? (s)kip (default) / (o)verwrite / (c)ancel > "
    )

    if user_input == "o" or user_input == "overwrite":
        return ClashHandling.OVERWRITE
    elif user_input == "c" or user_input == "cancel":
        print(f"{PRE2}[ Cancelled ]")
        return ClashHandling.CANCEL
    else:
        print(f"{PRE2}[ Skipped ]")
        return ClashHandling.SKIP

