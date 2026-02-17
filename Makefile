.PHONY: install test build clean publish

install:
    pip install -e .[dev]

test:
    pytest tests/ -v

build:
    python -m build

clean:
    rm -rf build/ dist/ *.egg-info
    find . -type d -name __pycache__ -exec rm -rf {} +
    find . -type f -name '*.pyc' -delete

publish: clean build
    twine check dist/*
    twine upload dist/*

dev-install:
    pip install -e .