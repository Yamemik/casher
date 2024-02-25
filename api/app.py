from fastapi import FastAPI


def create_app():
    app = FastAPI(debug=True, docs_url="/api/swagger", title="FastAPI Casher")

    return app
