import re
import typing
from enum import Enum
from io import IOBase
from os import PathLike
from typing import Callable

_EOF = '\x04'

class Node:
    def __init__(self, level: int):
        self.level = level

    def is_token(self, expected_content: str) -> bool:
        return False

    def is_token_lower(self, expected_content: str) -> bool:
        return False

    def is_whitespace(self):
        return False

    def __getitem__(self, item):
        raise IndexError

    def is_list(self) -> bool:
        return False

    def write(self, io: IOBase):
        pass

    def write_string(self) -> str:
        return ""

class Token(Node):
    def __init__(self, level: int, quoted: bool, content: str):
        super().__init__(level)
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
        io.write(self.write_string().encode(_get_encoding()))

    def write_string(self) -> str:
        return f'"{self.content}"' if self.quoted else self.content


class Whitespace(Node):
    def __init__(self, level: int, content: str):
        super().__init__(level)
        self.content = content

    def __str__(self):
        return (
            self.content
                .replace(' ', '_')
                .replace('\t', '\\t')
                .replace('\r', '\\r')
                .replace('\n','\\n')
        )

    def is_whitespace(self):
        return True

    def write(self, io: IOBase):
        io.write(self.write_string().encode(_get_encoding()))

    def write_string(self) -> str:
        return self.content

    def only_indentation(self) -> 'Whitespace':
        idx = self.content.find('\n')
        if idx == -1:
            return self
        else:
            return Whitespace(self.level, self.content[idx+1:])


class List(Node):
    def __init__(self, level: int, subnodes: typing.List[Node]):
        super().__init__(level)
        self.subnodes = subnodes
        self.subnodes_without_whitespace = [x for x in subnodes if not x.is_whitespace()]

    def is_list(self) -> bool:
        return True

    def __getitem__(self, key):
        return self.subnodes_without_whitespace[key]

    def __str__(self):
        return "[" + ','.join([str(x) for x in self.subnodes_without_whitespace]) + "]"

    def __len__(self):
        return len(self.subnodes_without_whitespace)

    def write(self, io: IOBase):
        if self.level > 0:
            io.write("(".encode(_get_encoding()))

        for s in self.subnodes:
            s.write(io)

        if self.level > 0:
            io.write(")".encode(_get_encoding()))

    def write_string(self) -> str:
        if self.level > 0:
            return f"({''.join(s.write_string() for s in self.subnodes)})"
        else:
            return ''.join(s.write_string() for s in self.subnodes)


def _is_white(c: str) -> bool:
    return re.match(r'\s', c) is not None


def _get_encoding() -> str:
    return 'utf8'


class ParserState(Enum):
    NEXT_TOKEN = 0
    IN_TOKEN_QUOTED = 1
    IN_TOKEN_QUOTED_ESC = 2
    IN_TOKEN = 3
    IN_WHITESPACE = 4


def _recursive_parse(i, d, lvl) -> typing.Tuple[int, Node]:
    i += 1
    state: ParserState = ParserState.NEXT_TOKEN
    token, ws = "", ""

    subnodes = []

    while True:
        if i >= len(d) and lvl != 0:
            raise Exception("Invalid S-Expression Data.")

        c = d[i] if i < len(d) else _EOF

        if state in {ParserState.NEXT_TOKEN, ParserState.IN_WHITESPACE}:
            if state == ParserState.IN_WHITESPACE and not _is_white(c):
                subnodes.append(Whitespace(lvl, ws))
                ws = ""

            if c == _EOF:
                return i, List(lvl, subnodes)
            if c == '(':
                i, node = _recursive_parse(i, d, lvl + 1)
                subnodes.append(node)
                i -= 1
                state = ParserState.NEXT_TOKEN
            elif c == '"':
                state = ParserState.IN_TOKEN_QUOTED
            elif c == ')':
                return i + 1, List(lvl, subnodes)
            elif _is_white(c):
                ws += c
                state = ParserState.IN_WHITESPACE
            elif not _is_white(c):
                token += c
                state = ParserState.IN_TOKEN

        elif state == ParserState.IN_TOKEN_QUOTED:
            if c == _EOF:
                raise Exception("EOF came too soon.")
            elif c == '\\':
                state = ParserState.IN_TOKEN_QUOTED_ESC
            elif c == '"':
                subnodes.append(Token(lvl, True, token))
                token, token_start_index = "", None
                state = ParserState.NEXT_TOKEN
            else:
                token += c

        elif state == ParserState.IN_TOKEN_QUOTED_ESC:
            state = ParserState.IN_TOKEN_QUOTED
            if c == _EOF:
                raise Exception("EOF came too soon.")
            elif c == '"' or token == '\\':
                token += c
            else:
                token += '\\' + c

        elif state == ParserState.IN_TOKEN:
            if c in {'(', ')'} or _is_white(c) or c == _EOF:
                subnodes.append(Token(lvl, False, token))
                token, token_start_index = "", None

            if c == _EOF:
                return i, List(lvl, subnodes)
            if c == '(':
                i, node = _recursive_parse(i, d, lvl + 1)
                subnodes.append(node)
                i -= 1
                state = ParserState.NEXT_TOKEN
            elif c == ')':
                return i + 1, List(lvl, subnodes)
            elif _is_white(c):
                ws += c
                state = ParserState.IN_WHITESPACE
            else:
                token += c

        i += 1


def read_from_string(character_data: str) -> Node:
    i, root_node = _recursive_parse(-1, character_data, 0)
    if i != len(character_data):
        raise Exception("The S-Expression data could not be fully read.")
    return root_node


def read_from_file(fpath: PathLike) -> Node:
    with open(fpath, 'rb') as f:
        character_data = f.read().decode(_get_encoding())
    return read_from_string(character_data)
