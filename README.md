# Homework_bot

Проект **Homework_bot** позволяет отслеживать статус домашней работы.

Бот делает запрос к API Практикум Домашка и отправляет сообщение в Telegram при изменении статуса работы.

## Содержание
- [Технологии](https://github.com/TimyrPahomov/homework_bot#технологии)
- [Локальный запуск](https://github.com/TimyrPahomov/homework_bot#локальный-запуск)
- [Автор](https://github.com/TimyrPahomov/homework_bot#автор)

## Технологии
- [Python](https://www.python.org/)
- [Telegram](https://core.telegram.org/)

## Локальный запуск
1. Необходимо клонировать репозиторий и перейти в него:

```sh
git clone https://github.com/TimyrPahomov/homework_bot.git
cd homework_bot/
```

2. Далее нужно создать и активировать виртуальное окружение:

```sh
python -m venv venv
source venv/Scripts/activate
```

3. Обновить пакетный менеджер и установить зависимости из файла _requirements.txt_:

```sh
python -m pip install --upgrade pip
pip install -r requirements.txt
```

4. Наконец, запустить проект:

```sh
python homework.py
```

## Автор
[Пахомов Тимур](<https://github.com/TimyrPahomov/>)