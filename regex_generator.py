from random import choice, randrange

import re


def _entry() -> str:
    return re.escape(chr(randrange(ord(' '), ord('~') + 1)))


def _char_group() -> str:
    entries = randrange(1, 5)
    negate = '^' if choice((True, False)) else ''
    return f"[{negate}{''.join(_entry() for _ in range(entries))}]"


def _atom(max_depth: int = 2) -> str:
    a = choice(('char',
                'char_group',
                'sub_group',
                'lookahead'
                ) if max_depth > 0 else
               ('char',
                'char_group'
                ))
    if a == 'char':
        c = chr(randrange(ord(' '), ord('~') + 1))
        return _mult(re.escape(c))
    elif a == 'char_group':
        return _mult(_char_group())
    elif a == 'sub_group':
        p = create_random(max_depth - 1)
        if choice((False, True)):
            return _mult(f"(?:{p})")
        else:
            return _mult(f"({p})")
    elif a == 'lookahead':
        p = create_random(max_depth - 1)
        if choice((False, True)):
            return f"(?={p})"
        else:
            return f"(?!{p})"
    else:
        raise ValueError(a)


def _mult(base: str) -> str:
    a = choice(('star', 'plus', 'mult', 'none'))
    greed = '' if choice((False, True)) else '?'
    if a == 'none':
        return base
    elif a == 'star':
        return f'{base}*{greed}'
    elif a == 'plus':
        return f'{base}+{greed}'
    elif a == 'mult':
        low = randrange(0, 10)
        high = randrange(low + 1, 20)
        low = '' if low == 0 else str(low)
        high = '' if high == 20 else str(high)
        return f"{base}{{{low},{high}}}{greed}"
    else:
        raise ValueError(a)


def _conc(max_depth: int) -> str:
    parts = randrange(0, 5)
    return ''.join(_atom(max_depth) for _ in range(parts))


def _pattern(max_depth: int) -> str:
    ops = randrange(1, 3)
    return '|'.join(_conc(max_depth) for _ in range(ops))


def create_random(max_depth: int = 1) -> str:
    return _pattern(max_depth)


if __name__ == '__main__':
    print(create_random())
    print(create_random())
    print(create_random())
