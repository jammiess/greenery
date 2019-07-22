from lark import Lark

from pattern_parser import parse_pattern

grammar = Lark(open("grammar.lark"))
regexps = [(term, parse_pattern(term.pattern.to_regexp())) for term in grammar._build_lexer().terminals]
print("parsed")
for t,p in regexps:
    print(t)
    print(p)
    print()
fsms = [(term, regex.to_fsm()) for term, regex in regexps]
for i, (term_a, fsm_a) in enumerate(fsms):
    for term_b, fsm_b in fsms[i + 1:]:
        if not fsm_a.isdisjoint(fsm_b):
            print(f"Collision in Terminal {term_a} and {term_b}")
