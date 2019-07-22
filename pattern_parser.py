from abc import abstractmethod, ABC
from dataclasses import dataclass
from textwrap import indent
from typing import Iterable, FrozenSet, Optional, Tuple, List, Union

from greenery.fsm import fsm, anything_else, epsilon, null
from simple_parser import SimpleParser, nomatch


@dataclass(frozen=True)
class _BasePattern(ABC):
    __slots__ = '_alphabet_cache', '_prefix_cache'

    @abstractmethod
    def to_fsm(self, alphabet=None) -> fsm:
        raise NotImplementedError

    @abstractmethod
    def _get_alphabet(self) -> Iterable:
        raise NotImplementedError

    @property
    def alphabet(self) -> FrozenSet:
        if not hasattr(self, '_alphabet_cache'):
            super(_BasePattern, self).__setattr__('_alphabet_cache', frozenset(self._get_alphabet()))
        return self._alphabet_cache

    @abstractmethod
    def _get_prefix(self) -> int:
        raise NotImplementedError

    @property
    def prefix(self) -> int:
        if not hasattr(self, '_prefix_cache'):
            super(_BasePattern, self).__setattr__('_prefix_cache', frozenset(self._get_prefix()))
        return self._prefix_cache


class _Repeatable(_BasePattern, ABC):
    pass


@dataclass(frozen=True)
class _CharGroup(_Repeatable):
    chars: FrozenSet[str]
    negated: bool
    __slots__ = 'chars', 'negated'

    def _get_alphabet(self, alphabet=None) -> Iterable:
        yield from self.chars
        yield anything_else

    def _get_prefix(self) -> int:
        return 0

    def to_fsm(self, alphabet=None) -> fsm:
        if alphabet is None:
            alphabet = self.alphabet

        # 0 is initial, 1 is final

        # If negated, make a singular FSM accepting any other characters
        if self.negated:
            mapping = {
                0: dict([(symbol, 1) for symbol in alphabet - self.chars]),
            }

        # If normal, make a singular FSM accepting only these characters
        else:
            mapping = {
                0: dict([(symbol, 1) for symbol in self.chars]),
            }

        return fsm(
            alphabet=alphabet,
            states={0, 1},
            initial=0,
            finals={1},
            map=mapping,
        )


@dataclass(frozen=True)
class _CompositeCharGroup(_Repeatable):
    groups: Tuple[_CharGroup, ...]
    negate: bool

    def _get_alphabet(self) -> Iterable:
        for g in self.groups:
            yield from g.alphabet
        yield anything_else

    def _get_prefix(self) -> int:
        return 0

    def to_fsm(self, alphabet=None) -> fsm:
        if alphabet is None:
            alphabet = self.alphabet
        base = fsm.union(*(g.to_fsm(alphabet) for g in self.groups))
        if self.negate:
            return _ALL.to_fsm(alphabet).different(base)
        else:
            return base


_EMPTY = _CharGroup(frozenset(""), False)
_ALL = _CharGroup(frozenset(""), True)
_CHAR_GROUPS = {
    'w': _CharGroup(frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"), False),
    'W': _CharGroup(frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"), True),
    'd': _CharGroup(frozenset("0123456789"), False),
    'D': _CharGroup(frozenset("0123456789"), True),
    's': _CharGroup(frozenset(" \t\n\r\f\v"), False),
    'S': _CharGroup(frozenset(" \t\n\r\f\v"), True),

    'a': _CharGroup(frozenset("\a"), False),
    'b': _CharGroup(frozenset("\b"), False),
    'f': _CharGroup(frozenset("\f"), False),
    'n': _CharGroup(frozenset("\n"), False),
    'r': _CharGroup(frozenset("\r"), False),
    't': _CharGroup(frozenset("\t"), False),
    'v': _CharGroup(frozenset("\v"), False),
}


@dataclass(frozen=True)
class _Repeated(_BasePattern):
    base: _Repeatable
    min: int
    max: Optional[int]

    def __str__(self):
        return f"Repeated[{self.min}:{self.max if self.max is not None else ''}]:\n" \
            f"{indent(str(self.base), '    ')}"

    def _get_alphabet(self) -> Iterable:
        return self.base.alphabet

    def _get_prefix(self) -> int:
        return self.base.prefix

    def to_fsm(self, alphabet=None) -> fsm:
        if alphabet is None:
            alphabet = self.alphabet
        unit = self.base.to_fsm(alphabet)
        mandatory = unit * self.min
        if self.max is None:
            optional = unit.star()
        else:
            optional = epsilon(alphabet) | unit
            optional *= (self.max - self.min)
        return mandatory + optional


_ALL_STAR = _Repeated(_ALL, 0, None)


@dataclass(frozen=True)
class _NonCapturing:
    inner: _BasePattern
    backwards: bool
    negate: bool
    __slots__ = 'inner', 'backwards', 'negate'

    @property
    def alphabet(self):
        return self.inner.alphabet

    def get_size(self):
        raise NotImplementedError


@dataclass(frozen=True)
class _Concatenation(_BasePattern):
    parts: Tuple[Union[_BasePattern, _NonCapturing], ...]
    __slots__ = 'parts',

    def __str__(self):
        return "Concatenation:\n" + "\n".join(indent(str(p), '  ') for p in self.parts)

    def _get_alphabet(self) -> Iterable:
        for p in self.parts:
            yield from p.alphabet
        yield anything_else

    def _get_prefix(self) -> int:
        for p in self.parts:
            raise NotImplementedError

    def to_fsm(self, alphabet=None) -> fsm:
        if alphabet is None:
            alphabet = self.alphabet
        fsm_parts = []
        empty = epsilon(alphabet)
        current = empty
        for part in self.parts:
            if isinstance(part, _NonCapturing):
                inner = part.inner.to_fsm(alphabet)
                if part.backwards:
                    raise NotImplementedError
                else:
                    fsm_parts.append((None, current))
                    fsm_parts.append((part, inner))
            else:
                current += part.to_fsm(alphabet)
        result = current
        all_star = _ALL_STAR.to_fsm(alphabet)
        for m, f in fsm_parts:
            if m is None:
                result = f + result
            else:
                assert isinstance(m, _NonCapturing) and not m.backwards
                if m.negate:
                    result = result.difference(f)
                else:
                    result = result.intersection(f + all_star)
        return result


@dataclass(frozen=True)
class Pattern(_Repeatable):
    options: Tuple[_BasePattern, ...]

    def __str__(self):
        return "Pattern:\n" + "\n".join(indent(str(o), '  ') for o in self.options)

    def _get_alphabet(self) -> Iterable:
        for o in self.options:
            yield from o.alphabet
        yield anything_else

    def _get_prefix(self) -> int:
        raise NotImplementedError

    def to_fsm(self, alphabet=None) -> fsm:
        if alphabet is None:
            alphabet = self.alphabet
        result = self.options[0].to_fsm(alphabet)
        for o in self.options[1:]:
            result |= o
        return result


class _ParsePattern(SimpleParser[Pattern]):
    SPECIAL_CHARS_STANDARD: FrozenSet[str] = frozenset({
        '+', '?', '*', '.', '$', '^', '\\', '(', ')', '[', ']', '{', '}'
    })
    SPECIAL_CHARS_INNER: FrozenSet[str] = frozenset({
        '\\', '[', ']', '-'
    })
    RESERVED_ESCAPES: FrozenSet[str] = frozenset({
        'u', 'U', 'A', 'Z', 'b', 'B'
    })

    def start(self):
        return self.pattern()

    def pattern(self):
        options = [self.conc()]
        while self.static_b('|'):
            options.append(self.conc())
        return Pattern(tuple(options))

    def conc(self):
        parts = []
        while True:
            try:
                parts.append(self.obj())
            except nomatch:
                break
        return _Concatenation(tuple(parts))

    def obj(self):
        if self.static_b("("):
            return self.group()
        return self.repetition(self.atom())

    def group(self):
        if self.static_b("?"):
            return self.extension_group()
        else:
            p = self.pattern()
            self.static(")")
            return self.repetition(p)

    def extension_group(self):
        c = self.any()
        if c in 'aiLmsux':
            raise NotImplementedError("Flags are not implmented")
        elif c == ':':
            p = self.pattern()
            self.static(")")
            return self.repetition(p)
        elif c == 'P':
            if self.static_b('<'):
                self.multiple('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_', 1, None)
                self.static('>')
                p = self.pattern()
                self.static(")")
                return self.repetition(p)
            elif self.static_b('='):
                raise NotImplementedError("Group references are not implemented")
        elif c == '#':
            while not self.static_b(')'):
                self.any()
        elif c == '=':
            p = self.pattern()
            self.static(")")
            return _NonCapturing(p, False, False)
        elif c == '!':
            p = self.pattern()
            self.static(")")
            return _NonCapturing(p, False, True)
        elif c == '<':
            c = self.any()
            if c == '=':
                p = self.pattern()
                self.static(")")
                return _NonCapturing(p, True, False)
            elif c == '!':
                p = self.pattern()
                self.static(")")
                return _NonCapturing(p, True, True)
        elif c == '(':
            raise NotImplementedError("Conditional matching is not implmented")
        else:
            raise ValueError(f"Unknown group-extension: {c!r} (Context: {self.data[self.index - 3:self.index + 5]!r}")

    def atom(self):
        if self.static_b("["):
            return self.repetition(self.chargroup())
        elif self.static_b("\\"):
            return self.repetition(self.escaped())
        elif self.static_b("."):
            return self.repetition(_ALL)
        else:
            c = self.any_but(*self.SPECIAL_CHARS_STANDARD)
            return self.repetition(_CharGroup(frozenset({c}), False))

    def repetition(self, base: _Repeatable):
        if self.static_b("*"):
            if self.static_b("?"):
                pass
            return _Repeated(base, 0, None)
        elif self.static_b("+"):
            if self.static_b("?"):
                pass
            return _Repeated(base, 1, None)
        elif self.static_b("?"):
            if self.static_b("?"):
                pass
            return _Repeated(base, 0, 1)
        elif self.static_b("{"):
            try:
                n = self.number()
            except nomatch:
                n = 0
            if self.static_b(','):
                try:
                    m = self.number()
                except nomatch:
                    m = None
            else:
                m = n
            self.static("}")
            if self.static_b('?'):
                pass
            return _Repeated(base, n, m)
        else:
            return base

    def number(self) -> int:
        return int(self.multiple("0123456789", 1, None))

    def escaped(self, inner=False):
        if self.static_b("x"):
            n = self.multiple("0123456789", 2, 2)
            c = chr(int(n, 16))
            return _CharGroup(frozenset({c}), False)
        if self.static_b("0"):
            n = self.multiple("01234567", 1, 2)
            c = chr(int(n, 8))
            return _CharGroup(frozenset({c}), False)
        if not inner:
            try:
                n = self.multiple("01234567", 3, 3)
            except nomatch:
                pass
            else:
                c = chr(int(n, 8))
                return _CharGroup(frozenset({c}), False)
            try:
                n = self.multiple("0123456789", 1, 2)
            except nomatch:
                pass
            else:
                raise NotImplementedError("Group references are not implemented")
        else:
            try:
                n = self.multiple("01234567", 1, 3)
            except nomatch:
                pass
            else:
                c = chr(int(n, 8))
                return _CharGroup(frozenset({c}), False)
        if not inner:
            try:
                c = self.anyof(*self.RESERVED_ESCAPES)
            except nomatch:
                pass
            else:
                raise NotImplementedError(f"Escape \\{c} is not implemented")
        try:
            c = self.anyof(*_CHAR_GROUPS)
        except nomatch:
            pass
        else:
            return _CHAR_GROUPS[c]
        c = self.any_but("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
        if c.isalpha():
            raise nomatch
        return _CharGroup(frozenset(c), False)

    def chargroup(self):
        if self.static_b("^"):
            negate = True
        else:
            negate = False
        groups = []
        while True:
            try:
                groups.append(self.chargroup_inner())
            except nomatch:
                break
        self.static("]")
        if len(groups) > 1:
            return _CompositeCharGroup(tuple(groups), negate)
        else:
            return tuple(groups)[0]

    def chargroup_inner(self) -> _CharGroup:
        start = self.index
        if self.static_b('\\'):
            base = self.escaped(True)
        else:
            base = _CharGroup(frozenset(self.any_but(*self.SPECIAL_CHARS_INNER)), False)
        if self.static_b('-'):
            if self.static_b('\\'):
                end = self.escaped(True)
            else:
                end = _CharGroup(frozenset(self.any_but(*self.SPECIAL_CHARS_INNER)), False)
            if len(base.chars) != len(end.chars) != 1:
                raise ValueError(f"Invalid Character-range: {self.data[start:self.index]}")
            low, high = ord(*base.chars), ord(*end.chars)
            if low > high:
                raise ValueError(f"Invalid Character-range: {self.data[start:self.index]}")
            return _CharGroup(frozenset((chr(i) for i in range(low, high + 1))), False)
        return base


def parse_pattern(pattern: str) -> Pattern:
    p = _ParsePattern(pattern)
    return p.parse()
