from ast import literal_eval

from pattern_parser import parse_pattern, compare_patterns

with open('terminals.pydata') as f:
    data = literal_eval(f.read())

regexes = [(n, v) for t, n, v in data if t == 're']

patterns = {parse_pattern(v): n for n, v in regexes}

for a, b in compare_patterns(*patterns.keys()):
    print(f"Collision between {patterns[a]} and {patterns[b]}")
