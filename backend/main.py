from fastapi import FastAPI
from api.routes.review import router

def main():
    print("CodeGuard backend starting...")
    print(router)

if __name__ == "__main__":
    main()
