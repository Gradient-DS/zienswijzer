from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
#from .utils.text_processor import transform_text
from db import init_db

app = FastAPI(title="WOO Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


class TextInput(BaseModel):
    text: str


class TextOutput(BaseModel):
    original: str
    transformed: str


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "ok"}


@app.post("/transform", response_model=TextOutput)
def transform(input_data: TextInput):
    """Transform text by randomly changing words"""
    original_text = input_data.text
    transformed_text = transform_text(original_text)
    return TextOutput(original=original_text, transformed=transformed_text)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
