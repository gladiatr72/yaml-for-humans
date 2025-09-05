

when running tests:
  - if .venv does not exist, run `uv venv .venv --seed`
  - always run `. .venv/bin/activate`
  - to run the tests: `uv run pytest -v`
  - to test the cli, first run `uv sync`

use generator comprehension whenever practical

before testing the cli:
  - always run `. .venv/bin/activate`
  - run `uv pip uninstall yaml-for-humans`
  - run `uv pip install .`

