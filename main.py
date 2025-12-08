import uvicorn
from airport_api import app
import os

if __name__ == "__main__":
    
    if os.getenv("ENV") != "dev":
        uvicorn.run("airport_api:app", host="0.0.0.0", port=8000, reload=True)

 
    
