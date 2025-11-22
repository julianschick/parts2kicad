import re
from datetime import datetime
from io import BytesIO, IOBase
from typing import Callable, TextIO

VERSION = "0.1"

base_data = open('base_input.kicad_sym', 'rb').read().decode('utf8')
additional_data = open('additional.kicad_sym', 'rb').read().decode('utf8')

# 0 next token expected
# 1 in quoted token
# 2 in quoted token after '\'
# 3 in unquoted token
# 4 in whitespace (and next token expected)

level = 0
entrypoints = []

def is_white(c) -> bool:
    return re.match(r'\s', c) is not None

class Node:
    def __init__(self, start_index: int, end_index: int):
        self.start_index = start_index
        self.end_index = end_index

    def is_token(self, expected_content: str) -> bool:
        return False

    def is_token_lower(self, expected_content: str) -> bool:
        return False

    def is_token_lambda(self, l: Callable[[str], bool]) -> bool:
        return False

    def __getitem__(self, item):
        raise IndexError

    def is_list(self) -> bool:
        return False

    def write(self, io: IOBase):
        pass

class Token(Node):
    def __init__(self, start_index: int, end_index: int, quoted: bool, content: str):
        super().__init__(start_index, end_index)
        self.quoted = quoted
        self.content = content

    def is_token(self, expected_content: str) -> bool:
        return self.content == expected_content

    def is_token_lower(self, expected_content: str) -> bool:
        return self.content.lower() == expected_content

    def is_token_lambda(self, l: Callable[[str], bool]) -> bool:
        return l(self.content)

    def __str__(self):
        return self.content

    def write(self, io: IOBase):
        output = f'"{self.content}"' if self.quoted else self.content
        io.write(output.encode('utf8'))


class Whitespace(Node):
    def __init__(self, start_index: int, end_index: int, content: str):
        super().__init__(start_index, end_index)
        self.content = content

    def __str__(self):
        return (
            self.content
                .replace(' ', '_')
                .replace('\t', '\\t')
                .replace('\r', '\\r')
                .replace('\n','\\n')
        )

    def write(self, io: IOBase):
        io.write(self.content.encode('utf8'))

    def only_indentation(self) -> Whitespace:
        idx = self.content.find('\n')
        if idx == -1:
            return self
        else:
            return Whitespace(-1, -1, self.content[idx+1:])


class List(Node):
    def __init__(self, start_index: int, end_index: int, subnodes: list[Node]):
        super().__init__(start_index, end_index)
        self.subnodes = subnodes
        self.subnodes_without_whitspace = [x for x in subnodes if type(x) is not Whitespace]

    def is_list(self) -> bool:
        return True

    def __getitem__(self, key):
        return self.subnodes_without_whitspace[key]

    def __str__(self):
        return "[" + ','.join([str(x) for x in self.subnodes_without_whitspace]) + "]"

    def __len__(self):
        return len(self.subnodes_without_whitspace)

    def write(self, io: IOBase):
        io.write("(".encode('utf8'))
        for s in self.subnodes:
            s.write(io)
        io.write(")".encode('utf8'))


def recurse(i, d, lvl):
    begin = i
    i += 1
    state = 0
    token, token_start_index = "", None
    ws = ""

    subnodes = []

    while True:
        c = d[i]

        if state == 0 or state == 4:
            if state == 4 and not is_white(c):
                subnodes.append(Whitespace(-1, -1, ws))
                ws = ""

            if c == '(':
                i, node = recurse(i, d, lvl + 1)
                subnodes.append(node)
                i -= 1
                state = 0
            elif c == '"':
                token_start_index = i
                state = 1
            elif c == ')':
                end = i
                return i + 1, List(begin, end, subnodes)
            elif is_white(c):
                ws += c
                state = 4
            elif not is_white(c):
                token_start_index = i
                token += c
                state = 3

        elif state == 1:
            if c == '\\':
                state = 2
            if c == '"':
                subnodes.append(Token(token_start_index, i, True, token))
                token, token_start_index = "", None
                state = 0
            else:
                token += c

        elif state == 2:
            state = 1
            if c == '"' or token == '\\':
                token += c
            else:
                token += '\\' + c

        elif state == 3:
            if c in {'(', ')'} or is_white(c):
                subnodes.append(Token(token_start_index, i - 1, False, token))
                token, token_start_index = "", None

            if c == '(':
                i, node = recurse(i, d, lvl + 1)
                subnodes.append(node)
                i -= 1
                state = 0
            elif c == ')':
                end = i
                return i + 1, List(begin, end, subnodes)
            elif is_white(c):
                ws += c
                state = 4
            else:
                token += c


        i += 1

def wrapper(chdata):
    first_bracket = chdata.find('(')
    if first_bracket != -1:
        _, node = recurse(first_bracket, chdata, 0)
        return node
    else:
        return None

base = wrapper(base_data)
add = wrapper(additional_data)

syms_in_lib: set[str] = {str(s[1]) for s in base.subnodes if s.is_list() and s[0].is_token_lower('symbol')}
syms_to_add = []

for i in range(0, len(add.subnodes)):
    s = add.subnodes[i]
    if s.is_list() and s[0].is_token_lower('symbol') and s[1] not in syms_in_lib:
        syms_to_add.append(s)
        if i+1 < len(add.subnodes) and type(add.subnodes[i+1]) is Whitespace:
            syms_to_add.append(add.subnodes[i+1])
        if i-1 > 0 and type(add.subnodes[i-1]) is Whitespace:
            syms_to_add.insert(0, add.subnodes[i-1].only_indentation())

#[s for s in add.subnodes if s.is_list() and s[0].is_token('symbol') and s[1] not in syms_in_lib]
not_to_add = [s for s in add.subnodes if s.is_list() and s[0].is_token_lower('symbol') and s[1] in syms_in_lib]


print(f"Already in lib: {', '.join(syms_in_lib)}")
print(f"To add: {', '.join(str(s[1]) for s in syms_to_add if type(s) is not Whitespace)}")
print(f"Not to add: {', '.join(str(s[1]) for s in not_to_add)}")

version = [s for s in base.subnodes if s.is_list() and s[0].is_token_lower('version')][0]
version[1].content = datetime.now().strftime('%Y%m%d')

generator = [s for s in base.subnodes if s.is_list() and s[0].is_token_lower('generator')][0]
generator[1].content = f"mouser2kicad v{VERSION}"
generator[1].quoted = True

for symb in syms_to_add:
    base.subnodes.append(symb)

base.write(open('output.kicad_sym', 'wb'))

base2 = wrapper(open('base_input.kicad_sym', 'rb').read().decode('utf8'))
print(base2)
b = BytesIO()
base2.write(b)
open('base_input_thru.kicad_sym', 'wb').write(b.getbuffer())
