# ruff: noqa: T201  # noqa: INP001
"""Tiny CLI runner used by cram tests for the Playwright launcher.

Prints parsed config in a deterministic format on success. Errors are produced
by the framework itself (argparse + CliBuilder) and go to stderr with exit
code 2.
"""

import io
import sys

from ocarina.opinionated.cli.playwright.cli_store_singleton import (
    PlaywrightCliStoreSingleton as CliStoreSingleton,
)
from ocarina.opinionated.cli.playwright.create_cli_store import (
    create_playwright_cli_store,
)


def main() -> None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", newline="\n")

    CliStoreSingleton().push(create_playwright_cli_store())
    store = CliStoreSingleton()
    print(f"browser={store.get('browser')}")
    print(f"profile_path={store.get('profile_path')}")
    print(f"headless={store.get('headless')}")
    print(f"workers={store.get('workers')}")
    print(f"wait_timeout={store.get('wait_timeout')}")
    print(f"logger={store.get('logger')}")
    print(f"video_dir={store.get('video_dir')}")
    print(f"trace_dir={store.get('trace_dir')}")
    print(f"only={store.get('only')}")
    print(f"exclude={store.get('exclude')}")


if __name__ == "__main__":
    main()
