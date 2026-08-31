from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import router  # Note: your snippet said 'route.py' but imported from 'routes'

app = FastAPI(title="LinkedInForge API")

app.add_middleware(
    CORSMiddleware,
    # Update this to your deployed frontend domain once you move off localhost
    allow_origins=["http://localhost:3000"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/")
def health():
    return {"status": "ok", "message": "LinkedInForge Agents Online"}