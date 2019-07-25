import time

from lark import Lark

from pattern_parser import parse_pattern, compare_patterns

start = time.time()
grammar = Lark(open("grammar.lark"), parser='lalr', start='file_input')
grammar.lexer = grammar._build_lexer()
terminals = [(term.pattern.type, term.name, term.pattern.to_regexp()) for term in grammar.lexer.terminals]
with open('terminals.pydata', 'w') as f:
    print(repr(terminals), file=f)
patterns = [(term, parse_pattern(term.pattern.to_regexp())) for term in grammar.lexer.terminals if
            term.pattern.type == 're']
print(len(patterns))
pat_term_map = {p: t for t, p in patterns}
for a, b in compare_patterns(*pat_term_map.keys()):
    print(f"Collision between {pat_term_map[a]} and {pat_term_map[b]}")
end = time.time()
print(f"Total time: {end - start}")
