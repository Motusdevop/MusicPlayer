from typing import Any, Optional

from urllib.error import URLError

import requests

import config

URL = config.URL  # Получаем URL


def check_connection() -> bool:
    try:
        requests.get(URL)
        return True

    except:
        return False


def get_data(track_id: int) -> Optional[dict]:  # Получаем json с датой о треке
    try:
        r = requests.get(f"{URL}/json?track_id={track_id}")
        # print(type(r.json())) Преобразуется в словарь
        return r.json()

    except URLError:
        return None


def load_mp3_to_directory(track_id: int, path: str) -> int:  # Получаем .mp3
    r = requests.get(f"{URL}/track?track_id={track_id}")

    with open(f"{path}/{track_id}.mp3", "wb") as f:
        f.write(r.content)

    return r.status_code


def get_track(track_id: int, path: str):  # Получаем трек и дату к нему
    load_mp3_to_directory(track_id, path)
    return get_data(track_id)


def search(search_text) -> Optional[Any]:  # Делаем поиск по дб сервера
    try:
        r = requests.get(f"{URL}/search?search_text={search_text}")
        list1 = eval(r.text)
        if len(list1) == 0:
            return None
        else:
            return list1

    except SyntaxError:
        return None


def get_snippet(id: int) -> list[int]:  # Получаем сниппет с сервера
    try:
        r = requests.get(f"{URL}/get_post_snippet?track_id={id}")
        return eval(r.text)

    except:
        print("Error")


def post_snippet(id: int, snippet: list[int]):  # Отправляем сниппет из плеера
    requests.post(f"{URL}/get_post_snippet?track_id={id}", json={f"{id}": snippet})


if __name__ == "__main__":
    pass
