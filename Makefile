.PHONY: help clean build install test publish-test publish

PYTHON := python3
PIP := $(PYTHON) -m pip
TWINE := $(PYTHON) -m twine

help:
	@echo "batchtsocmd - Makefile targets"
	@echo ""
	@echo "Available targets:"
	@echo "  help          - Show this help message"
	@echo "  clean         - Remove build artifacts and cache files"
	@echo "  build         - Build the package distribution files"
	@echo "  install       - Install the package locally in development mode"
	@echo "  test          - Run tests (placeholder - no tests yet)"
	@echo "  publish-test  - Upload package to TestPyPI"
	@echo "  publish       - Upload package to PyPI"
	@echo ""
	@echo "Example workflow:"
	@echo "  make clean build    # Clean and build the package"
	@echo "  make publish-test   # Test upload to TestPyPI"
	@echo "  make publish        # Upload to PyPI"

clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf src/*.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	@echo "Clean complete."

build: clean
	@echo "Building package..."
	$(PYTHON) -m build
	@echo "Build complete. Distribution files are in dist/"

install:
	@echo "Installing package in development mode..."
	$(PIP) install -e .
	@echo "Installation complete."

test:
	@echo "Running tests..."
	@echo "Note: Tests must be run on z/OS with ZOAU installed."
	$(PYTHON) -m pytest tests/ -v

publish-test: build
	@echo "Uploading to TestPyPI..."
	@echo "Note: You need to have a TestPyPI account and API token configured."
	@echo "Configure with: python3 -m pip install --upgrade twine"
	$(TWINE) upload --repository testpypi dist/*
	@echo "Upload to TestPyPI complete."
	@echo "Test installation with:"
	@echo "  pip install --index-url https://test.pypi.org/simple/ batchtsocmd"

publish: build
	@echo "Uploading to PyPI..."
	@echo "Note: You need to have a PyPI account and API token configured."
	@echo "WARNING: This will publish to the public PyPI repository!"
	@read -p "Are you sure you want to publish to PyPI? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		$(TWINE) upload dist/*; \
		echo "Upload to PyPI complete."; \
	else \
		echo "Publish cancelled."; \
	fi