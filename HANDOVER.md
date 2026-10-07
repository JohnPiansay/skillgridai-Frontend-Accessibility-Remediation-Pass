# Handover: Frontend Accessibility Remediation Starter

## Python HTML audit tool

The companion script
[`frontend_accessibility_audit.py`](../frontend_accessibility_audit.py) is a
separate, lightweight command-line checker for static `.html` and `.htm` files.
It is not part of the React app's runtime or its axe-core test suite, and it
does not inspect React `.tsx` or `.jsx` source.

### Architecture

The audit follows a small input-to-report pipeline:

1. **CLI argument parsing:** `build_parser()` defines one or more input paths,
   text or JSON output, and the optional `--fail-on-issues` CI flag.
2. **Input discovery:** `collect_html_files()` validates the supplied paths.
   Directories are searched recursively for `.html` and `.htm` files.
3. **File parsing:** `audit_file()` reads each file as UTF-8 and feeds its
   contents to `AccessibilityParser`, which extends Python's standard-library
   `HTMLParser`. The parser tracks open elements, text, label relationships,
   heading order, and whether the root `<html>` element declares a language.
4. **Finding generation:** Each issue is represented by the immutable `Finding`
   data class, with the source file, line number, rule ID, description, and
   remediation suggestion. The current rule IDs cover missing image alt
   attributes (`IMG001`/`IMG002`), unnamed links or buttons
   (`LINK001`/`BUTTON001`), unlabeled form controls (`FORM001`), skipped heading
   levels (`HEADING001`), and missing document language (`HTML001`).
5. **Reporting and exit status:** `main()` serializes findings as readable text
   or JSON. Without `--fail-on-issues`, findings are informational and the
   command exits successfully; with the flag, any findings produce exit code 1.
   Invalid paths and file read/encoding errors are surfaced as CLI errors.

### Python dependencies and execution

The script has **no third-party dependencies**. It uses only Python standard
library modules: `argparse`, `json`, `sys`, `dataclasses`, `html.parser`,
`pathlib`, and `typing`. Python 3.7 or newer is required for `dataclasses`.
The verification environment used Python 3.14.8.

Examples:

```sh
python ../frontend_accessibility_audit.py path/to/page.html
python ../frontend_accessibility_audit.py path/to/site --format json
python ../frontend_accessibility_audit.py path/to/site --fail-on-issues
```

### Python tool test verification

The tool was exercised with a temporary synthetic HTML file through its CLI
entry point using `--format json --fail-on-issues`. The fixture intentionally
included a missing document language, missing image alternative, unnamed link,
unnamed button, unlabeled form control, and skipped heading level. It also
included a correctly associated label and an ARIA-labelled textarea to check
that those controls were not incorrectly flagged.

**Verified result:** seven findings were emitted, covering six unique rule IDs
(`HTML001`, `IMG001`, `LINK001`, `BUTTON001`, `FORM001`, and `HEADING001`).
The JSON findings had the expected file, line, rule, message, and suggestion
fields, and the CLI returned exit code 1 as requested. This was a synthetic
verification fixture, not an audit of a real website or React application. The
script does not currently include a checked-in automated test suite.

### Python tool limitations

This is a lightweight static HTML checker, not a full accessibility auditor.
It does not render pages, execute JavaScript, inspect React source, calculate
color contrast, or verify keyboard navigation, focus order, or screen-reader
behavior. Automated findings should be followed by browser, keyboard, and
assistive-technology testing. The tool's output cannot be treated as WCAG
conformance certification.

## Project status

This is a new React + TypeScript starter containing an accessible example page
and a small automated accessibility test workflow. It is not a remediation of
an existing production app: no audited React components, audit report, baseline
violation count, GitHub remote, or pull request were provided.

## Architecture

- `index.html` supplies the document shell and declares English as the page
  language.
- `src/main.tsx` mounts the React application.
- `src/App.tsx` provides the example page: skip navigation, labelled navigation,
  semantic sections and heading order, a labelled email form, and live status
  feedback after submission.
- `src/styles.css` implements responsive layout, visible keyboard focus, skip
  link behavior, and the example page's text and control colors.
- `src/App.test.tsx` contains an axe-core scan and an interaction test for
  keyboard focus and form submission.
- `src/test-setup.ts` enables Testing Library's Vitest matchers.
- `vite.config.ts` configures Vite, React, and Vitest with JSDOM.
- `package.json` defines development, test, audit, and production build scripts.

## Dependencies and runtime

- Required runtime: Node.js 20 or later and npm.
- Runtime packages: React and React DOM.
- Development/test packages: Vite, TypeScript, Vitest, JSDOM, axe-core,
  jest-axe, and Testing Library.
- Dependencies are declared in `package.json`. No successful `npm install` was
  performed in the development environment, so a lockfile and resolved package
  versions are not yet recorded.

## Verification and execution summary

| Check | Result | Evidence / next step |
|---|---|---|
| Project manifest and expected source files | Passed | `package.json` parsed and starter files were present. |
| Selected foreground/background contrast | Passed | Ratios were calculated for body text (16.27:1), links (8.81:1), button text (9.42:1), and the focus outline (8.11:1) against white. |
| Python-based file/read checks | Passed | These confirm project files and selected colors only; they do not execute the React app. |
| `npm test` | Not run | Node.js/npm were unavailable in the authoring environment. Run in a Node.js 20+ environment after installing dependencies. |
| `npm run audit:a11y` | Not run | This invokes the axe-core test; no actual axe results or violation count are available yet. |
| `npm run build` | Not run | Run after dependency installation to verify TypeScript and Vite compilation. |
| Browser, keyboard, screen-reader testing | Not run | Perform against the running app before release. |

The test suite is configured to expect zero axe violations for the starter's
rendered example page, but this is a test expectation, **not a measured audit
result**. No before/after count can be claimed until `npm run audit:a11y` runs
successfully and its output is recorded.

## Next steps for the receiving developer

1. Use Node.js 20 or later and run `npm install`.
2. Run `npm test`, `npm run audit:a11y`, and `npm run build`; record versions,
   results, and any axe findings here.
3. Run `npm run dev`, then manually test keyboard-only navigation, visible focus,
   zoom/reflow, and relevant screen readers in a browser.
4. When the target React app and its audit report are available, apply fixes to
   those components, save the audit's baseline and post-fix reports, and open a
   pull request with a per-issue summary.
5. Connect this folder to the intended GitHub repository before publishing or
   creating a pull request.

## Limitations

Automated DOM scans cannot verify every keyboard interaction, focus-management
behavior, screen-reader experience, or contrast state. Verify hover, focus,
disabled, validation-error, and other application-specific states. Treat this
starter and its tests as a foundation, not as WCAG conformance certification.
