# Sprint 1 Week 4 — Features Delivered

## Accomplished

### Authentication System (Backend)
- **JWT login endpoint** (`POST /api/auth/login`) — bcrypt password verification, JWT token set as httponly cookie
- **User info endpoint** (`GET /api/auth/me`) — returns authenticated user with org name
- **Logout endpoint** (`POST /api/auth/logout`) — clears auth cookie
- **Auth dependency** (`get_current_user`) — reusable FastAPI dependency injected into all protected routes
- **24-hour token expiry** — configurable via `JWT_EXPIRE_MINUTES` env var

### Multi-Tenant Data Isolation
- **Org-scoped device queries** — users see only devices belonging to their organisation
- **Org-scoped organisation queries** — users see only their own org
- **Cross-org access returns 404** — no information leakage about other orgs' resources
- **Compound filters** — device lookups check both device ID and org ID

### Frontend Authentication
- **Login page** (`/login`) — email + password form with error handling
- **Protected routes** — `_authenticated` layout redirects to `/login` if not logged in
- **Session persistence** — httponly cookie survives page reload / new tabs
- **Auth-aware header** — shows user name, org name, and logout button when authenticated
- **Cache clearing on logout** — prevents data leakage between user sessions

### Testing
- **7 auth tests** — login success/failure, /me, logout, inactive user
- **7 org isolation tests** — org A vs org B device access, embed URL access, org listing
- **27 total backend tests** — all passing, up from 13 in Sprint 0

### Seed Data
- **Two organisations** — Demo Corp (admin) + Acme IoT (viewer)
- **Three devices** — sensor01, sensor02 (Demo Corp) + sensor03 (Acme IoT)
- **Two users** — admin@democorp.com, viewer@acmeiot.com

## Business Value
- **First demo moment** — screen-record the login → dashboard → logout → different user flow
- **Multi-tenant proof** — investors/clients can see that each org's data is isolated
- **Security foundation** — httponly cookies, bcrypt passwords, org-scoped queries
- **Two-user demo** — show the same platform serving different clients with different data

## Gaps Remaining
- **No refresh tokens** — token expires after 24h, user must re-login (planned: Sprint 5)
- **No password reset** — users cannot recover forgotten passwords (planned: Sprint 5)
- **No user registration** — admin creates users via seed script / future admin panel (planned: Sprint 3)
- **No role-based UI** — admin and viewer roles exist in DB but UI doesn't differentiate (planned: Sprint 3)
- **No HTTPS** — `secure=False` on cookies for localhost dev (planned: Sprint 4 Azure deployment)
- **No admin panel** — device/org/user management still via DB (planned: Sprint 3)
- **No error boundaries** — React errors crash the page
