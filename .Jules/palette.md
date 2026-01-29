## 2024-05-23 - Contextual Loading States
**Learning:** Generic full-screen spinners can be disorienting, especially for screen readers. Users might not know if the app is frozen or what it's waiting for.
**Action:** Always wrap loading spinners in a container with `role="status"` and `aria-label`, and provide visible descriptive text (e.g., "Loading intelligence reports...") to reduce uncertainty and improve perceived performance.

## 2024-05-24 - Keyboard Accessibility for Auxiliary Inputs
**Learning:** Interactive elements inside input wrappers (like password toggles) are often overlooked for keyboard focus styles. They need explicit `focus-visible` states to be accessible.
**Action:** Use `focus-visible:ring-2` and `rounded-sm` on auxiliary buttons to ensure they have a visible focus indicator without affecting mouse users.
