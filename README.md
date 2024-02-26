# casher

## python
```bash
# инструмент для управления зависимостями
$ pip install poetry
$ pip install --user poetry
```

## poetry
```bash
# сделать пакетным менеджером poetry
$ poetry init
# добавление пакетов
$ poetry add fastapi uvicorn
$ poetry add pymongo
$ poetry add pytest --dev

poetry remove pymongo
```

## fastapi
```bash
# запустить сервер
$ uvicorn --factory api.app:create_app --reload
```

## docker
```bash
$ docker compose -f docker_compose/app.yaml up
```