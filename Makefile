MAKEFLAGS += --silent

PY_CMD ?= python3
VENV_BIN ?= .venv/bin
VENV_PYTHON ?= $(VENV_BIN)/python
VENV_PIP ?= $(VENV_BIN)/pip

ALLURE_RESULTS ?= allure-results
ALLURE_REPORT ?= allure-report

.PHONY: all
all:
	$(error This Makefile is not for compilation)

.PHONY: ruff-check
ruff-check:
	ruff check .

.PHONY: mypy-check
mypy-check:
	mypy src/ tests/

.PHONY: install-on-ci
install-on-ci:
	@test -d .venv || python -m venv .venv
	$(VENV_PYTHON) -m pip install --upgrade pip
	$(VENV_PIP) install -r requirements-dev.txt
	$(VENV_PIP) install -e . --no-deps

.PHONY: update-snapshots
update-snapshots:
	@echo "Running tests (only to update snapshots)..."
	-pytest --snapshot-update

.PHONY: cram-test
cram-test:
ifeq ($(OS),Windows_NT)
	@echo "N A P O L E O N  D I S A P P R O V E S  W I N D O W S"
else
	@echo "Running cram tests..."
	PYTHON="$(CURDIR)/$(VENV_PYTHON)" "$(CURDIR)/$(VENV_BIN)/prysk" tests/cram/
endif

.PHONY: test
test: cram-test
	@echo "Running tests..."
	-pytest --alluredir=$(ALLURE_RESULTS) -vv --hypothesis-show-statistics

.PHONY: generate-allure
generate-allure:
	@echo "Generating Allure report..."
	allure generate $(ALLURE_RESULTS) -o $(ALLURE_REPORT)
	@echo "Report generated in $(ALLURE_REPORT)/"

.PHONY: serve-allure
serve-allure:
	@echo "Opening Allure report..."
ifeq ($(OS),Windows_NT)
	@if exist $(ALLURE_REPORT) ( \
		allure open $(ALLURE_REPORT) \
	) else ( \
		echo No report found, generating from results... & \
		allure serve $(ALLURE_RESULTS) \
	)
else
	@if [ -d $(ALLURE_REPORT) ]; then \
		allure open $(ALLURE_REPORT); \
	else \
		echo "No report found, generating from results..."; \
		allure serve $(ALLURE_RESULTS); \
	fi
endif

.PHONY: serve-htmlcov
serve-htmlcov:
	@echo "Opening coverage report..."
	-python -c "import webbrowser, pathlib; webbrowser.open(pathlib.Path('htmlcov/index.html').resolve().as_uri())"

.PHONY: test-ui
test-ui: test generate-allure
	@$(MAKE) serve-htmlcov
	@$(MAKE) serve-allure

.PHONY: check-coding-style
check-coding-style: mypy-check ruff-check

.PHONY: create-venv
create-venv:
	$(PY_CMD) -m venv .venv

.PHONY: install
install:
ifeq ($(OS),Windows_NT)
	@if not exist .venv $(MAKE) create-venv
	.venv\Scripts\python.exe -m pip install --upgrade pip
	.venv\Scripts\pip.exe install -e . --group dev
	.venv\Scripts\pre-commit.exe install
else
	@test -d .venv || $(MAKE) create-venv
	.venv/bin/python -m pip install --upgrade pip
	.venv/bin/pip install -e . --group dev
	.venv/bin/pre-commit install
endif

.PHONY: ruff-format
ruff-format:
	ruff format .

.PHONY: clean-allure
clean-allure:
	@echo "Cleaning Allure artifacts..."
ifeq ($(OS),Windows_NT)
	-cmd /c "if exist $(ALLURE_RESULTS) rmdir /s /q $(ALLURE_RESULTS)"
	-cmd /c "if exist $(ALLURE_REPORT) rmdir /s /q $(ALLURE_REPORT)"
else
	rm -rf $(ALLURE_RESULTS) $(ALLURE_REPORT)
endif

.PHONY: clean
clean: clean-allure
	@echo "Cleaning all artifacts..."
ifeq ($(OS),Windows_NT)
	if exist __pycache__ rmdir /s /q __pycache__
	if exist .pytest_cache rmdir /s /q .pytest_cache
	if exist .coverage del /q .coverage
	if exist coverage.xml del /q coverage.xml
	if exist htmlcov rmdir /s /q htmlcov
	if exist .hypothesis rmdir /s /q .hypothesis
	if exist .mypy_cache rmdir /s /q .mypy_cache
	if exist .ruff_cache rmdir /s /q .ruff_cache
	for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
	for /d /r . %%d in (*.egg-info) do @if exist "%%d" rmdir /s /q "%%d"
	if exist .venv rmdir /s /q .venv
else
	rm -rf .venv __pycache__ .pytest_cache .coverage coverage.xml htmlcov .hypothesis .mypy_cache .ruff_cache *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
endif
