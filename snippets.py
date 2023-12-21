import json

from statistics import median


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
        f.write(json.dumps({"0": [0, 0, 0, 0]}))


def create_snippet_list(count) -> list[int]:
    return [0] * count


def create_seconds_zone(snippet_list: list[int]) -> tuple:
    if max(snippet_list) < 30 or min(snippet_list) == 0:
        return tuple()

    # graph = snippet_list[4:]

    median_count = median(snippet_list)
    print("median", median_count)

    zone = list()

    for i in range(len(snippet_list)):
        if snippet_list[i] >= median_count:
            zone.append(i)

    # print(zone)

    zones = [list() for _ in range(5)]

    count_zones = 0

    for i in range(len(zone)):

        if i + 1 == len(zone) or count_zones > 4:
            break

        if zone[i] + 1 == zone[i + 1]:
            zones[count_zones].append(zone[i])

        else:
            count_zones += 1

    maximum_len = 0
    index = 0

    for i in zones:
        if len(i) > maximum_len:
            maximum_len = len(i)
            index = zones.index(i)

    # print(index)

    return zones[index][0], zones[index][-1]


if __name__ == '__main__':
    start, end = create_seconds_zone(eval(input()))

    from pygame import mixer

    mixer.init()
    mixer.music.load("music/1.mp3")
    mixer.music.play(start=start)

    while True:
        pass
