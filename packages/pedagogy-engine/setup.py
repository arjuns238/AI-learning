"""Setup configuration for pedagogy-engine package."""

from setuptools import setup, find_packages

setup(
    name="pedagogy-engine",
    version="0.1.0",
    description="AI-powered pedagogical content generation system",
    packages=find_packages(include=["layer1", "layer1.*", "layer2", "layer2.*"]),
    python_requires=">=3.9",
    install_requires=[
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "anthropic>=0.18.0",
        "openai>=1.0.0",
        "python-dotenv>=1.0.0",
        "pyyaml>=6.0.0",
    ],
    extras_require={
        "test": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
        ]
    }
)
