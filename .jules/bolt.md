## 2024-05-22 - [React Key Stability]
**Learning:** Generating random IDs (e.g., `Date.now()`) inside a component render function for list keys causes React to lose state and re-mount components on every render. This destroys performance and causes focus loss/input issues.
**Action:** Always use stable IDs from data (e.g., database ID, hash of content, or index if list is static) instead of generating them on the fly.

## 2024-05-23 - [Memoization of Child Components]
**Learning:** Inline arrow functions in parent components break `React.memo` optimization in child components because a new function reference is created on every render.
**Action:** Wrap callbacks in `useCallback` when passing them to memoized child components to ensure referential stability and prevent unnecessary re-renders.
