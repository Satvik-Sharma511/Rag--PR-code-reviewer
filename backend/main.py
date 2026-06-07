from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import router as reviews_router
from api.webhooks import router as webhooks_router

app = FastAPI(title="RAG-Powered Code Reviewer API")

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to the frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(reviews_router)
app.include_router(webhooks_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the RAG Code Reviewer API"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
