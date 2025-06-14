#!/usr/bin/env python3
import os
import sys
import uvicorn

def main():
    # Get port from environment
    port = int(os.getenv("PORT", 8000))
    
    print(f"🚀 PRISMY Starting on port: {port}")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    
    # Start uvicorn
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0", 
        port=port,
        log_level="info"
    )

if __name__ == "__main__":
    main()
