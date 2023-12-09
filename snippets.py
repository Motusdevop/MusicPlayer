import json

from math import ceil

def get_json():
    with open("snippets.json") as f:
        return json.load(f)

def write_json(new_json):
    with open("snippets.json", 'w') as f:
        f.write(json.dumps(new_json, indent=1))

def clear():
    with open("snippets.json", 'w') as f:
        f.write(json.dumps({"0": [0,0,0,0]}))

def create_snippet_list(count):
    return [0] * count

def create_snippet(y_list):
    median = ceil(y_list)
    for i in range(len(y_list)):
        if y_list[y] > median-1 and i > min:
            max=i
        else:
            min = i
    print(min, max)

