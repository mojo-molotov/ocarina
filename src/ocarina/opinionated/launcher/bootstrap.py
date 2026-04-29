"""Generic bootstrap for running a test cycle, post-run plugins, and reporting."""

from concurrent.futures.thread import ThreadPoolExecutor
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from ocarina.custom_types.effect import Effect
    from ocarina.custom_types.oc_test_layers import TestCycleResults
    from ocarina.dsl.testing.oc_test_cycle import TestCycle
    from ocarina.ports.ilogger import ILogger


def run_plugins(*plugins: Effect, exceptions_logger: ILogger) -> None:
    """Run plugins sequentially (one plugin) or in parallel (multiple plugins).

    Exceptions are caught and logged via `exceptions_logger` so that a failing
    plugin never interrupts the others.

    Args:
        *plugins: Side-effectful callables to execute.
        exceptions_logger: Logger used to report plugin failures.

    """
    if not plugins:  # pragma: no cover
        return

    def _run_plugin(plugin: Effect, exceptions_logger: ILogger) -> None:
        try:
            plugin()
        except Exception as exc:
            exceptions_logger.exception("The plugin failed.", exc=exc)

    if len(plugins) == 1:
        _run_plugin(plugins[0], exceptions_logger)
        return

    with ThreadPoolExecutor(max_workers=len(plugins)) as executor:
        futures = [
            executor.submit(_run_plugin, plugin, exceptions_logger)
            for plugin in plugins
        ]
        for f in futures:
            f.result()


def bootstrap[T](
    *,
    test_cycle: TestCycle[T],
    run_plugins: Callable[[TestCycleResults], None],
    post_exec: Callable[[TestCycleResults], None] | None = None,
    saturate_workers: bool = True,
) -> None:
    """Run all tests, execute post-run plugins, and optionally print the report.

    Args:
        test_cycle: The test cycle to run.
        run_plugins: Called with the results once the cycle completes. Receives
            ``results`` as its only argument, which allows plugins that depend on
            the results (e.g. JSON export) to be declared at the call-site without
            forward-referencing an not-yet-existing variable.
        post_exec: Post execution callback, taking results.
        saturate_workers: Duplicate tests to reach max_workers. Default: True.

    Example:
        bootstrap(
            post_exec=lambda results: pretty_print_results(results),
            test_cycle=TestCycle(campaigns=[...]),
            run_plugins=lambda results: run_plugins(
                lambda: generate_docx_proof(
                    logs_root=get_default_log_dir(),
                    logger=logger,
                    output_root=Path.cwd() / "tests_docx_output",
                ),
                lambda: generate_json_results(
                    results=results,
                    output_dir=Path.cwd() / "tests_json_output",
                    logger=logger,
                ),
                exceptions_logger=PrintLogger()
                    .set_prefix(
                        lambda: concat_metadata(
                            format_utc_date_metadata_str,
                            format_current_thread_metadata_str,
                        )
                    )
                    .set_domain_taxonomy(("Post-execution plugins",)),
            ),
        )

    """
    results = test_cycle.run_all(saturate_workers=saturate_workers)
    run_plugins(results)
    if post_exec:
        post_exec(results)
