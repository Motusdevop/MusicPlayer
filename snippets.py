import json

from math import ceil


def create_json() -> None:
    with open("snippets.json", "w") as f:
        f.write("")
def get_json() -> dict:
    try:
        with open("snippets.json") as f:
            return json.load(f)
    except json.decoder.JSONDecodeError:
        return dict()


def write_json(new_json) -> None:
    with open("snippets.json", 'w') as f:
        f.write(json.dumps(new_json, indent=1))


def clear() -> None:
    with open("snippets.json", 'w') as f:
        f.write(json.dumps({"0": [0,0,0,0]}))


def create_snippet_list(count) -> list[int]:
    return [0] * count


def create_snippet(y_list) -> None:
    median = ceil(y_list)
    
    for i in range(len(y_list)):
        if y_list[y] > median-1 and i > min:
            max=i
        else:
            min = i
    print(min, max)
