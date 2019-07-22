from pattern_parser import parse_pattern

pattern = parse_pattern("(?=1.*9)\d+")
print(pattern)
fsm = pattern.to_fsm()
print(fsm)
print(fsm.accepts("123"))
print(fsm.accepts("129"))
print(fsm.accepts("1294"))
print(fsm.accepts("12d94"))
print(fsm.accepts("124294"))
