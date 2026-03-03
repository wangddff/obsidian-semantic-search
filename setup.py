from setuptools import setup, find_packages

with open("README_GITHUB.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="obsidian-semantic-search",
    version="1.0.0",
    author="wangddff",
    author_email="your.email@example.com",
    description="Semantic search for Obsidian notes using BGE-M3 and LanceDB",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/obsidian-semantic-search",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Text Processing :: General",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.14",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.14",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "obsidian-search=src.pipeline_integration:main",
        ],
    },
    include_package_data=True,
    keywords="obsidian, semantic-search, bge-m3, lancedb, vector-search, note-taking",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/obsidian-semantic-search/issues",
        "Source": "https://github.com/yourusername/obsidian-semantic-search",
        "Documentation": "https://github.com/yourusername/obsidian-semantic-search#readme",
    },
)