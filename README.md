<p align="center">
  <img src="https://github.com/mojo-molotov/ocarina/blob/main/ocarina-logo.png?raw=true" alt="description" width="904"/>
</p>

# Ocarina

A Python browser test automation framework built on Railway Oriented Programming (ROP).

## Overview

Ocarina is a pure-Python framework that provides a
declarative DSL for composing browser tests.

Its defining characteristic is that
every test step is a link in a Railway chain: on failure, the rest of the chain
short-circuits and the error is captured as a value rather than propagated as an
exception.

This keeps test code flat and the failure path explicit.

Notable features:

- Railway-based action chains with first-class success/failure handlers.
- Hierarchical test orchestration: `Test` → `TestSuite` → `TestCampaign` → `TestCycle`.
- Parallel execution with a thread-safe WebDriver pool.
- Automatic retries on transient errors.
- Conditional branching via `match_page` for pages that can render in multiple states.
- Fluent assertion chains via `validate`.
- Built-in reporters: pretty-print (ANSI), JSON, DOCX proof documents, timing, screenshots.
- Framework-agnostic `POMBase`; the Selenium integration is one of several possible adapters.
- Ships its own test runner: Ocarina is NOT a pytest plugin.

## Requirements

- Python **3.14+**
- (SELENIUM) A matching WebDriver binary on disk (`chromedriver`, `geckodriver`, `msedgedriver`) for the browser you intend to use. Safari uses the native macOS `safaridriver` and needs no binary on disk.

## Documentation

See [**The Ocarina Holy Book**](https://mojo-molotov.github.io/ocarina-holy-book)

## Installation

```bash
pip install ocarina
```

## Core concepts

- **POM** — page objects subclass [`POMBase`](src/ocarina/pom/base.py); the base class is browser-agnostic.
- **Scenario** — a factory `(driver, logger) -> Scenario(test_chain, setup, teardown, watchers)` built from [`Scenario`](src/ocarina/custom_types/scenario.py).
- **Railway chain** — actions are wrapped with [`create_act`](src/ocarina/dsl/testing_with_railway/constructors/create_act.py), which returns a builder with `.failure(...)`, `.success(...)`, and `.execute()`.
- **drive_page** — [`drive_page`](src/ocarina/opinionated/dsl/drive_page.py) composes multiple acts into a single chain.
- **match_page** — [`match_page`](src/ocarina/dsl/testing_with_railway/match_page.py) branches on which of several states a page is in.
- **validate** — [`validate`](src/ocarina/dsl/invariants/validate.py) is a fluent assertion chain with alternatives and aggregated errors.
- **Test orchestrators** — `Test` (one case), `TestSuite` (parallel + retry policy), `TestCampaign` (sequential suites), `TestCycle` (smoke campaigns before main campaigns).

## CLI flags (opinionated Selenium launcher)

Parsed by [`create_selenium_auto_cli_store`](src/ocarina/opinionated/cli/selenium/create_cli_store.py). Headless mode is the default; use `--not-headless` to opt out.

| Flag                           | Default         | Notes                                                           |
|--------------------------------|-----------------|-----------------------------------------------------------------|
| `--driver-path`                | `""`            | Path to the WebDriver binary (not used on Safari).              |
| `--browser`                    | *required*      | `chrome`, `firefox`, `edge` (Windows), `safari` (macOS).        |
| `--not-headless`               | off             | Shows the browser UI.                                           |
| `--workers`                    | `5`             | Parallel workers (size of the driver pool).                     |
| `--wait-timeout`               | `10`            | Selenium implicit wait seconds (max `60`).                      |
| `--profile-path`               | `None`          | Browser profile directory (not supported on Safari).            |
| `--logger`                     | `terminal+file` | One of `terminal`, `file`, `terminal+file`, `muted`.            |
| `--dont-force-delete-tmp-dirs` | off             | Skip the post-run cleanup of Selenium temp profiles on Windows. |
| `--exclude`                    | []              | Exclude tests by IDs.                                           |
| `--only`                       | []              | Select tests by IDs.                                            |

## Reporting

The `opinionated/plugins/reports` package ships four reporters that can be passed to `bootstrap` via `run_plugins`:

- **pretty-print** — hierarchical ANSI summary on stdout.
- **JSON results** — structured results.
- **DOCX proofs** — Word document assembled from logs (requires FileLogger).
- **timing** — context manager that prints total test duration.

Screenshots are captured automatically on failure (when `autoscreen_on_fail=True` on a suite) and can also be triggered explicitly through the `ITakeScreenshot` port.

## Full example

For a complete, runnable project:
- CI workflow,
- Real page objects,
- OTP-based login coordinated through Redis,
- Data-driven suites,
- File upload tests,
- Chaos scenarios

See [**ocarina-example**](https://github.com/mojo-molotov/ocarina-example).

## Full AI example

See [**ocarina-with-ai-example**](https://github.com/mojo-molotov/ocarina-with-ai-example).

## Development

From a clone of this repo:

```bash
make install              # create .venv and install with dev deps
make test                 # pytest + coverage + allure results
make check-coding-style   # mypy + ruff
make ruff-format          # apply formatting
make serve-htmlcov        # open the HTML coverage report
make serve-allure         # open the Allure report
```

## Misc

[Allure report](https://mojo-molotov.github.io/ocarina/allure-report/)

## License

MIT — Igor Casanova.

---

Built by [@mojo-molotov](https://github.com/mojo-molotov)  
Fueled by figatellu and Квас.
