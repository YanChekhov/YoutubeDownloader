Эта программа — это загрузчик видео и аудио с YouTube с графическим интерфейсом. Основные функции:

Поддержка скачивания видео и аудио с YouTube.
Возможность выбора качества видео перед загрузкой.
Скачивание аудио с возможностью разбивки на части по продолжительности.
Автоматическая загрузка и установка FFmpeg при необходимости.
Управление метаданными скачанных аудиофайлов, включая установку обложки и тегов.
История загрузок с возможностью её просмотра.
Программа автоматически устанавливает необходимые пакеты и настраивает рабочую среду.

This program is an YouTube video and audio downloader with a graphical interface. Key features include:

Support for downloading both video and audio from YouTube.
Ability to choose video quality before downloading.
Audio download with the option to split it into parts based on duration.
Automatic download and installation of FFmpeg if required.
Manage metadata for downloaded audio files, including cover art and tags.
Download history with a review option.
The program automatically installs necessary packages and configures the working environment.
md
Копировать код
# Как запустить программу

## Требования
- Убедитесь, что на вашем компьютере установлен Python 3. Если Python не установлен, скачайте его с [официального сайта](https://www.python.org/downloads/).

## Шаги для запуска программы:

```bash
1. Скачайте и установите Python:
   Перейдите на сайт https://www.python.org/downloads/, скачайте последнюю версию Python и установите её.
   Обязательно отметьте галочку **"Add Python to PATH"** при установке.

2. Установите необходимые зависимости:
   После установки Python, откройте командную строку (или PowerShell) и перейдите в папку с программой. 
   Для установки зависимостей введите команду:
   
   ```bash
   pip install -r requirements.txt
Если файл requirements.txt отсутствует, установите следующие зависимости вручную:

bash
Копировать код
pip install pyperclip yt_dlp ttkthemes pydub mutagen Pillow requests
Загрузите и установите FFmpeg: Программа автоматически скачает и установит FFmpeg, если его нет на вашем ПК. Но, если вы хотите установить FFmpeg вручную:

Перейдите на сайт FFmpeg и скачайте последнюю версию.
Добавьте путь к FFmpeg в переменную окружения PATH или укажите путь в config.json.
Запустите программу: Чтобы запустить программу, в командной строке введите:

bash
Копировать код
python YoutubeDownloader.py
Пример работы с программой:
Для скачивания видео или аудио вставьте ссылку в поле URL.
Выберите нужное качество или параметры скачивания.
Нажмите на соответствующую кнопку, чтобы загрузить видео или аудио.
