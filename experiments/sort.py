
import fileinput

lines = [ line.split() for line in fileinput.input() ]

for line in sorted(lines, key = lambda x : float(x[-1]) if x[-1] != "nan" else 0.0) :
    print(" ".join(line))



