from setuptools import setup, find_namespace_packages

setup(
    name="homeymind",
    version="0.1.0",
    packages=find_namespace_packages(include=['app*', 'homey*', 'utils*']),
    install_requires=[
        "fastapi>=0.68.0",
        "uvicorn>=0.15.0",
        "pydantic>=1.8.0",
        "autogen>=0.2.0",
        "pyyaml>=6.0",
        "sse-starlette>=0.10.0",
        "paho-mqtt>=1.6.1",
        "python-dotenv>=0.19.0",
        "aiohttp>=3.8.0",
        "openai>=1.0.0",
        "python-multipart>=0.0.5",
        "websockets>=10.0",
        "async-timeout>=4.0.0",
    ],
    extras_require={
        "test": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",
        ],
    },
    python_requires=">=3.8",
    author="Your Name",
    description="A voice-controlled home automation assistant using LLMs and AutoGen agents",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    package_data={
        "app": ["*.yaml", "*.json"],
        "homey": ["*.yaml", "*.json"],
        "utils": ["*.yaml", "*.json"],
    },
) 