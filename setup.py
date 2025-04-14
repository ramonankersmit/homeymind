from setuptools import setup, find_packages

setup(
    name="homeymind",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "pydantic",
        "autogen",
        "pyyaml",
        "sse-starlette",
    ],
    python_requires=">=3.8",
    author="Your Name",
    description="A voice-controlled home automation assistant using LLMs and AutoGen agents",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
) 