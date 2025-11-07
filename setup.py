"""Setup configuration for crypto-llm-trading package."""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="crypto-llm-trading",
    version="0.1.0",
    author="Pablo Felipe",
    author_email="pablofelipe01@gmail.com",
    description="Sistema automatizado de trading multi-LLM en Binance Futures",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pablofelipe01/ai-arena-ll",
    packages=find_packages(exclude=["tests", "tests.*", "docs", "scripts"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Office/Business :: Financial :: Investment",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "black==23.11.0",
            "ruff==0.1.6",
            "mypy==1.7.1",
            "ipython==8.17.2",
        ],
        "test": [
            "pytest==7.4.3",
            "pytest-asyncio==0.21.1",
            "pytest-cov==4.1.0",
            "pytest-mock==3.12.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "crypto-llm-trading=src.api.main:main",
            "init-system=scripts.init_system:main",
            "init-db=scripts.init_db:main",
        ],
    },
)
