import uvicorn
from mobile_server.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "mobile_server.main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=False,
    )
