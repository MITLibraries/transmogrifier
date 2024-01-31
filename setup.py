from setuptools import setup  # type: ignore[import-untyped]

setup(
    name="transmogrifier",
    version="0.1.0",
    install_requires=[
        "click",
        "sentry-sdk",
    ],
    entry_points={
        "console_scripts": [
            "transform=transmogrifier.cli:main",
        ]
    },
    python_requires=">=3.11",
)
