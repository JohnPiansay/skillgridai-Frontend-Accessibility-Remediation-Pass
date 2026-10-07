# Frontend Accessibility Remediation Starter

A small React + TypeScript project for building accessible UI and checking common
regressions. It is a starter workflow, not a remediation of an existing audited
application.

## Requirements

- Node.js 20 or later
- npm

## Run locally

```sh
npm install
npm run dev
```

## Verification

```sh
npm test
npm run audit:a11y
npm run build
```

The Vitest suite runs axe-core against the rendered React page and checks keyboard
focus and form submission. `audit:a11y` is the focused accessibility test. The
test suite fails if axe reports any violations.

## Architecture

- `src/App.tsx` contains a semantic example page with a skip link, labelled
  navigation, heading hierarchy, labelled form, and live status message.
- `src/styles.css` provides visible keyboard focus, responsive layout, and
  high-contrast foreground/background colors.
- `src/App.test.tsx` checks rendered markup with axe-core and tests keyboard
  navigation and the labelled form interaction.
- `src/test-setup.ts` loads Testing Library's Vitest matchers.
- `vite.config.ts` configures React, Vitest, and the JSDOM test environment.

## Scope and limitations

Automated checks catch only some accessibility failures. Before release, also
test the actual page in a browser using keyboard-only navigation, zoom, and
relevant screen readers. Contrast should be checked for all real design states,
including hover, focus, disabled, and error states. Axe results are the baseline
for this starter and do not describe an external application's prior violations.
