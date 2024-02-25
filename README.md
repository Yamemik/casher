# casher

## python
```bash
# создание виртуального пространства
$ python -m venv venv
# перейти в свое окружение
$ venv\Scripts\activate.bat
# деактивация
$ deactivate
# инструмент для управления зависимостями
$ pip install poetry
# установить fastapi
$ pip install fastapi[all]

```

## poetry
```bash
# сделать пакетным менеджером poetry
$ poetry init

```
## fastapi
```bash
# запустить сервер
$ uvicorn --factory api.app:create_app --reload

```
