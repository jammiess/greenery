from lark import Lark

from pattern_parser import parse_pattern, compare_patterns

grammar = Lark(open("grammar.lark"),parser='lalr',start='file_input')
regexps = [(term, parse_pattern(term.pattern.to_regexp())) for term in grammar._build_lexer().terminals]
# print("parsed")
# for t, p in regexps:
#     print(t)
#     print(p)
#     print(p.to_fsm())
#     print()
pat_term_map = {p: t for t, p in regexps}
for a, b in compare_patterns(*pat_term_map.keys()):
    print(f"Collision between {pat_term_map[a]} and {pat_term_map[b]}")
