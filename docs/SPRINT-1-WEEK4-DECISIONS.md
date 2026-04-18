# Sprint 1 Week 4 — Technical Decisions

## 1. JWT in HttpOnly Cookie

**Decision:** JWT stored in an httponly cookie, not an Authorization header.

**Why:** HttpOnly cookies cannot be read by JavaScript, preventing XSS from stealing tokens. The browser sends the cookie automatically on every request (with `credentials: 'include'`), so the frontend doesn't need to manage token storage. SameSite=Lax works because frontend (localhost:5173) and backend (localhost:8000) share the same registrable domain (localhost).

**Production:** Set `secure=True` once HTTPS is enabled (Sprint 4 Azure deployment).

## 2. PyJWT Library

**Decision:** PyJWT (not python-jose, not Authlib).

**Why:** PyJWT does one thing — encode/decode JWTs — and does it well. It's the most popular Python JWT library, actively maintained, and has no unnecessary dependencies. python-jose includes extra cryptographic backends we don't need for HS256.

## 3. Org-Scoped Query Pattern

**Decision:** Every protected endpoint injects `current_user` via `Depends(get_current_user)`, then filters all queries by `current_user.organisation_id`. Cross-org access returns 404, not 403.

**Why:** Returning 404 instead of 403 prevents information leakage — an attacker cannot determine whether a resource exists in another org. The dependency injection pattern means org scoping is enforced at the framework level, not by convention. Missing the dependency causes a compile-time import error, not a silent data leak.

## 4. CORS Origin Restriction

**Decision:** Changed `allow_origins=["*"]` to `allow_origins=[settings.FRONTEND_URL]`.

**Why:** The CORS spec requires a specific origin (not wildcard) when `allow_credentials=True`. Browsers reject `Access-Control-Allow-Origin: *` with credentials mode. This change was mandatory for httponly cookies to work cross-origin.

## 5. DB Lookup on Every Request

**Decision:** `get_current_user` queries the database on every authenticated request.

**Why:** If a user is deactivated or their role changes, the change takes effect immediately — not after the JWT expires. At current scale (single-digit users), the extra query is negligible. If it ever matters, add a 60-second in-memory cache.

## 6. TanStack Router Pathless Layout for Auth Guard

**Decision:** Dashboard routes moved under `_authenticated/` pathless layout route. URLs unchanged. Two-layer redirect: `beforeLoad` (sync) + component-level `<Navigate>` (async).

**Why:** TanStack Router's `_` prefix creates a layout boundary without affecting the URL. The `_authenticated.tsx` route guards all child routes with two layers: (1) `beforeLoad` checks the Zustand store synchronously and redirects if auth state is already known, (2) the component checks `isAuthenticated` after the async `useMe()` call resolves — if the user turns out to be unauthenticated, it renders `<Navigate to="/login" />`. The two-layer approach is necessary because `beforeLoad` runs once before the initial `/me` API call completes (while `isLoading` is still `true`). Adding new protected pages just means putting them under `_authenticated/`.

## 7. Auth State via /me Endpoint

**Decision:** Frontend determines auth state by calling `GET /api/auth/me` on app load, not by reading the cookie.

**Why:** The JWT is httponly — JavaScript cannot read it. The `/me` endpoint is the only way for the frontend to know if the user is authenticated and to get user details (name, org). React Query caches this with a 5-minute staleTime to avoid unnecessary requests on every navigation.

## 8. Seed Data for Multi-Org Testing

**Decision:** Added second org (Acme IoT) with viewer user and device to seed script.

**Why:** The sprint demo requires logging in as two different users in different orgs to prove data isolation. One org with one user cannot demonstrate multi-tenancy. The seed script is idempotent (checks for existing orgs before inserting).
