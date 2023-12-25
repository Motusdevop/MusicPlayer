import time

import os

import json

from typing import Optional

from PyQt6 import uic
from PyQt6.QtWidgets import *
from PyQt6.QtCore import QTimer

from pygame import mixer

from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3

from Server import get_files
import snippets

snippets_dict = snippets.get_json()
# snippets.clear()

created_id = dict()


class Track:  # Общий класс для всех треков
    id: int
    mutagenfile: EasyID3
    title: str
    artist: str
    title_and_artist: str
    path: str
    duration: int
    snippet: bool
    snippet_list: list[int]

    def __init__(self, path: str, id: int = 0) -> None:  # Локальные файлы обозначаются id=0
        self.id = id
        self.mutagenfile = EasyID3(path)
        self.title = self.mutagenfile["title"][0]
        self.artist = self.mutagenfile["artist"][0]
        self.title_and_artist = self.title + " - " + self.artist
        self.path = path
        self.duration = int(MP3(path).info.length)
        self.snippet = False
        self.snippet_list = self.get_snippet_list()

    def get_snippet_list(self) -> list[int]:
        if self.id == 0:  # Трек локальный
            if self.title_and_artist in snippets_dict.keys():
                self.snippet = True
                return snippets_dict[self.title_and_artist]
            else:
                return snippets.create_snippet_list(self.duration)
        else:  # Трек из сервера
            snippet_list = get_files.get_snippet(self.id)
            if snippet_list == None:
                return snippets.create_snippet_list(self.duration)
            else:
                return snippet_list

    def update_snippet_list(self) -> None:
        if self.id == 0:  # Если трек из локальной директории то обновим его сниппет
            global snippets_dict
            snippets_dict[self.title_and_artist] = self.snippet_list
        else:  # Трек не локальный поэтому отправим новый сниппет лист
            get_files.post_snippet(self.id, self.snippet_list)


class PlayList:  # Класс нашей медиатеки из сервера. Хранение id в media/playlist.txt. Класс является сингтоном
    def __init__(self) -> None:
        try:
            with open("media/playlist.txt") as f:
                self.tracks_id = eval(f.read())
        except FileNotFoundError:
            with open("media/playlist.txt", "w") as f:
                f.write("[]")
                self.tracks_id = list()

    def update(self) -> None:  # Обновим медиатеку
        with open("media/playlist.txt", "w") as f:
            f.write(str(self.tracks_id))

    def add(self, id: int) -> None:  # Добавим трек в оперативную память
        self.tracks_id.append(id)
        self.update()

    def remove(self, id) -> None:  # Уберём трек из оперативной памяти
        self.tracks_id.pop(self.tracks_id.index(id))
        self.update()


class MainWindow(QMainWindow):  # Окно PyQt. Главное окно. Синглтон
    search_dict: dict
    timer: QTimer
    player: mixer.music
    playlist: PlayList
    select_mode: str
    dir_: str
    select_mode: str
    dir_: str

    def __init__(self) -> None:
        super(MainWindow, self).__init__()
        uic.loadUi('ui/mainwindow.ui', self)  # Загружаем UI

        mixer.init()  # Иницилизация pygame.mixer

        self.track = None  # Активный трек

        self.search_dict = dict()  # словарь для поиска

        self.dir_for_offline = "LocalTracks"  # Ставим стандартную папку

        self.timer = QTimer()  # Создаём таймер
        self.timer.setInterval(1000)  # Миллисекунды
        self.timer.timeout.connect(self.time)  # Как только проходит каждая секунда вызываем self.time

        self.player = mixer.music  # Создаём плеер
        self.player.set_volume(0.5)  # Громкость на 50%
        self.player.state = 0
        self.horizontalSliderVolume.setValue(50)  # слайдер громкости на 50%

        # Отключаем кнопки при запуске
        self.pushButtonPlay.setEnabled(False)
        self.horizontalSlider.setEnabled(False)
        self.add_remove.setEnabled(False)
        self.OpenFolder.setEnabled(False)
        self.snippet_btn.setEnabled(False)

        self.playlist = PlayList()  # Создаём плейлист

        self.installing_signals()  # Устанавливаем связи UI с методами главного окна
        self.show()  # показываем окно

        self.load_indicators()  # подгружаем сохранённые параметры

        if get_files.check_connection():  # проверка соеденения с сервером
            self.select_mode = "Online"
            self.dir_ = "music"
        else:
            self.select_mode = "Local"
            self.dir_ = self.dir_for_offline
            self.OnlineRad.setEnabled(False)
            self.al = Alert(Alert_text="Не удалось подключится к серверу. Режим оффлайн")

        self.get_tracks()  # Получаем треки от сервера
        self.add()  # Добавляем в QListWidget

    # Добавляем треки в список
    def add(self) -> None:
        self.listWidget.clear()  # Очищаем QListWidget

        if self.select_mode == "Online":  # Если режим онлайн получаем треки с Сервера
            global created_id  # Чтобы не создавать в будущем дупликаты создаём/проверяем словарь
            self.get_tracks()

            file_list = [i for i in os.listdir(self.dir_)]  # Просматриваем файлы

            mp3_list = []
            for i in file_list:
                if i[-4:] == ".mp3":  # Отсееваем файлы которые не являются *.mp3
                    mp3_list.append(i[:-4])

            self.track_list = []  # очищаем список треков
            for file_name in mp3_list:  # Создаём объекты класса Track и добавляем из в список трэков
                id = int(file_name)  # получаем id из заголовка mp3 файла
                Track_object = Track(self.dir_ + "/" + file_name + ".mp3", id=id)
                self.track_list.append(Track_object)
                created_id[id] = Track_object

        else:  # Тоже самое только для локальных файлов
            file_list = [i for i in os.listdir(self.dir_)]

            mp3_list = []
            for i in file_list:
                if i[-4:] == ".mp3":
                    mp3_list.append(i[:-4])

            self.track_list = []
            for file_name in mp3_list:
                self.track_list.append(Track(self.dir_ + "/" + file_name + ".mp3"))

        track_title_and_artist = [f"{track.title} - {track.artist}" for track in self.track_list]
        self.listWidget.addItems(track_title_and_artist)

        if self.listWidget.count() == 0:  # Если ничего не удалось загрузить вызываем уведомление о том что ничего не найдено
            self.NoneTracks = Alert(Alert_text="Ничего нет. Добавьте песни")

    def set_dir(self) -> None:  # Смена локальной директории
        self.dir_ = QFileDialog.getExistingDirectory(None, 'Select a folder:',
                                                     self.dir_)  # Устанавливаем активную директорию

        if self.dir_:
            self.add()
            self.dir_for_offline = self.dir_  # Устанавливаем параметр локальной директории

    def closeEvent(self, event) -> None:
        try:
            global snippets_dict

            self.track.update_snippet_list()  # Перед выходом обновляем сниппет лист
            snippets.write_json(snippets_dict)
            self.clear_preload()  # очищаем /preload/
            self.saving_indicators()  # сохраняем параметры
            event.accept()  # let the window close

        except AttributeError:  # если что-то пошло не так закрываем приложение
            event.accept()

    # Загрузка трека в плеер
    def installing_signals(self) -> None:  # Устанавливаем связи с методами
        self.listWidget.itemClicked.connect(self.load_track)
        self.pushButtonPlay.clicked.connect(self.play_music)
        self.pushButtonNextMusic.clicked.connect(self.next_track)
        self.pushButtonStEd.clicked.connect(self.back_track)
        self.horizontalSliderVolume.valueChanged.connect(self.volume_changed)
        self.horizontalSlider.valueChanged.connect(self.slider)
        self.horizontalSlider.sliderReleased.connect(self.slider_release)
        self.OpenFolder.clicked.connect(self.set_dir)
        self.add_remove.clicked.connect(self.add_del_to_playlist)
        self.pushButtonSearch.clicked.connect(self.search)
        self.SearchCombox.lineEdit().returnPressed.connect(self.search)
        self.SearchCombox.activated.connect(self.load)
        self.Rad_group = QButtonGroup()  # создаём группу кнопок
        self.Rad_group.addButton(self.LocalRad, 1)
        self.Rad_group.addButton(self.OnlineRad, 2)
        self.Rad_group.buttonClicked.connect(self.change_mode)
        self.Update_btn.clicked.connect(self.add)
        self.snippet_btn.clicked.connect(self.run_snippet)

    def load_track(self, item, id=0, start=0) -> None:  # Запускаем трек
        if self.track:  # Если до этого был активный трек то сохраним его сниппет
            self.track.update_snippet_list()
        if id == 0:  # Если трек локальный
            try:
                self.index = self.listWidget.currentRow()
                self.track = self.track_list[self.index]
                self.labelMusic.setText(self.track.title_and_artist)
                self.player.load(self.track.path)
                self.track_time = self.track.duration
                self.player.state = 1
                self.ui_load_track()  # Готовим UI к треку
                self.track_current_time = start  # Устанавливаем время
                self.timer.start()  # Запускаем таймер
                self.player.play(loops=0, start=start)
            except IndexError:
                pass

        else:  # Если трек с сервера
            get_files.load_mp3_to_directory(id, "preload/")  # Загружаем трек в /preload/
            if not id in created_id.keys():  # Если трека нету в created_id создами обёект для него
                self.track_list.append(Track(f"preload/{id}.mp3", id=id))
                self.track = self.track_list[len(self.track_list) - 1]
            else:
                self.track = created_id[id]  # Иначе получим обёект класса Track

            self.labelMusic.setText(self.track.title_and_artist)
            self.player.load(self.track.path)
            self.track_time = self.track.duration
            self.player.state = 1
            self.ui_load_track()
            self.track_current_time = start
            self.timer.start()
            self.player.play(loops=0, start=start)

        self.check_snippet_zone()  # Проверим можем ли мы использовать сниппет

    def run_snippet(self):  # Запускаем сниппет
        self.load_track(None, id=self.track.id, start=self.track.zone[0])

    def ui_load_track(self) -> None:  # Подготовка UI к треку
        self.horizontalSlider.setSliderPosition(0)
        self.labelTime.setText(f"{time.strftime('%M:%S', time.gmtime(self.track_time))}")
        self.horizontalSlider.setMaximum(int(self.track_time))
        self.pushButtonPlay.setEnabled(True)
        self.labelTimeFirst.setText("00:00")
        self.horizontalSlider.setEnabled(True)

        if self.track.id in self.playlist.tracks_id:  # Если трек в медиатеке то позволим убрать его
            self.add_remove.setEnabled(True)
            self.add_remove.setText("-")

        elif self.track.id == 0:
            self.add_remove.setDisabled(True)  # Трек локальный поэтому отключим кнопку добавления и удаления

        else:
            self.add_remove.setEnabled(True)
            self.add_remove.setText("+")

    def play_music(self) -> None:  # Работа с кнопкой Play/Pause
        if self.player.state == 0:
            self.player.state = 1
            self.player.unpause()
            self.timer.start()

        else:
            self.player.pause()
            self.timer.stop()
            self.player.state = 0

    def next_track(self) -> None:  # Логика кнопки Next
        if self.listWidget.currentRow() != self.listWidget.count() - 1:
            new_item = self.listWidget.item(self.listWidget.currentRow() + 1)

        else:
            new_item = self.listWidget.item(0)

        self.listWidget.setCurrentItem(new_item)
        self.load_track(new_item)

    def back_track(self) -> None:  # Логика кнопки Back
        if self.player.get_pos() > 3000:  # Если трек прослушали больше 3 секунд
            self.load_track(self.listWidget.item(self.listWidget.currentRow()))  # Запускаем его заново

        else:  # Если нет то включаем другой
            if self.listWidget.currentRow() != 0:
                new_item = self.listWidget.item(self.listWidget.currentRow() - 1)

            else:
                new_item = self.listWidget.item(self.listWidget.count() - 1)

            self.listWidget.setCurrentItem(new_item)
            self.load_track(new_item)

    def volume_changed(self, value) -> None:  # Если произошло изменение значение слайдера
        self.player.set_volume(value / 100)

    def time(self) -> None:  # Вызывается каждую секунду прослушывания
        if self.track_current_time >= self.track_time:  # Если прослушан весь трек то включаем слейдущий
            self.timer.stop()
            self.next_track()

        else:  # Если трек не закончился то обновим время в UI и зачислим прослушивание этой секунды
            self.track_current_time = self.track_current_time + 1
            self.horizontalSlider.setSliderPosition(self.track_current_time)
            self.labelTimeFirst.setText(time.strftime('%M:%S', time.gmtime(self.track_current_time)))
            self.track.snippet_list[self.track_current_time - 1] += 1

    def slider(self, value) -> None:
        if value != self.track_current_time and value != 0:  # Если произошла перемотка перемотаем трек в pygame.mixer.music
            self.value = value

    def slider_release(self) -> None:  # Слайдер отпустили
        self.track_current_time = self.value
        self.player.set_pos(self.value)
        self.labelTimeFirst.setText(time.strftime('%M:%S', time.gmtime(self.track_current_time)))

    def get_tracks(self) -> None:  # Если трек пропал из music но не из плейлиста вернём его
        try:
            for track_id in self.playlist.tracks_id:
                if not f"{track_id}.mp3" in os.listdir(self.dir_):
                    get_files.load_mp3_to_directory(track_id, self.dir_)

        except:
            pass

    def add_del_to_playlist(self) -> None:  # Добавляем или удаляем из медиатеки
        if self.track.id in self.playlist.tracks_id:
            self.playlist.remove(self.track.id)
            self.remove_track(self.track.id)
            self.add_remove.setText("+")

        else:
            self.playlist.add(self.track.id)
            self.get_tracks()
            self.add()  # Обновляем QListWidget
            self.add_remove.setText("-")

    def remove_track(self, id) -> None:  # Удаляем трэк из music/
        os.remove(self.dir_ + "/" + str(id) + ".mp3")
        self.add()  # Обновляем QListWidget

    def search(self) -> None:  # Метод поиска
        self.search_text = self.SearchCombox.lineEdit().text()  # Получаем текст запроса

        if self.search_text:  # Если не пустой
            self.results = get_files.search(self.search_text)  # получаем результаты поиска с сервера

            self.SearchCombox.clear()  # Очищаем поиск

            self.SearchCombox.addItem("Результаты по запросу: " + self.search_text)

            if self.results is None:
                self.SearchCombox.addItem("Ничего не найдено")
                self.SearchCombox.showPopup()

            else:  # Добавляем результаты в поиск
                self.search_dict = dict()
                for item in self.results:
                    self.search_dict[item[1]] = item[0]
                    self.SearchCombox.addItem(item[1])
                self.SearchCombox.showPopup()  # Показываем результаты

            self.SearchCombox.lineEdit().clear()  # Очищаем строку поиска

    def load(self, item) -> None:  # Загружаем трек из поиска
        if self.SearchCombox.currentIndex() not in (-1, 0):
            try:  # Пробуем загрузить трек в плеер
                track_text = self.SearchCombox.currentText()
                id = self.search_dict[track_text]

                self.load_track(item, id=id)
                self.SearchCombox.lineEdit().clear()

            except KeyError:
                self.search()

    def clear_preload(self) -> None:
        for filename in os.listdir("preload"):
            file_path = os.path.join("preload", filename)

            try:
                if os.path.isfile(file_path) and file_path != "preload/.gitkeep":  # Удаляем всё кроме .gitkeep
                    os.remove(file_path)

            except Exception as e:
                print(f'Ошибка при удалении файла {file_path}. {e}')

    def saving_indicators(self):  # Сохраняем параметры при выходе
        with open("Last_Indicators.json", "w") as f:
            f.write(json.dumps({'Volume': self.player.get_volume(), 'Select_dir': self.dir_for_offline}))

    def load_indicators(self):  # Загружаем параметры при запуске
        with open("Last_Indicators.json") as f:
            indicators = json.load(f)
            self.player.set_volume(indicators['Volume'])
            self.horizontalSliderVolume.setValue(int(indicators['Volume'] * 100))
            self.dir_for_offline = indicators['Select_dir']

    def change_mode(self) -> None:
        mode = self.Rad_group.checkedId()

        self.select_mode = ("Local", "Online")[mode - 1]  # Получаем выбранный режим

        if self.select_mode == "Local":
            # self.Update_btn.setEnabled(False)
            self.OpenFolder.setEnabled(True)
            self.add_remove.hide()
            self.SearchCombox.setEnabled(False)
            self.pushButtonSearch.setEnabled(False)
            self.dir_ = self.dir_for_offline
            self.add()

        else:
            self.Update_btn.setEnabled(True)
            self.OpenFolder.setEnabled(False)
            self.add_remove.show()
            self.SearchCombox.setEnabled(True)
            self.pushButtonSearch.setEnabled(True)
            self.dir_ = "music"
            self.add()

    def check_snippet_zone(self):  # Проверяем можем ли запустить сниппет
        zone = snippets.create_seconds_zone(self.track.snippet_list)
        if len(zone) == 0:
            self.snippet_btn.setEnabled(False)
            self.track.zone = None
        else:
            self.snippet_btn.setEnabled(True)
            self.track.zone = zone


class Alert(QWidget):  # Класс для уведомлений
    def __init__(self, Alert_text: str = "Alert") -> None:
        super(Alert, self).__init__()
        uic.loadUi('ui/alert.ui', self)

        self.label.setText(Alert_text)

        self.show()
