#install requirements.txt & activate venv
#cd \backend; .\venv\Scripts\Activate
#uvicorn main:app
#uvicorn main:app --reload


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Paper Search Backend")

# Allow frontend (React + Vite) to access backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Backend is running successfully 🚀"}

#check health endpoint
@app.get("/health")
async def check_health():
    print("Health check endpoint called")
    return {"message": "hello world"}
    