# ruff: noqa: T201  # noqa: INP001
"""Tiny CLI runner used by cram tests.

Forces the Linux-specific CLI store so tests are platform-stable on any Linux
runner. Prints parsed config in a deterministic format on success. Errors are
produced by the framework itself (argparse + CliBuilder) and go to stderr with
exit code 2.
"""

import io
import sys

from ocarina.opinionated.cli.selenium.cli_store_singleton import (
    SeleniumCliStoreSingleton as CliStoreSingleton,
)
from ocarina.opinionated.cli.selenium.create_cli_store import (
    create_selenium_linux_cli_store,
)


def main() -> None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", newline="\n")

    CliStoreSingleton().push(create_selenium_linux_cli_store())
    store = CliStoreSingleton()
    print(f"browser={store.get('browser')}")
    print(f"driver_path={store.get('driver_path')}")
    print(f"headless={store.get('headless')}")
    print(f"workers={store.get('workers')}")
    print(f"wait_timeout={store.get('wait_timeout')}")
    print(f"logger={store.get('logger')}")
    print(f"only={store.get('only')}")
    print(f"exclude={store.get('exclude')}")


if __name__ == "__main__":
    main()
