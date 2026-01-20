## 2024-05-23 - Contextual Loading States
**Learning:** Generic full-screen spinners can be disorienting, especially for screen readers. Users might not know if the app is frozen or what it's waiting for.
**Action:** Always wrap loading spinners in a container with `role="status"` and `aria-label`, and provide visible descriptive text (e.g., "Loading intelligence reports...") to reduce uncertainty and improve perceived performance.
