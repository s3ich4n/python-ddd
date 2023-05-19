import time

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

import api.routers.catalog
from api.models.catalog import CurrentUser
from api.routers import bidding, catalog, iam
from config.api_config import ApiConfig
from config.container import Container
from seedwork.domain.exceptions import DomainException, EntityNotFoundException
from seedwork.infrastructure.logging import LoggerFactory, logger
from seedwork.infrastructure.request_context import request_context

# configure logger prior to first usage
LoggerFactory.configure(logger_name="api")

# dependency injection container
container = Container()
container.config.from_pydantic(ApiConfig())
container.wire(modules=[api.routers.catalog, api.routers.bidding, api.routers.iam])

app = FastAPI(debug=container.config.DEBUG)
app.include_router(catalog.router)
app.include_router(bidding.router)
app.include_router(iam.router)
app.container = container

logger.info("using db engine %s" % str(container.engine()))


@app.exception_handler(DomainException)
async def unicorn_exception_handler(request: Request, exc: DomainException):
    return JSONResponse(
        status_code=500,
        content={"message": f"Oops! {exc.name} did something. There goes a rainbow..."},
    )


@app.exception_handler(EntityNotFoundException)
async def unicorn_exception_handler(request: Request, exc: EntityNotFoundException):
    return JSONResponse(
        status_code=404,
        content={
            "message": f"Entity {exc.entity_id} not found in {exc.repository.__class__.__name__}"
        },
    )


@app.middleware("http")
async def add_request_context(request: Request, call_next):
    start_time = time.time()
    request_context.begin_request(current_user=CurrentUser.fake_user())
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response
    finally:
        request_context.end_request()


@app.get("/")
async def root():
    return {"info": "Online auctions API. See /docs for documentation"}


@app.get("/test")
async def test():
    import asyncio

    logger.debug("test1")
    await asyncio.sleep(3)
    logger.debug("test2")
    await asyncio.sleep(3)
    logger.debug("test3")
    await asyncio.sleep(3)
    logger.debug("test4")
    service = container.dummy_service()
    return {
        "service response": service.serve(),
        "correlation_id": request_context.correlation_id,
    }
