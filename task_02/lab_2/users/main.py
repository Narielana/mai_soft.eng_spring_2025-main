import contextlib
import json

from fastapi import FastAPI

from auth import router as auth_router
from users import router as users_router


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    with open("openapi.json", "w") as f:
        json.dump(app.openapi(), f)

    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
def read_root():
    return {"status": "ok"}


app.include_router(auth_router)
app.include_router(users_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
