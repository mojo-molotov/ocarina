// Allure Report 3 configuration.
//
// A plain object is exported on purpose (instead of `defineConfig` from the
// "allure" package): the config file is loaded by the Allure CLI, and importing
// "allure" here would require the package to be resolvable from this file. With
// a global install (`bun add -g allure`) that resolution is not guaranteed, so
// avoiding the import keeps the config working in CI and locally alike.
//
// - `output`      : directory the report is generated into (kept as
//                   `allure-report` so the GitHub Pages deploy step is unchanged).
// - `historyPath` : single JSONL file Allure 3 reads and appends to on every
//                   `generate`, replacing Allure 2's manual `history/` folder
//                   copying. CI restores/saves it on the `allure-history` branch
//                   to keep trends across builds.
// - `categories`  : ported from the former `categories.json`. Allure 2's
//                   `matchedStatuses`/`messageRegex` map to `matchers.statuses`/
//                   `matchers.message` (which accepts a RegExp).
export default {
  name: "Ocarina",
  output: "allure-report",
  historyPath: "./history.jsonl",
  plugins: {
    awesome: {
      options: {
        reportName: "Ocarina",
      },
    },
  },
  categories: {
    rules: [
      {
        name: "Test defects",
        matchers: { statuses: ["broken"] },
      },
      {
        name: "Invariant violations",
        matchers: { statuses: ["failed"], message: /.*InvariantViolationError.*/ },
      },
      {
        name: "Assertion errors",
        matchers: { statuses: ["failed"], message: /.*AssertionError.*/ },
      },
      {
        name: "Skipped",
        matchers: { statuses: ["skipped"] },
      },
    ],
  },
};
