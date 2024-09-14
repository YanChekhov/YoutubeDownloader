import sys
import subprocess
import os
import logging
import platform
import zipfile
import shutil
import re
import json
from datetime import datetime
from queue import Queue
import threading

# Список необходимых пакетов
required_packages = [
    'pyperclip',
    'yt_dlp',
    'ttkthemes',
    'pydub',
    'mutagen',
    'Pillow',
    'requests',
]

def install_packages(packages):
    for package in packages:
        try:
            __import__(package)
        except ImportError:
            print(f"Установка пакета: {package}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def load_config():
    """Загрузка конфигурации из config.json или создание его с настройками по умолчанию"""
    default_config = {
        "ffmpeg_path": "",
        "download_dir": "Download",
        "db_path": "downloads.db"
    }
    if not os.path.exists('config.json'):
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=4)
    with open('config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

config = load_config()

def get_ffmpeg_path():
    """Определение пути к FFmpeg"""
    if config['ffmpeg_path']:
        return config['ffmpeg_path']
    else:
        return os.path.join(os.getcwd(), 'ffmpeg')

FFMPEG_PATH = get_ffmpeg_path()

install_packages(required_packages)

def check_and_install_ffmpeg():
    """Проверяет наличие FFmpeg и устанавливает его при необходимости."""
    import requests
    import zipfile
    import shutil

    ffmpeg_exe = os.path.join(FFMPEG_PATH, 'ffmpeg.exe')
    if not os.path.isfile(ffmpeg_exe):
        print("FFmpeg не найден. Попытка загрузить FFmpeg...")
        try:
            # Скачиваем статическую сборку FFmpeg для Windows
            ffmpeg_url = 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip'
            zip_path = os.path.join(os.getcwd(), 'ffmpeg-release-essentials.zip')
            # Скачиваем zip-файл
            response = requests.get(ffmpeg_url, stream=True)
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            # Распаковываем zip-файл
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(os.getcwd())
            # Перемещаем файлы в FFMPEG_PATH
            extracted_dir = [d for d in os.listdir(os.getcwd()) if 'ffmpeg' in d and os.path.isdir(d)][0]
            bin_dir = os.path.join(os.getcwd(), extracted_dir, 'bin')
            if not os.path.exists(FFMPEG_PATH):
                os.makedirs(FFMPEG_PATH)
            shutil.move(os.path.join(bin_dir, 'ffmpeg.exe'), FFMPEG_PATH)
            shutil.move(os.path.join(bin_dir, 'ffprobe.exe'), FFMPEG_PATH)
            # Очистка
            shutil.rmtree(os.path.join(os.getcwd(), extracted_dir))
            os.remove(zip_path)
        except Exception as e:
            print(f"Не удалось установить FFmpeg: {e}")
            sys.exit(1)
    else:
        print("FFmpeg уже установлен.")

check_and_install_ffmpeg()

# Настройка логирования
logging.basicConfig(filename='app.log', level=logging.ERROR,
                    format='%(asctime)s %(levelname)s:%(message)s')

# Теперь импортируем все необходимые модули
import pyperclip
import yt_dlp as youtube_dl
import re
from pydub import AudioSegment, silence
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, APIC, ID3NoHeaderError
from PIL import Image
from io import BytesIO
import sqlite3
import threading
from tkinter import ttk, messagebox, filedialog
import tkinter as tk
from ttkthemes import ThemedTk
import requests

class YouTubeDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Downloader")
        self.root.geometry("+{}+{}".format(self.root.winfo_screenwidth() // 2 - 300,
                                         self.root.winfo_screenheight() // 2 - 200))
        self.root.resizable(False, False)
        self.root.attributes('-fullscreen', False)

        # Настройка стилей
        style = ttk.Style(self.root)
        style.configure('TLabel', background='#f0f0f0')
        style.configure('TButton', background='#f0f0f0', foreground='#000000', font=('Arial', 12))
        style.configure('TCombobox', background='#ffffff', foreground='#000000', font=('Arial', 12),
                        selectbackground='#ffffff', selectforeground='#000000')
        style.map('TCombobox', fieldbackground=[('readonly', '#ffffff')],
                  background=[('readonly', '#ffffff')])

        # Основные директории
        self.BASE_DIR = os.path.dirname(os.path.abspath(sys.executable)) if getattr(sys, 'frozen', False) else os.path.abspath(".")
        self.DOWNLOAD_DIR = os.path.join(self.BASE_DIR, config.get('download_dir', 'Download'))
        os.makedirs(self.DOWNLOAD_DIR, exist_ok=True)

        # Инициализация базы данных
        self.init_db()

        # Создание очереди загрузок
        self.download_queue = Queue()
        threading.Thread(target=self.worker, daemon=True).start()

        # Создание интерфейса
        self.create_widgets()

    def init_db(self):
        """Инициализация базы данных для истории загрузок"""
        try:
            self.conn = sqlite3.connect(config.get('db_path', 'downloads.db'))
            self.cursor = self.conn.cursor()
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS downloads
                                   (id INTEGER PRIMARY KEY, url TEXT, type TEXT, date TIMESTAMP, status TEXT)''')
            self.conn.commit()
        except Exception as e:
            logging.error(f"Ошибка инициализации базы данных: {e}")
            messagebox.showerror("Ошибка", "Не удалось инициализировать базу данных.")

    def create_widgets(self):
        """Создание всех виджетов интерфейса"""
        frame = tk.Frame(self.root, bg='#f0f0f0')
        frame.grid(row=0, column=0, padx=10, pady=10, columnspan=3)

        self.url_label = tk.Label(frame, width=50, font=('Arial', 12), bg='white', anchor='w',
                                  relief='sunken', text="Нажмите здесь, чтобы вставить URL")
        self.url_label.grid(row=0, column=0, padx=(0, 10), pady=10, columnspan=3)
        self.url_label.bind('<Button-1>', self.handle_click)
        self.url_label.bind('<Button-3>', self.handle_click)

        # Кнопки загрузки
        download_video_button = ttk.Button(frame, text="Скачать видео", command=self.download_video_thread)
        download_video_button.grid(row=1, column=0, pady=10, padx=5)

        download_audio_button = ttk.Button(frame, text="Скачать аудио", command=self.download_audio_thread)
        download_audio_button.grid(row=1, column=1, pady=10, padx=5)

        download_audio_with_split_button = ttk.Button(frame, text="Скачать аудио с разбивкой",
                                                     command=self.download_audio_with_split_thread)
        download_audio_with_split_button.grid(row=1, column=2, pady=10, padx=5)

        # Настройка комбобокса для выбора качества
        tk.Label(self.root, text="Качество видео:", bg='#f0f0f0', font=('Arial', 12)).grid(row=2, column=0,
                                                                                              padx=10, pady=10,
                                                                                              sticky='e')
        self.quality_combobox = ttk.Combobox(self.root, values=[], font=('Arial', 12), state='readonly')
        self.quality_combobox.grid(row=2, column=1, padx=10, pady=10, columnspan=2, sticky='w')

        # Прогресс-бар
        self.progress_bar = ttk.Progressbar(self.root, orient='horizontal', mode='determinate', length=400)
        self.progress_bar.grid(row=3, column=0, columnspan=3, padx=10, pady=10)

        # Статус-лейбл
        self.status_var = tk.StringVar()
        self.status_label = tk.Label(self.root, textvariable=self.status_var, bg='#f0f0f0', font=('Arial', 12))
        self.status_label.grid(row=4, column=0, columnspan=3, pady=10)
        self.status_var.set("Готов к работе")

        # Кнопка для показа/скрытия лога с иконкой
        self.log_button = ttk.Button(self.root, text="📋", command=self.toggle_log, width=2)
        self.log_button.grid(row=5, column=0, padx=10, pady=10, sticky='w')

        # Текстовый виджет для лога
        self.status_text = tk.Text(self.root, height=10, width=60, state='disabled', wrap='word', font=('Arial', 12))
        self.status_text.grid(row=6, column=0, columnspan=3, padx=10, pady=10)
        self.status_text.grid_remove()  # Скрываем лог по умолчанию

        self.enable_text_widget_copy_paste(self.status_text)

        # Меню
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Выход", command=self.root.quit)

        history_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="История", menu=history_menu)
        history_menu.add_command(label="Показать историю", command=self.show_history)

    def handle_click(self, event):
        """Обработка клика по метке URL"""
        try:
            clipboard_content = pyperclip.paste()
            if self.is_valid_youtube_url(clipboard_content):
                self.url_label.config(text=clipboard_content)
                self.download_queue.put(('analyze', clipboard_content))
            else:
                messagebox.showerror("Ошибка", "Буфер обмена не содержит действительный URL YouTube.")
        except Exception as e:
            logging.error(f"Ошибка при обработке клика: {e}")
            messagebox.showerror("Ошибка", "Произошла ошибка при обработке URL.")

    def is_valid_youtube_url(self, url):
        """Проверка, является ли URL действительным YouTube-ссылкой"""
        youtube_regex = re.compile(
            r'(https?://)?(www\.)?'
            r'(youtube|youtu|youtube-nocookie)\.(com|be)/'
            r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')
        return youtube_regex.match(url)

    def analyze_url(self, url):
        """Анализ URL и заполнение информации о видео"""
        self.update_status("Анализ URL...")
        try:
            ydl_opts = {}
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                video_title = info_dict.get('title', 'video')  # Получаем название видео
                uploader = info_dict.get('uploader', '')  # Получаем имя автора
                tags = info_dict.get('tags', [])  # Получаем теги
                thumbnail_url = info_dict.get('thumbnail', '')  # URL обложки
                formats = info_dict.get('formats', [])
                quality_options = set()
                format_map = {}
                for f in formats:
                    if f.get('vcodec') != 'none':
                        height = f.get('height')
                        if height:
                            label = f"{height}p"
                            quality_options.add(label)
                            format_map[label] = f['format_id']
                self.quality_combobox['values'] = sorted(list(quality_options), reverse=True,
                                                        key=lambda x: int(x[:-1]))
                if quality_options:
                    self.quality_combobox.current(0)
                self.quality_combobox.format_map = format_map
                self.video_info = {
                    'title': video_title,
                    'uploader': uploader,
                    'tags': ', '.join(tags),
                    'thumbnail_url': thumbnail_url
                }
            self.update_status("Анализ завершен.")
        except Exception as e:
            logging.error(f"Ошибка при анализе URL: {e}")
            self.update_status("Ошибка: " + str(e))

    def download_video(self):
        """Скачивание видео"""
        if not self.check_ffmpeg_in_path():
            return

        url = self.url_label.cget("text")
        quality = self.quality_combobox.get()

        if not url:
            messagebox.showerror("Ошибка", "Введите URL видео.")
            return

        if not quality or quality not in self.quality_combobox.format_map:
            messagebox.showerror("Ошибка", "Выберите доступное качество.")
            return

        format_id = self.quality_combobox.format_map[quality]
        self.update_status("Скачивание видео...")

        try:
            ydl_opts = {
                'format': f"{format_id}+bestaudio/best",
                'outtmpl': os.path.join(self.DOWNLOAD_DIR, '%(title)s_%(resolution)s.%(ext)s'),
                'ffmpeg_location': FFMPEG_PATH,
                'progress_hooks': [self.download_progress_hook],
                'merge_output_format': 'mp4',
                'socket_timeout': 60,  # Увеличиваем время ожидания
                'retries': 5,          # Количество повторных попыток
            }
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            self.update_status("Загрузка видео завершена.")
            self.add_to_history(url, "video", "Завершено")
        except Exception as e:
            logging.error(f"Ошибка при скачивании видео: {e}")
            self.update_status("Ошибка: " + str(e))
            self.add_to_history(url, "video", f"Ошибка: {e}")

    def download_audio(self):
        """Скачивание аудио"""
        if not self.check_ffmpeg_in_path():
            return

        url = self.url_label.cget("text")

        if not url:
            messagebox.showerror("Ошибка", "Введите URL видео.")
            return

        self.update_status("Скачивание аудио...")

        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(self.DOWNLOAD_DIR, '%(title)s.%(ext)s'),
                'ffmpeg_location': FFMPEG_PATH,
                'progress_hooks': [self.download_progress_hook],
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',  # Фиксированный формат mp3
                    'preferredquality': '192',  # Качество аудио
                }],
                'socket_timeout': 60,
                'retries': 5,
                'fragment_retries': 5,
            }
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            self.update_status("Загрузка аудио завершена.")

            # Путь к скачанному аудио
            audio_file = None
            for file in os.listdir(self.DOWNLOAD_DIR):
                if file.endswith('.mp3'):
                    audio_file = os.path.join(self.DOWNLOAD_DIR, file)
                    break

            if audio_file:
                self.apply_metadata(audio_file, prefill_metadata=True)
                self.add_to_history(url, "audio", "Завершено")
            else:
                self.update_status("Ошибка: Не удалось найти скачанное аудио.")
                self.add_to_history(url, "audio", "Ошибка: Не найден файл аудио")
        except Exception as e:
            logging.error(f"Ошибка при скачивании аудио: {e}")
            self.update_status("Ошибка: " + str(e))
            self.add_to_history(url, "audio", f"Ошибка: {e}")

    def download_audio_with_split(self):
        """Скачивание аудио с разбивкой на части"""
        if not self.check_ffmpeg_in_path():
            return

        url = self.url_label.cget("text")

        if not url:
            messagebox.showerror("Ошибка", "Введите URL видео.")
            return

        self.update_status("Скачивание аудио с разбивкой...")

        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(self.DOWNLOAD_DIR, '%(title)s.%(ext)s'),
                'ffmpeg_location': FFMPEG_PATH,
                'progress_hooks': [self.download_progress_hook],
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',  # Фиксированный формат mp3
                    'preferredquality': '192',  # Качество аудио
                }],
                'socket_timeout': 60,
                'retries': 5,
                'fragment_retries': 5,
            }
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            self.update_status("Загрузка аудио завершена.")

            # Путь к скачанному аудио
            audio_file = None
            for file in os.listdir(self.DOWNLOAD_DIR):
                if file.endswith('.mp3'):
                    audio_file = os.path.join(self.DOWNLOAD_DIR, file)
                    break

            if audio_file:
                self.apply_metadata(audio_file, prefill_metadata=True)
                self.add_to_history(url, "audio_split", "Завершено")
                self.update_status("Разбивка аудио на части по 25 минут...")
                self.split_audio_logically(audio_file, self.DOWNLOAD_DIR, max_duration=25*60*1000)
                self.update_status("Разбивка завершена.")
            else:
                self.update_status("Ошибка: Не удалось найти скачанное аудио.")
                self.add_to_history(url, "audio_split", "Ошибка: Не найден файл аудио")
        except Exception as e:
            logging.error(f"Ошибка при скачивании аудио с разбивкой: {e}")
            self.update_status("Ошибка: " + str(e))
            self.add_to_history(url, "audio_split", f"Ошибка: {e}")

    def split_audio_logically(self, audio_path, output_dir, max_duration=25*60*1000):
        """
        Разбивает аудио на части по max_duration миллисекунд, стараясь делать это на паузах.
        :param audio_path: Путь к исходному аудио файлу.
        :param output_dir: Директория для сохранения частей.
        :param max_duration: Максимальная продолжительность каждой части в миллисекундах.
        """
        try:
            audio = AudioSegment.from_file(audio_path)
            silence_thresh = audio.dBFS - 16  # Порог тишины
            min_silence_len = 1000  # Минимальная длина тишины в миллисекундах

            # Находим паузы в аудио
            silent_ranges = silence.detect_silence(audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh)
            silent_ranges = [(start, end) for start, end in silent_ranges]

            segments = []
            start_idx = 0

            for silent_start, silent_end in silent_ranges:
                if silent_start - start_idx >= max_duration:
                    # Найдена пауза, подходящая для разрыва
                    segments.append((start_idx, silent_start))
                    start_idx = silent_end

            # Добавляем оставшуюся часть
            if start_idx < len(audio):
                segments.append((start_idx, len(audio)))

            # Получаем базовое имя файла без расширения
            base_name = os.path.basename(audio_path)
            name_without_ext = os.path.splitext(base_name)[0]

            # Сохраняем сегменты
            for i, (start, end) in enumerate(segments):
                segment = audio[start:end]
                output_path = os.path.join(output_dir, f"{name_without_ext}{i+1}.mp3")
                segment.export(output_path, format="mp3")
                self.update_status(f"Часть {i+1} сохранена: {output_path}")
                # Применяем метаданные к каждой части
                self.apply_metadata(output_path, prefill_metadata=True)
        except Exception as e:
            logging.error(f"Ошибка при разбивке аудио: {e}")
            self.update_status("Ошибка при разбивке аудио: " + str(e))

    def apply_metadata(self, audio_path, prefill_metadata=False):
        """
        Открывает диалоговое окно для ввода метаданных и применяет их к указанному аудиофайлу.
        :param audio_path: Путь к аудиофайлу.
        :param prefill_metadata: Если True, предварительно заполняет поля метаданными из video_info.
        """
        def set_metadata():
            author = author_var.get().strip()
            tag = tag_var.get().strip()
            cover_path = cover_var.get()

            if not author or not tag:
                messagebox.showerror("Ошибка", "Пожалуйста, заполните все обязательные поля (Имя автора и Главный тег).")
                return

            try:
                audio = MP3(audio_path, ID3=ID3)
            except ID3NoHeaderError:
                audio = MP3(audio_path)
                audio.add_tags()

            audio_tags = audio.tags

            # Установка основных метаданных
            audio_tags.add(TPE1(encoding=3, text=author))  # Исполнитель
            audio_tags.add(TIT2(encoding=3, text=tag))     # Название

            # Добавление обложки, если выбрана
            if cover_path:
                try:
                    if cover_path.startswith('http://') or cover_path.startswith('https://'):
                        response = requests.get(cover_path)
                        if response.status_code == 200:
                            img_data = response.content
                        else:
                            img_data = None
                    else:
                        with open(cover_path, 'rb') as img_file:
                            img_data = img_file.read()

                    if img_data:
                        mime_type = 'image/jpeg' if cover_path.lower().endswith(('.jpg', '.jpeg')) else 'image/png'
                        audio_tags.add(
                            APIC(
                                encoding=3,         # 3 - utf-8
                                mime=mime_type,     # Тип изображения
                                type=3,             # Тип обложки (3 - обложка фронтальная)
                                desc='Cover',
                                data=img_data
                            )
                        )
                except Exception as e:
                    logging.error(f"Ошибка при добавлении обложки: {e}")
                    self.update_status(f"Ошибка при добавлении обложки: {e}")

            audio.save()
            messagebox.showinfo("Успех", f"Метаданные успешно применены к {os.path.basename(audio_path)}.")
            metadata_window.destroy()

        # Создание нового окна для ввода метаданных
        metadata_window = tk.Toplevel(self.root)
        metadata_window.title("Добавить метаданные")
        metadata_window.geometry("400x400")
        metadata_window.grab_set()  # Делает окно модальным

        # Инициализация переменных с предзаполненными значениями
        if prefill_metadata and hasattr(self, 'video_info'):
            prefill_author = self.video_info.get('uploader', '')
            prefill_tag = self.video_info.get('tags', '')
            prefill_cover = self.video_info.get('thumbnail_url', '')
        else:
            prefill_author = ""
            prefill_tag = ""
            prefill_cover = ""

        tk.Label(metadata_window, text="Имя автора:", font=('Arial', 12)).pack(pady=10)
        author_var = tk.StringVar(value=prefill_author)
        author_entry = ttk.Entry(metadata_window, textvariable=author_var, width=50)
        author_entry.pack(pady=5)

        tk.Label(metadata_window, text="Главный тег:", font=('Arial', 12)).pack(pady=10)
        tag_var = tk.StringVar(value=prefill_tag)
        tag_entry = ttk.Entry(metadata_window, textvariable=tag_var, width=50)
        tag_entry.pack(pady=5)

        tk.Label(metadata_window, text="Обложка (опционально):", font=('Arial', 12)).pack(pady=10)
        cover_var = tk.StringVar()
        cover_entry = ttk.Entry(metadata_window, textvariable=cover_var, width=50, state='readonly')
        cover_entry.pack(pady=5, padx=10, fill='x')

        def browse_cover():
            file_path = filedialog.askopenfilename(
                title="Выберите обложку",
                filetypes=[("Image Files", "*.jpg *.jpeg *.png")]
            )
            if file_path:
                cover_var.set(file_path)

        browse_button = ttk.Button(metadata_window, text="Выбрать обложку", command=browse_cover)
        browse_button.pack(pady=5)

        # Если есть предзаполненная обложка, скачиваем ее временно
        if prefill_metadata and prefill_cover:
            try:
                response = requests.get(prefill_cover)
                if response.status_code == 200:
                    img = Image.open(BytesIO(response.content))
                    temp_cover_path = os.path.join(self.DOWNLOAD_DIR, 'temp_cover.jpg')
                    img.save(temp_cover_path)
                    cover_var.set(temp_cover_path)
            except Exception as e:
                logging.error(f"Ошибка при загрузке обложки: {e}")
                self.update_status(f"Ошибка при загрузке обложки: {e}")

        apply_button = ttk.Button(metadata_window, text="Применить", command=set_metadata)
        apply_button.pack(pady=20)

    def check_ffmpeg_in_path(self):
        """Проверка наличия FFmpeg по указанному пути"""
        ffmpeg_exe = os.path.join(FFMPEG_PATH, 'ffmpeg.exe')
        if not os.path.isfile(ffmpeg_exe):
            messagebox.showerror("Ошибка", f"FFmpeg не найден по пути {ffmpeg_exe}. Пожалуйста, перезапустите программу для автоматической установки FFmpeg.")
            return False
        os.environ["PATH"] += os.pathsep + FFMPEG_PATH
        return True

    def download_progress_hook(self, d):
        """Обработчик прогресса загрузки"""
        if d['status'] == 'downloading':
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
            if total_bytes:
                progress = d['downloaded_bytes'] / total_bytes * 100
                self.progress_bar['value'] = progress
                speed = d.get('_speed_str', 'N/A')
                eta = d.get('_eta_str', 'N/A')
                # Удаляем ANSI escape-коды
                speed_clean = self.remove_ansi_escape_sequences(speed)
                eta_clean = self.remove_ansi_escape_sequences(eta)
                status_message = f"Загрузка... {progress:.2f}% Скорость: {speed_clean} ETA: {eta_clean}"
                self.update_status(status_message)
                self.root.update_idletasks()
        elif d['status'] == 'finished':
            self.progress_bar['value'] = 100
            self.update_status("Скачивание завершено, обработка...")

    def remove_ansi_escape_sequences(self, text):
        """Удаление ANSI escape-кодов из текста"""
        ansi_escape = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')
        return ansi_escape.sub('', text)

    def update_status(self, message):
        """Обновление статусной строки и лога"""
        self.status_var.set(message)
        self.status_text.config(state='normal')
        self.status_text.insert(tk.END, message + '\n')
        self.status_text.config(state='disabled')
        self.status_text.see(tk.END)
        self.root.update_idletasks()

    def toggle_log(self):
        """Показать или скрыть лог"""
        if self.status_text.winfo_viewable():
            self.status_text.grid_remove()
        else:
            self.status_text.grid()

    def enable_text_widget_copy_paste(self, text_widget):
        """Включение копирования и вставки для текстового виджета"""
        def copy(event=None):
            text_widget.event_generate("<<Copy>>")
            return "break"

        def select_all(event=None):
            text_widget.tag_add("sel", "1.0", "end")
            return "break"

        text_widget.bind("<Control-c>", copy)
        text_widget.bind("<Control-a>", select_all)

        # Добавляем контекстное меню
        def show_context_menu(event):
            context_menu.tk_popup(event.x_root, event.y_root)
            return "break"

        context_menu = tk.Menu(text_widget, tearoff=0)
        context_menu.add_command(label="Копировать", command=lambda: text_widget.event_generate("<<Copy>>"))
        context_menu.add_command(label="Выделить всё", command=lambda: text_widget.event_generate("<<SelectAll>>"))

        text_widget.bind("<Button-3>", show_context_menu)  # Правая кнопка мыши

    def add_to_history(self, url, type_, status):
        """Добавление записи в историю загрузок"""
        try:
            self.cursor.execute("INSERT INTO downloads (url, type, date, status) VALUES (?, ?, ?, ?)",
                                (url, type_, datetime.now(), status))
            self.conn.commit()
        except Exception as e:
            logging.error(f"Ошибка при добавлении в историю: {e}")

    def show_history(self):
        """Отображение истории загрузок"""
        try:
            self.cursor.execute("SELECT * FROM downloads ORDER BY date DESC")
            records = self.cursor.fetchall()

            history_window = tk.Toplevel(self.root)
            history_window.title("История загрузок")
            history_window.geometry("600x400")

            columns = ('ID', 'URL', 'Тип', 'Дата', 'Статус')
            tree = ttk.Treeview(history_window, columns=columns, show='headings')
            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, width=100, anchor='center')

            for record in records:
                tree.insert('', tk.END, values=record)

            tree.pack(expand=True, fill='both')

            scrollbar = ttk.Scrollbar(history_window, orient=tk.VERTICAL, command=tree.yview)
            tree.configure(yscroll=scrollbar.set)
            scrollbar.pack(side='right', fill='y')
        except Exception as e:
            logging.error(f"Ошибка при отображении истории: {e}")
            messagebox.showerror("Ошибка", "Не удалось загрузить историю загрузок.")

    def worker(self):
        """Рабочий поток для обработки очереди загрузок"""
        while True:
            task = self.download_queue.get()
            if task[0] == 'analyze':
                self.analyze_url(task[1])
            elif task[0] == 'download_video':
                self.download_video()
            elif task[0] == 'download_audio':
                self.download_audio()
            elif task[0] == 'download_audio_with_split':
                self.download_audio_with_split()
            self.download_queue.task_done()

    def download_video_thread(self):
        """Добавление задачи скачивания видео в очередь"""
        self.download_queue.put(('download_video',))

    def download_audio_thread(self):
        """Добавление задачи скачивания аудио в очередь"""
        self.download_queue.put(('download_audio',))

    def download_audio_with_split_thread(self):
        """Добавление задачи скачивания аудио с разбивкой в очередь"""
        self.download_queue.put(('download_audio_with_split',))

    def run(self):
        """Запуск основного цикла приложения"""
        self.root.mainloop()

if __name__ == '__main__':
    try:
        root = ThemedTk(theme="arc")
        app = YouTubeDownloaderApp(root)
        app.run()
    except Exception as e:
        logging.error(f"Необработанное исключение: {e}")
        messagebox.showerror("Ошибка", "Произошла критическая ошибка. Проверьте лог для подробностей.")
