## 2024-05-23 - Contextual Loading States
**Learning:** Generic full-screen spinners can be disorienting, especially for screen readers. Users might not know if the app is frozen or what it's waiting for.
**Action:** Always wrap loading spinners in a container with `role="status"` and `aria-label`, and provide visible descriptive text (e.g., "Loading intelligence reports...") to reduce uncertainty and improve perceived performance.

## 2026-01-25 - Focus Visibility on Auxiliary Controls
**Learning:** Keyboard users often lose context when navigating inside complex inputs (like password fields with toggles) if the internal buttons lack focus indicators.
**Action:** Ensure auxiliary interactive elements (like "show password" toggles) inside input wrappers have explicit `focus-visible` styles (e.g., `ring-2`) that match the primary input's focus behavior.
