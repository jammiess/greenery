from pattern_parser import parse_pattern

pattern = parse_pattern("[A-Za-z_][A-Za-z_0-9]*(?=\W)")
print(pattern)
print(pattern.lengths)
print(pattern.prefix_postfix)
fsm = pattern.to_fsm()
print(fsm)
print(fsm.accepts("abc "))
print(fsm.accepts("129"))
print(fsm.accepts("1294"))
print(fsm.accepts("12d94"))
print(fsm.accepts("124294"))
