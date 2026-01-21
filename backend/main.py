from fastapi import FastAPI
from api.routes.review import router as review_router

app = FastAPI(title="CodeGuard")

app.include_router(review_router)

@app.get("/")
def health_check():
    return {"status": "ok", "service": "CodeGuard"}

def main():
    print("CodeGuard backend starting...")

if __name__ == "__main__":
    main()