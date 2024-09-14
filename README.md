# YoutubeDownloader
---
## Описание
Эта программа — загрузчик видео и аудио с YouTube с графическим интерфейсом. Основные функции:

Поддержка скачивания видео и аудио с YouTube.
Возможность выбора качества видео перед загрузкой.
Скачивание аудио с возможностью разбивки на части по продолжительности.
Автоматическая загрузка и установка FFmpeg при необходимости.
Управление метаданными скачанных аудиофайлов, включая установку обложки и тегов.
История загрузок с возможностью её просмотра.
Программа автоматически устанавливает необходимые пакеты и настраивает рабочую среду.
---
### Механизм работы
1. Когда вы запускаете программу, она проверяет, установлены ли все необходимые зависимости. Если какие-то из них отсутствуют, программа автоматически попытается их установить через pip.
2. После установки зависимостей программа загружает файл конфигурации config.json. Если файла нет, программа создаёт его с настройками по умолчанию, такими как директория для загрузки файлов и путь к базе данных.
3. Далее программа проверяет, установлен ли FFmpeg, который необходим для обработки аудио и видео файлов. Если FFmpeg не найден, программа автоматически скачает его и установит.
4. После всех проверок откроется графический интерфейс, где вы можете вставить ссылку на видео с YouTube.
5. В зависимости от выбора (видео или аудио), программа скачает файл в указанную директорию, используя YouTube-DLP для загрузки, и FFmpeg для конвертации.
6. Если выбрано аудио с разбивкой на части, программа автоматически разрежет файл на отрезки по 25 минут, сделал для загрузки длинных подкастов, разрезания на 25 минут и перезалива в телеграм канал.
7. Программа поддерживает добавление метаданных (название, автор, обложка) к аудиофайлам.



