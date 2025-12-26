## 2024-05-23 - React Memoization Pitfalls
**Learning:** Defining helper functions (like data transformers) inside a component body creates new function references on every render. Passing the results of these functions to child components (even via `useMemo` if the dependency array includes unstable references) or passing the functions themselves breaks `React.memo` optimization, as props are never referentially equal.
**Action:** Always move pure helper functions *outside* the component definition or wrap them in `useCallback` if they depend on state. Ensure derived data passed to memoized components is stable using `useMemo`.

## 2024-05-23 - Dependency Management & Testing
**Learning:** Attempting to fix test environment issues by installing missing peer dependencies (like `react-router-dom` for tests) can lead to inadvertent `package.json` modifications, violating project constraints.
**Action:** When `npm test` environment is incomplete/broken and `package.json` is frozen, rely on `npm run build` for static analysis and custom scripts (e.g., Playwright) for runtime verification instead of trying to patch the test runner environment.
