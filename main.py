import os
import re
import time
import streamlit as st
from mutagen.mp3 import MP3
import threading
import pygame
import chardet


class MusicPlayer:
    def __init__(self):
        self.music_list = []
        self.current_index = 0
        self.duration = 0
        self.paused = False
        self.start_play = False
        self.lyrics = []
        self.lyrics_time = []
        self.lyric_index = 0

        pygame.init()
        pygame.mixer.init(frequency=16000)

        self.play_button = st.button('播放', on_click=self.play_music)
        self.pause_button = st.button('暂停', on_click=self.pause_music)
        self.previous_button = st.button('上一首', on_click=self.previous_music)
        self.next_button = st.button('下一首', on_click=self.next_music)

        self.music_label = st.empty()
        self.time_label = st.empty()
        self.lyric_label = st.empty()

        self.load_music_files()

        self.music_thread = threading.Thread(target=self.music_loop)
        self.music_thread.daemon = True  # Set the daemon attribute directly
        self.music_thread.start()

    def load_music_files(self):
        current_directory = os.getcwd()
        st.write(f'当前工作目录: {current_directory}')
        st.write('目录中的文件:')
        st.write(os.listdir(current_directory))  # 列出目录中的文件

        for file_name in os.listdir(current_directory):
            if file_name.endswith('.mp3'):
                music_path = os.path.join(current_directory, file_name)
                lrc_path = os.path.join(current_directory, file_name[:-3] + 'lrc')
                if os.path.exists(lrc_path):
                    self.music_list.append({'path': music_path, 'lrc': lrc_path})
                else:
                    self.music_list.append({'path': music_path, 'lrc': ''})

        if not self.music_list:
            st.warning('目录中没有找到音乐文件。')

    def play_music(self):
        if not self.music_list:
            st.warning('目录中没有找到音乐文件。')
            return

        if not self.start_play:
            self.music_path = self.music_list[self.current_index]['path']
            self.lrc_path = self.music_list[self.current_index]['lrc']
            pygame.mixer.music.load(self.music_path)
            pygame.mixer.music.play()
            self.duration = MP3(self.music_path).info.length
            self.start_play = True
            self.paused = False
            self.get_lyric()
            self.update_time_label()
        else:
            pygame.mixer.music.stop()
            self.start_play = False
            self.lyric_label.empty()
            self.lyric_index = 0

    def pause_music(self):
        if not self.paused:
            pygame.mixer.music.pause()
            self.paused = True
        else:
            pygame.mixer.music.unpause()
            self.paused = False

    def previous_music(self):
        if self.music_list:
            self.current_index = (self.current_index - 1) % len(self.music_list)
            self.play_music()

    def next_music(self):
        if self.music_list:
            self.current_index = (self.current_index + 1) % len(self.music_list)
            self.play_music()

    def get_lyric(self):
        self.lyrics.clear()
        self.lyrics_time.clear()
        if self.lrc_path == '':
            return
        with open(self.lrc_path, 'rb') as f:
            raw_data = f.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding']

        with open(self.lrc_path, 'r', encoding=encoding) as f:
            lrc_data = f.readlines()

        pattern = re.compile(r'\[(\d+:\d+\.\d+)\]')
        for line in lrc_data:
            matches = pattern.findall(line)
            if matches:
                time_str = matches[0]
                time_parts = time_str.split(':')
                m = float(time_parts[0])
                s = float(time_parts[1])
                time = m * 60 + s
                self.lyrics_time.append(time)
                lyric = line.replace(f'[{time_str}]', '').strip()
                self.lyrics.append(lyric)

    def update_time_label(self):
        while self.start_play:
            try:
                current_time = pygame.mixer.music.get_pos() / 1000
            except pygame.error:
                return
            current_time_str = time.strftime('%H:%M:%S', time.gmtime(current_time))
            duration_time_str = time.strftime('%H:%M:%S', time.gmtime(self.duration))
            self.time_label.text(f'{current_time_str} / {duration_time_str}')
            if self.lyrics_time:
                if current_time > self.lyrics_time[self.lyric_index]:
                    self.lyric_label.text(self.lyrics[self.lyric_index])
                    self.lyric_index += 1
                    if self.lyric_index == len(self.lyrics):
                        self.lyric_index = 0
            time.sleep(0.1)

    def music_loop(self):
        while True:
            if not self.start_play:
                self.music_label.text('Music Player')
            else:
                self.music_label.text('Now Playing: ' + os.path.basename(self.music_list[self.current_index]['path']))
            time.sleep(0.1)


if __name__ == '__main__':
    try:
        pygame.mixer.init(frequency=16000)
    except pygame.error:
        st.error('无法初始化pygame音频输出')
    else:
        st.title('Music Player')
        st.write('请将mp3文件和对应的lrc歌词文件放在同一个文件夹中')
        st.write('支持同步显示歌词')
        mp = MusicPlayer()
