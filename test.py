from pattern_parser import parse_pattern

pattern = parse_pattern("(?s).(?-s:.)")
print(pattern)
print(pattern.lengths)
print(pattern.prefix_postfix)
fsm = pattern.to_fsm()
print(fsm)
print(fsm.accepts("\n\n"))
print(fsm.accepts(" \n"))
print(fsm.accepts("\n "))
print(fsm.accepts("  "))
print(fsm.accepts("abc "))
print(fsm.accepts("129"))
print(fsm.accepts("1294"))
print(fsm.accepts("12d94"))
print(fsm.accepts("124294"))
