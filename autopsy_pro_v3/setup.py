"""Setup script for Autopsy Pro v3"""
from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding='utf-8') if readme_file.exists() else ""

setup(
    name="autopsy-pro",
    version="3.0.0",
    author="Autopsy Pro Team",
    description="Extract and rebuild code from inactive projects",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/autopsy-pro",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=[
        # Core has no dependencies beyond stdlib
    ],
    extras_require={
        "frameworks": [
            "django>=4.2.0",
            "flask>=2.3.0",
            "fastapi>=0.100.0",
            "uvicorn[standard]>=0.23.0",
        ],
        "cli": [
            "rich>=13.0.0",
            "click>=8.1.0",
        ],
        "performance": [
            "orjson>=3.9.0",
        ],
        "dev": [
            "pytest>=7.4.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.4.0",
        ],
        "all": [
            "django>=4.2.0",
            "flask>=2.3.0",
            "fastapi>=0.100.0",
            "uvicorn[standard]>=0.23.0",
            "rich>=13.0.0",
            "click>=8.1.0",
            "orjson>=3.9.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "autopsy-pro=autopsy_pro_v3.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
