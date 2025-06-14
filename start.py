import os
import uvicorn

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"🚀 Starting PRISMY Minimal on port: {port}")
    uvicorn.run("src.api.main_minimal:app", host="0.0.0.0", port=port)
