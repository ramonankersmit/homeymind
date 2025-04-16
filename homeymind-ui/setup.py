from setuptools import setup, find_packages

setup(
    name="homeymind",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "paho-mqtt",
        "python-dotenv",
        "pydantic",
        "sse-starlette",
        "pyyaml"
    ],
) 