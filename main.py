#!/usr/bin/env python3
"""
Company Management API - Entry Point
"""

if __name__ == "__main__":
    import uvicorn
    from app.main import app
    
    uvicorn.run(app, host="0.0.0.0", port=8080)
    