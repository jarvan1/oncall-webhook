import importlib
import pkgutil
import types

from fastapi import APIRouter, FastAPI


def _add_child_router(parent_router: APIRouter, child_router_module: types.ModuleType):
    parent_router.include_router(
        child_router_module.router,
        # prefix=f"/{child_router_module.endpoint_name}",
        tags=[child_router_module.endpoint_name],
    )


def _list_submodules(package: types.ModuleType) -> list[types.ModuleType]:
    submodules: list[types.ModuleType] = []
    for _, name, is_pkg in pkgutil.iter_modules(
        package.__path__,
        f"{package.__name__}.",
    ):
        if not is_pkg:
            module = importlib.import_module(name)
            submodules.append(module)
    return submodules


def register_routers(app: FastAPI, routers_parent_module: types.ModuleType):
    routers_module = _list_submodules(routers_parent_module)
    [
        _add_child_router(routers_parent_module.router, router)
        for router in routers_module
    ]
    app.include_router(
        routers_parent_module.router,
        prefix=routers_parent_module.VERSION_PREFIX,
    )
