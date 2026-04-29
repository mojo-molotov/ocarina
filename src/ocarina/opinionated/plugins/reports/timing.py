"""Context manager logging how long an action took to run."""

import time
from contextlib import contextmanager

from ocarina.infra.drivers_pool import WarmupTimeoutError


def format_elapsed(seconds: float) -> str:
    """Format elapsed time in seconds."""
    secs = int(seconds)
    days, secs = divmod(secs, 86400)
    hours, secs = divmod(secs, 3600)
    minutes, secs = divmod(secs, 60)

    parts = []
    if days:
        parts.append(f"{days} day{'s' if days > 1 else ''}")
    if hours:
        parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
    if minutes:
        parts.append(f"{minutes} minute{'s' if minutes > 1 else ''}")
    if secs or not parts:
        parts.append(f"{secs} second{'s' if secs > 1 else ''}")

    if len(parts) > 1:
        return ", ".join(parts[:-1]) + " and " + parts[-1]
    return parts[0]


@contextmanager
def timing(*, prefix: str = "Duration:", seconds_label: str = "seconds"):
    """Context manager logging how long an action took to run."""
    start = time.perf_counter()
    interrupted = False

    try:
        yield
    except KeyboardInterrupt, WarmupTimeoutError:
        interrupted = True
        raise
    finally:
        if not interrupted:  # pragma: no branch
            end = time.perf_counter()
            elapsed = end - start

            human_readable = format_elapsed(elapsed)

            p = f"{prefix} " if prefix else ""
            print(f"\n{p}{human_readable} ({elapsed:.2f} {seconds_label})")  # noqa: T201
