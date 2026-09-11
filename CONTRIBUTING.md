# Contributing

Thanks for your interest in improving this project.

## Ground rules

1. One logical change per pull request.
2. Run the test suite before pushing: `pip install -e . && pip install pytest && pytest -q`
3. Keep changes small and reviewable; describe what and why.

## Repository layout

- src/meetingtax/ - ICS parsing, recurrence expansion, fragmentation
- 	ests/ - the test suite (pip install -e . && pytest -q)
- samples/ - a bundled team calendar used by the tests
