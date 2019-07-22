import sys
from greenery.lego import lego, parse
from greenery.fsm import fsm

regexes = list(sys.argv[1:])

if len(regexes) == 0:
    from ast import literal_eval
    while True:
        reg = input("regex|")
        if not reg:
            break
        if reg[0] in '\'"' or reg[:2] in ('r"',"r'"):
            reg = literal_eval(reg)
        regexes.append(reg)

if len(regexes) < 2:
    print("Please supply several regexes to compute their intersection, union and concatenation.")
    print("E.g. \"19.*\" \"\\d{4}-\\d{2}-\\d{2}\"")

else:
    regexes = [parse(regex) for regex in regexes]
    fsms = [regex.to_fsm() for regex in regexes]
    print(f"Have Intersection: {not fsm.intersection(*fsms).empty()}")
    print("Intersection:  %s" % (lego.intersection(*regexes).reduce()))
    print("Union:         %s" % (lego.union(*regexes).reduce()))
    print("Concatenation: %s" % (lego.concatenate(*regexes).reduce()))
