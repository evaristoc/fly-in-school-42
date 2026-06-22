# Define the path to the virtual environment's python/pip 
VENV = .venv
PYTHON = $(VENV)/bin/python3 
PIP := $(VENV)/bin/pip 

.PHONY: all install-deps install run debug extract lint clean re
# Setup virtual environment and dependencies 
install: $(VENV)/bin/activate install-deps 

$(VENV)/bin/activate: extract
	@test -d $(VENV) || (echo "Creating .venv..." && python3 -m venv $(VENV)) 
	@test -f $(VENV)/bin/pip || $(VENV)/bin/python -m ensurepip
	@test -f $(VENV)/bin/pip || ln -s $(VENV)/bin/pip3 $(VENV)/bin/pip
	$(VENV)/bin/pip install --upgrade pip 
	@sh ./$(VENV)/bin/activate
	@echo "Virtual environment ready." 
	
# Install dependencies
# .venv/Script/xxxx instead of .venv/bin/xxx for MS
# then source .venv/Scripts/activate when using git-bash
# somes do `poetry lock --no-update` before this one too
install-deps: 
	@echo "Installing Python dependencies..." 
	@.venv/bin/pip install poetry
	@.venv/bin/poetry install --no-root
	@echo "Handshake complete. Dependencies are synced." 
	
# # Run the project 
run:
	@$(PYTHON) main.py

extract:
	@test -f maps.tar.gz && tar -xvzf maps.tar.gz || (echo "maps.tar.gz not found"; exit 1)

# # Debug the project (using pdb) 
debug: 
	@$(PYTHON) -m pdb main.py

# # Linting and type checking 
lint-mypy: 
	@echo "Running mypy..." 
	@$(PYTHON) -m mypy src --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs || true

lint-flake:
	@echo "Running flake8..." 
	@$(PYTHON) -m flake8 src --max-line-length=79 || true

lint: lint-mypy lint-flake

# Clean temporary files 
clean: 
	rm -rf $(VENV)
	rm -rf maps
	find . -type d -name "__pycache__" -exec rm -rf {} + 
	find . -type d -name "*.egg-info" -exec rm -rf {} + 
	find . -type f -name "*.pyc" -delete
	find . -type f -name "poetry.log" -delete
	find . -type f -name "poetry.lock" -delete
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type f -name "map_output.txt" -exec rm -f {} +
	@echo "Clean complete."

re:
	make clean
	make