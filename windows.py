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

class Track:
    id: int
    mutagenfile: EasyID3
    title: str
    artist: str
    title_and_artist: str
    path: str
    duration: int
    snippet: bool
    snippet_list: list[int]

    def __init__(self, path: str, id: int = 0) -> None:
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
        if self.id == 0:
            if self.title_and_artist in snippets_dict.keys():
                self.snippet = True
                return snippets_dict[self.title_and_artist]
            else:
                return snippets.create_snippet_list(self.duration)
        else:
            snippet_list = get_files.get_snippet(self.id)
            if snippet_list == None:
                return snippets.create_snippet_list(self.duration)
            else:
                return snippet_list

    def update_snippet_list(self) -> None:
        if self.id == 0:
            global snippets_dict
            snippets_dict[self.title_and_artist] = self.snippet_list
        else:
            get_files.post_snippet(self.id, self.snippet_list)


class PlayList:
    def __init__(self) -> None:
        try:
            with open("media/playlist.txt") as f:
                self.tracks_id = eval(f.read())
        except FileNotFoundError:
            with open("media/playlist.txt", "w") as f:
                f.write("[]")
                self.tracks_id = list()

    def update(self) -> None:
        with open("media/playlist.txt", "w") as f:
            f.write(str(self.tracks_id))

    def add(self, id: int) -> None:
        self.tracks_id.append(id)
        self.update()

    def remove(self, id) -> None:
        self.tracks_id.pop(self.tracks_id.index(id))
        self.update()


class MainWindow(QMainWindow):
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
        uic.loadUi('ui/mainwindow.ui', self)

        mixer.init()

        self.track = None

        self.search_dict = dict()

        self.dir_for_offline = "LocalTracks"

        self.timer = QTimer()
        self.timer.setInterval(1000)  # Миллисекунды
        self.timer.timeout.connect(self.time)

        self.player = mixer.music
        self.player.set_volume(0.5)
        self.player.state = 0

        self.horizontalSliderVolume.setValue(50)

        self.pushButtonPlay.setEnabled(False)
        self.horizontalSlider.setEnabled(False)
        self.add_remove.setEnabled(False)
        self.OpenFolder.setEnabled(False)
        self.snippet_btn.setEnabled(False)

        self.playlist = PlayList()

        self.installing_signals()
        self.show()

        self.load_indicators()

        if get_files.check_connection():
            self.select_mode = "Online"
            self.dir_ = "music"
        else:
            self.select_mode = "Local"
            self.dir_ = self.dir_for_offline
            self.OnlineRad.setEnabled(False)
            self.al = Alert(Alert_text="Не удалось подключится к серверу. Режим оффлайн")

        self.get_tracks()
        self.add()

    # Добавляем треки в список
    def add(self) -> None:
        self.listWidget.clear()

        if self.select_mode == "Online":
            global created_id
            self.get_tracks()

            file_list = [i for i in os.listdir(self.dir_)]

            mp3_list = []
            for i in file_list:
                if i[-4:] == ".mp3":
                    mp3_list.append(i[:-4])

            self.track_list = []
            for file_name in mp3_list:
                id = int(file_name)
                Track_object = Track(self.dir_ + "/" + file_name + ".mp3", id=id)
                self.track_list.append(Track_object)
                created_id[id] = Track_object

        else:
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

    def set_dir(self) -> None:
        self.dir_ = QFileDialog.getExistingDirectory(None, 'Select a folder:', self.dir_)

        if self.dir_:
            self.add()
            self.dir_for_offline = self.dir_

    def closeEvent(self, event) -> None:
        try:
            global snippets_dict

            self.track.update_snippet_list()
            snippets.write_json(snippets_dict)
            self.clear_preload()
            self.saving_indicators()
            event.accept()  # let the window close

        except AttributeError:
            event.accept()

    # Загрузка трека в плеер
    def installing_signals(self) -> None:
        self.listWidget.itemClicked.connect(self.load_track)
        self.pushButtonPlay.clicked.connect(self.play_music)
        self.pushButtonNextMusic.clicked.connect(self.next_track)
        self.pushButtonStEd.clicked.connect(self.back_track)
        self.horizontalSliderVolume.valueChanged.connect(self.volume_changed)
        self.horizontalSlider.valueChanged.connect(self.slider)
        self.horizontalSlider.sliderReleased.connect(self.slider_release)
        self.OpenFolder.clicked.connect(self.set_dir)
        # self.pushButtonSearch.clicked.connect(self.search)
        # self.lineEditSearchPath.returnPressed.connect(self.search)
        self.add_remove.clicked.connect(self.add_del_to_playlist)
        self.pushButtonSearch.clicked.connect(self.search)
        self.SearchCombox.lineEdit().returnPressed.connect(self.search)
        self.SearchCombox.activated.connect(self.load)
        self.Rad_group = QButtonGroup()
        self.Rad_group.addButton(self.LocalRad, 1)
        self.Rad_group.addButton(self.OnlineRad, 2)
        self.Rad_group.buttonClicked.connect(self.change_mode)
        self.Update_btn.clicked.connect(self.add)
        self.snippet_btn.clicked.connect(self.run_snippet)

    def load_track(self, item, id=0, start=0) -> None:
        if self.track:
            self.track.update_snippet_list()
        if id == 0:
            try:
                self.index = self.listWidget.currentRow()
                self.track = self.track_list[self.index]
                self.labelMusic.setText(self.track.title_and_artist)
                self.player.load(self.track.path)
                self.track_time = self.track.duration
                self.player.state = 1
                self.ui_load_track()
                self.track_current_time = start
                self.timer.start()
                self.player.play(loops=0, start=start)
            except IndexError:
                pass

        else:
            get_files.load_mp3_to_directory(id, "preload/")
            if not id in created_id.keys():
                self.track_list.append(Track(f"preload/{id}.mp3", id=id))
                self.track = self.track_list[len(self.track_list) - 1]
            else:
                self.track = created_id[id]

            self.labelMusic.setText(self.track.title_and_artist)
            self.player.load(self.track.path)
            self.track_time = self.track.duration
            self.player.state = 1
            self.ui_load_track()
            self.track_current_time = start
            self.timer.start()
            self.player.play(loops=0, start=start)

        self.check_snippet_zone()

    def run_snippet(self):
        self.load_track(None, id=self.track.id, start=self.track.zone[0])

    def ui_load_track(self) -> None:
        self.horizontalSlider.setSliderPosition(0)
        self.labelTime.setText(f"{time.strftime('%M:%S', time.gmtime(self.track_time))}")
        self.horizontalSlider.setMaximum(int(self.track_time))
        self.pushButtonPlay.setEnabled(True)
        self.labelTimeFirst.setText("00:00")
        self.horizontalSlider.setEnabled(True)

        if self.track.id in self.playlist.tracks_id:
            self.add_remove.setEnabled(True)
            self.add_remove.setText("-")

        elif self.track.id == 0:
            self.add_remove.setDisabled(True)

        else:
            self.add_remove.setEnabled(True)
            self.add_remove.setText("+")

    def play_music(self) -> None:
        if self.player.state == 0:
            self.player.state = 1
            self.player.unpause()
            self.timer.start()

        else:
            self.player.pause()
            self.timer.stop()
            self.player.state = 0

    def next_track(self) -> None:
        if self.listWidget.currentRow() != self.listWidget.count() - 1:
            new_item = self.listWidget.item(self.listWidget.currentRow() + 1)

        else:
            new_item = self.listWidget.item(0)

        self.listWidget.setCurrentItem(new_item)
        self.load_track(new_item)

    def back_track(self) -> None:
        if self.player.get_pos() > 3000:
            self.load_track(self.listWidget.item(self.listWidget.currentRow()))

        else:
            if self.listWidget.currentRow() != 0:
                new_item = self.listWidget.item(self.listWidget.currentRow() - 1)

            else:
                new_item = self.listWidget.item(self.listWidget.count() - 1)

            self.listWidget.setCurrentItem(new_item)
            self.load_track(new_item)


    def volume_changed(self, value) -> None:
        self.player.set_volume(value / 100)

    def time(self) -> None:
        if self.track_current_time >= self.track_time:
            self.timer.stop()
            self.next_track()

        else:
            self.track_current_time = self.track_current_time + 1
            self.horizontalSlider.setSliderPosition(self.track_current_time)
            self.labelTimeFirst.setText(time.strftime('%M:%S', time.gmtime(self.track_current_time)))
            self.track.snippet_list[self.track_current_time - 1] += 1

    def slider(self, value) -> None:
        if value != self.track_current_time and value != 0:
            self.value = value

    def slider_release(self) -> None:
        self.track_current_time = self.value
        self.player.set_pos(self.value)
        self.labelTimeFirst.setText(time.strftime('%M:%S', time.gmtime(self.track_current_time)))

    def get_tracks(self) -> None:
        try:
            for track_id in self.playlist.tracks_id:
                if not f"{track_id}.mp3" in os.listdir(self.dir_):
                    get_files.load_mp3_to_directory(track_id, self.dir_)

        except:
            pass

    def add_del_to_playlist(self) -> None:
        if self.track.id in self.playlist.tracks_id:
            self.playlist.remove(self.track.id)
            self.remove_track(self.track.id)
            self.add_remove.setText("+")

        else:
            self.playlist.add(self.track.id)
            self.get_tracks()
            self.add()
            self.add_remove.setText("-")

    def remove_track(self, id) -> None:
        os.remove(self.dir_ + "/" + str(id) + ".mp3")
        self.add()

    def search(self) -> None:
        self.search_text = self.SearchCombox.lineEdit().text()

        if self.search_text:
            self.results = get_files.search(self.search_text)

            self.SearchCombox.clear()

            self.SearchCombox.addItem("Результаты по запросу: " + self.search_text)

            if self.results is None:
                self.SearchCombox.addItem("Ничего не найдено")

            else:
                self.search_dict = dict()
                for item in self.results:
                    self.search_dict[item[1]] = item[0]
                    self.SearchCombox.addItem(item[1])
                self.SearchCombox.showPopup()

            self.SearchCombox.lineEdit().clear()

    def load(self, item) -> None:
        if self.SearchCombox.currentIndex() not in (-1, 0):
            try:
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
                if os.path.isfile(file_path) and file_path != "preload/.gitkeep":
                    os.remove(file_path)

            except Exception as e:
                print(f'Ошибка при удалении файла {file_path}. {e}')

    def saving_indicators(self):
        with open("Last_Indicators.json", "w") as f:
            f.write(json.dumps({'Volume': self.player.get_volume(), 'Select_dir': self.dir_for_offline}))

    def load_indicators(self):
        with open("Last_Indicators.json") as f:
            indicators = json.load(f)
            self.player.set_volume(indicators['Volume'])
            self.horizontalSliderVolume.setValue(int(indicators['Volume'] * 100))
            self.dir_for_offline = indicators['Select_dir']



    def change_mode(self) -> None:
        mode = self.Rad_group.checkedId()

        self.select_mode = ("Local", "Online")[mode - 1]

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

    def check_snippet_zone(self):
        zone = snippets.create_seconds_zone(self.track.snippet_list)
        if len(zone) == 0:
            self.snippet_btn.setEnabled(False)
            self.track.zone = None
        else:
            self.snippet_btn.setEnabled(True)
            self.track.zone = zone

        print("OK check", self.track.zone)


class Alert(QWidget):
    def __init__(self, Alert_text="Alert") -> None:
        super(Alert, self).__init__()
        uic.loadUi('ui/alert.ui', self)

        self.label.setText(Alert_text)

        self.show()
