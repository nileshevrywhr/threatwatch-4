## 2024-05-23 - Contextual Loading States
**Learning:** Generic full-screen spinners can be disorienting, especially for screen readers. Users might not know if the app is frozen or what it's waiting for.
**Action:** Always wrap loading spinners in a container with `role="status"` and `aria-label`, and provide visible descriptive text (e.g., "Loading intelligence reports...") to reduce uncertainty and improve perceived performance.
# UX and Accessibility Learnings

## Field Mapping and API Consistency
- **Consistency is Key**: When a backend expects query parameters, ensure the frontend uses a centralized API client that handles this pattern. Discrepancies between request bodies and query parameters lead to "Field required" errors.
- **Database Schema Alignment**: Always verify frontend field names (e.g., `term`) against database columns (e.g., `query_text`). Use a mapping layer in the API client to maintain UI simplicity while ensuring database compatibility.
- **ID Naming**: Standardize on `id` when the database uses it, especially if the frontend has previously used more descriptive but inconsistent names like `monitor_id`.

## UI Feedback
- **Success/Error States**: Consistently use `Alert` components with `CheckCircle` or `AlertTriangle` icons to provide clear visual feedback to users after form submissions.
