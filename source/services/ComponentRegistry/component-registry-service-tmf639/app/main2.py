
if __name__ == "__main__":
    import uvicorn
    import os
    PORT = 8082
    os.environ["DATABASE_URL"] = "sqlite:///./resource_inventory2.db"
    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", PORT)),
        reload=True
    )