# YoutubeDownloader

-

## RU

-

### Описание

Эта программа — загрузчик видео и аудио с YouTube с графическим интерфейсом. Основные функции:

- Поддержка скачивания видео и аудио с YouTube.
- Возможность выбора качества видео перед загрузкой.
- Скачивание аудио с возможностью разбивки на части по продолжительности.
- Автоматическая загрузка и установка FFmpeg при необходимости.
- Управление метаданными скачанных аудиофайлов, включая установку обложки и тегов.
- История загрузок с возможностью её просмотра.
- Программа автоматически устанавливает необходимые пакеты и настраивает рабочую среду.

---

### Механизм работы

1. Когда вы запускаете программу, она проверяет, установлены ли все необходимые зависимости. Если какие-то из них отсутствуют, программа автоматически попытается их установить через `pip`.
2. После установки зависимостей программа загружает файл конфигурации `config.json`. Если файла нет, программа создаёт его с настройками по умолчанию, такими как директория для загрузки файлов и путь к базе данных.
3. Далее программа проверяет, установлен ли **FFmpeg**, который необходим для обработки аудио и видео файлов. Если **FFmpeg** не найден, программа автоматически скачает его и установит.
4. После всех проверок откроется графический интерфейс, где вы можете вставить ссылку на видео с YouTube.
5. В зависимости от выбора (видео или аудио), программа скачает файл в указанную директорию, используя **YouTube-DLP** для загрузки, и **FFmpeg** для конвертации.
6. Если выбрано аудио с разбивкой на части, программа автоматически разрежет файл на отрезки по 25 минут — это удобно для загрузки длинных подкастов или аудио-файлов и их перезаливки в Telegram-каналы.
7. Программа поддерживает добавление метаданных (название, автор, обложка) к аудиофайлам.

---

### Установка и запуск

1. Скачайте и установите Python 3.x с официального сайта.
2. Запустить программу YoutubeDownloader.py. Программа автоматически установит все необходимые зависимости и продолжит работу.

---

## EN

---

### Description

This program is a YouTube video and audio downloader with a graphical interface. Key features include:

- Support for downloading both video and audio from YouTube.
- Ability to choose video quality before downloading.
- Audio download with the option to split it into parts based on duration.
- Automatic download and installation of FFmpeg if required.
- Manage metadata for downloaded audio files, including cover art and tags.
- Download history with the ability to view it later.
- The program automatically installs the necessary packages and configures the working environment.

---

### How it works

1. When you run the program, it checks if all the necessary dependencies are installed. If any are missing, the program will automatically attempt to install them via `pip`.
2. After installing the dependencies, the program loads the `config.json` configuration file. If the file does not exist, the program creates it with default settings, such as the download directory and the path to the database.
3. The program then checks whether **FFmpeg** is installed, which is required for processing audio and video files. If **FFmpeg** is not found, the program will automatically download and install it.
4. After all checks, the graphical interface will open, where you can paste a YouTube video link.
5. Depending on your choice (video or audio), the program will download the file to the specified directory, using **YouTube-DLP** for downloading and **FFmpeg** for conversion.
6. If you select audio with splitting, the program will automatically split the file into 25-minute segments—this is useful for downloading long podcasts or audio files and uploading them to Telegram channels.
7. The program supports adding metadata (title, author, cover art) to audio files.

---

### Installation and Running

1. Download and install Python 3.x from the official website.
2. Run the program `YoutubeDownloader.py`. The program will automatically install all necessary dependencies and continue to run.
