from fastapi import FastAPI

from book.routes import router

app = FastAPI(title="Momentum Library", version="0.2.0")
app.include_router(router)


@app.get("/", tags=["health"])
def health():
    return {"message": "Yes, app works!"}
