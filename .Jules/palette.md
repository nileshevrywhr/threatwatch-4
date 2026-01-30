## 2024-05-23 - Contextual Loading States
**Learning:** Generic full-screen spinners can be disorienting, especially for screen readers. Users might not know if the app is frozen or what it's waiting for.
**Action:** Always wrap loading spinners in a container with `role="status"` and `aria-label`, and provide visible descriptive text (e.g., "Loading intelligence reports...") to reduce uncertainty and improve perceived performance.

## 2024-05-24 - Keyboard Accessibility for Auxiliary Inputs
**Learning:** Interactive elements inside input wrappers (like password toggles) are often overlooked for keyboard focus styles. They need explicit `focus-visible` states to be accessible.
**Action:** Use `focus-visible:ring-2` and `rounded-sm` on auxiliary buttons to ensure they have a visible focus indicator without affecting mouse users.

## 2026-01-26 - Keyboard Accessible Navigation
**Learning:** Core navigation elements like logos are often implemented as `div`s with `onClick`, making them inaccessible to keyboard users.
**Action:** Always use semantic `<a>` or `<Link>` tags for navigation, and ensure they have visible focus states (`focus-visible`) and `aria-label`s if they lack visible text.