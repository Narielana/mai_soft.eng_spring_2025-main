import contextlib
import json

from fastapi import FastAPI
import uvicorn


from api.auth import router as auth_router
from api.users import router as users_router


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    with open("openapi.json", "w") as f:
        json.dump(app.openapi(), f)
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def read_root():
    return {"status": "ok"}


app.include_router(auth_router)
app.include_router(users_router)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8082)
