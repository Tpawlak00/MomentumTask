from fastapi import FastAPI
from book.book_services import router as book_router
from utils.logger import log_request
import uvicorn

app = FastAPI()


@app.get("/")
async def am_i_working():
    return {"message": f"Yes, app works!"}

app.middleware("http")(log_request)

app.include_router(book_router, prefix="/book")

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
