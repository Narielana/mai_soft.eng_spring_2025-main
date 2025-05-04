from fastapi import FastAPI
import uvicorn
import contextlib
import json

from delivery import router as delivery_router

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    with open("openapi.json", "w") as f:
        json.dump(app.openapi(), f)
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
def read_root():
    return {"status": "ok", "service": "delivery-service"}


app.include_router(delivery_router)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8081)
