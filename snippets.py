import json

from statistics import median

# Получаем настройки
from config import MIN_COUNT_OF_PLAYS_TO_CREATE_SNIPPET, MIN_MEDIAN_OF_PLAYS_TO_CREATE_SNIPPET


def create_json() -> None:  # Создаём json файл для хранения сниппетов
    with open("snippets.json", "w") as f:
        f.write("")


def get_json() -> dict:  # Получаем словарь
    try:
        with open("snippets.json") as f:
            return json.load(f)
    except json.decoder.JSONDecodeError:
        return dict()
    except FileNotFoundError:
        create_json()


def write_json(new_json) -> None:  # Обновляем json
    with open("snippets.json", 'w') as f:
        f.write(json.dumps(new_json, indent=1))


def clear() -> None:  # очищаем файл
    with open("snippets.json", 'w') as f:
        f.write(json.dumps({"0": [0, 0, 0, 0]}))  # Затычка для нормальной работы


def create_snippet_list(count) -> list[int]:  # Создаём пустой сниппет лист
    return [0] * count


def create_seconds_zone(snippet_list: list[int]) -> tuple:  # Получаем зону сниппета
    if max(snippet_list) < MIN_COUNT_OF_PLAYS_TO_CREATE_SNIPPET or median(
            snippet_list) < MIN_MEDIAN_OF_PLAYS_TO_CREATE_SNIPPET:  # Условия создания сниппета
        return tuple()

    median_count = median(snippet_list)
    # print("median", median_count)

    zone = list()

    for i in range(len(snippet_list)):  # Ищем где кол-во прослушиваний больше медианного
        if snippet_list[i] > median_count:
            zone.append(i)

    # print(zone)

    zones = [list() for _ in range(5)]  # Создаём список зон с ограничение до 5 возможных

    count_zones = 0

    for i in range(len(zone)):

        if i + 1 == len(zone) or count_zones > 4:  # Если прошли весь список или кол-во зон слишком большое ломаем цикл
            break

        if zone[i] + 1 == zone[i + 1]:  # Если зона не прырывается то добавляем
            zones[count_zones].append(zone[i])

        else:
            count_zones += 1

    maximum_len = 0
    index = 0

    for i in zones:  # Ищем самую большую зону. Это и есть наш сниппет
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
