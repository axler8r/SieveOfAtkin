# command aliases
PYTHON = python3

# location aliases
SRC_DIR = sieve
BLD_DIR = build
DST_DIR = dist


# phony targets
.PHONY: get-started init exe clean check format help

# targets
get-started:
	@echo "Get started with the project..."
	@echo "  'make init' to initialize the project"
	@echo "  'source .venv/bin/activate' to activate the virtual environment"
	@echo "  'bin/help' to see the available commands"

init:
	@echo "Initializing uv environment..."
	uv python install 3.12
	uv venv
	uv sync

exe:
	@echo "Generate the primes executalbe..."
	pyinstaller --onefile --name primes $(SRC_DIR)/main.py

clean:
	@echo "Cleaning up..."
	rm -rf $(BLD_DIR) $(DST_DIR) **/*.spec **/*.bin ./__pycache__ **/__pycache__

check:
	@echo "Check source code..."
	ruff check

format:
	@echo "Format souce code..."
	ruff format

help:
	@echo "Usage: make [target]"
	@echo "Targets:"
	@echo "  get-started:      Get started with the project"
	@echo "  init:             Initialize the project"
	@echo "  exe:              Generate the primes executable"
	@echo "  clean:            Clean the project"
	@echo "  check:            Check the project"
	@echo "  format:           Format the project"
	@echo "  help:             Show this help message"
