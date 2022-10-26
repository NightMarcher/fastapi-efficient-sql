"""
working directory: fastapi-efficient-sql/
command: python -m examples.service
"""
import uvicorn


if __name__ == "__main__":
    uvicorn.run("examples.service:app", reload=True)
