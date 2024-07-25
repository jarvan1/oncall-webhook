from fastapi import FastAPI
from app.routes import v1_routes
from app.core.router import register_routers
from fastapi.responses import ORJSONResponse

def create_app() -> FastAPI:
    app = FastAPI(
        default_response_class=ORJSONResponse
    )
    register_routers(app, v1_routes)
    return app


app = create_app()

