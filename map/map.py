import json

file = open("seats.json", "r")
seats = json.load(file)

map = ""
pre_line_size = 0
diff = 0

for line in seats['lines']:
    line_size = len(line['seats'])
    if pre_line_size > line_size:
        diff += (pre_line_size - line_size)//2
    elif (pre_line_size < line_size) and (diff > 0):
        diff = (line_size - pre_line_size)//2
    for i in range(diff):
        map += ' '
    pre_line_size = line_size
    for seat in line['seats']:
        if seat['status'] == 'Available':
            map += 'o'
        else:
            map += '-'
    map += '\n'

print(map)