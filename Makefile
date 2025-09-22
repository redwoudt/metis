# Makefile for Metis GenAI
clean:
	rm -rf __pycache__ 

# Create and activate virtual environment
env:
	python3 -m venv .venv
	source .venv/bin/activate

# Install runtime and development dependencies
install:
	. .venv/bin/activate || source .venv/bin/activate
	.venv/bin/pip install -r requirements.txt
	.venv/bin/pip install -r dev-requirements.txt

# Format code using black
format:
	. .venv/bin/activate || source .venv/bin/activate && \
	black metis tests examples

# Lint code using mypy
lint:
	. .venv/bin/activate || source .venv/bin/activate && \
	mypy metis

# Run tests (placeholder)
test:
	. .venv/bin/activate || source .venv/bin/activate && \
	pytest tests

# Run test coverage
coverage:
	. .venv/bin/activate || source .venv/bin/activate && \
	coverage run -m pytest && \
	coverage report -m && \
	coverage html

# Run an example script
run:
	. .venv/bin/activate || source .venv/bin/activate && \
	python examples/run_request.py

# TODO: Add CI integration commands here
