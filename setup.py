from pathlib import Path

from setuptools import find_packages, setup


ROOT = Path(__file__).parent
README = (ROOT / "README.md").read_text(encoding="utf-8")


setup(
    name="SpecGo",
    version="1.0.0",
    description="CLI-first spec-to-API agent for embedded protocols.",
    keywords=[
        "embedded",
        "protocol",
        "can",
        "dbc",
        "codegen",
        "code-generation",
        "validation",
        "testing",
        "property-testing",
        "toolchain",
    ],
    platforms=["Windows", "Linux", "macOS"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS",
        "Operating System :: POSIX :: Linux",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Software Development :: Testing",
        "Topic :: System :: Hardware :: Hardware Drivers",
    ],
    long_description=README,
    long_description_content_type="text/markdown",
    author="Ce Xu",
    license="Apache-2.0",
    python_requires=">=3.11",
    packages=find_packages(include=("specgo", "specgo.*")),
    include_package_data=True,
    package_data={
        "specgo": [
            "codegen/templates/README.md",
            "codegen/templates/c/*.j2",
            "llm/prompts/*.md",
        ]
    },
    install_requires=[
        "typer>=0.12.0",
        "pyyaml>=6.0",
        "pydantic>=2.0",
        "cantools>=39.0",
        "jinja2>=3.1.2",
    ],
    entry_points={
        "console_scripts": [
            "specgo=specgo.__main__:run",
        ]
    },
)
