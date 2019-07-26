from time import time

from pattern_parser import parse_pattern
from greenery import fsm

p1 = parse_pattern("(?i)A(\w(?-i:C)|\W\$)")
p2 = parse_pattern("(?i)Ab(?-i:C)")
p3 = parse_pattern("(?i)Ab(?-i:C)")

f1, f2, f3 = p1.to_fsm(), p1.to_fsm(), p1.to_fsm()
print(f1.categories())

