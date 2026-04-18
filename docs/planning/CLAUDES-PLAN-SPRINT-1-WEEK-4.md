# Sprint 1 Week 4 — Authentication

## Context

Week 3 delivered a React frontend that lists devices and embeds Grafana panels — but anyone can see everything. Week 4 adds JWT authentication with httponly cookies, org-scoped data isolation, a login page, and protected routes. The demo moment: log in as user A → see org A's devices; log out, log in as user B → see only org B's.

---

## Key Decisions

**JWT in httponly cookie** (not Authorization header). Backend sets `Set-Cookie: access_token=<jwt>; HttpOnly; SameSite=Lax; Path=/`. Frontend sends `credentials: 'include'` on all fetches. Both on `localhost` (same-site), so `SameSite=Lax` works without HTTPS. `secure=False` for dev; swap in production.

**PyJWT** (not python-jose). Simpler, well-maintained, does one thing. Add `PyJWT>=2.8,<3` to requirements.txt.

**CORS tightened.** `allow_origins=["*"]` → `allow_origins=[settings.FRONTEND_URL]` because wildcard + `allow_credentials=True` is rejected by browsers.

**Org scoping via dependency injection.** Every protected endpoint gets `current_user: User = Depends(get_current_user)`, then filters queries by `current_user.organisation_id`. Cross-org access returns 404 (not 403) to avoid leaking existence.

**Frontend auth flow.** Token is httponly (JS can't read it), so auth state comes from `GET /api/auth/me`. Root route calls `useMe()` on mount → populates Zustand store → `_authenticated` layout route checks store before rendering dashboard routes.

**Route restructuring.** Dashboard routes move under `_authenticated/` pathless layout. URLs don't change (`/dashboard` stays `/dashboard`). Login page at `/login` (public, outside layout guard).

---

## Step 1: Backend Config + Dependency

**`backend/requirements.txt`** — add `PyJWT>=2.8,<3`

**`backend/app/config.py`** — add to Settings:
- `JWT_SECRET_KEY: str = "dev-secret-change-in-production"`
- `JWT_ALGORITHM: str = "HS256"`
- `JWT_EXPIRE_MINUTES: int = 1440` (24h)
- `FRONTEND_URL: str = "http://localhost:5173"`

**`docker-compose.yml`** — add `JWT_SECRET_KEY: ${JWT_SECRET_KEY:-dev-secret-change-in-production}` to backend env

**`.env.example`** — add `JWT_SECRET_KEY`, `FRONTEND_URL`

## Step 2: Auth Module

**Create `backend/app/auth.py`:**
- `COOKIE_NAME = "access_token"`
- `verify_password(plain, hashed) → bool` — `bcrypt.checkpw`
- `create_access_token(user) → str` — JWT with `{sub, email, org_id, role, exp}`
- `decode_access_token(token) → dict` — raises 401 on expired/invalid
- `get_current_user(access_token: Cookie(None), db: Depends) → User` — extract cookie, decode, lookup user, check is_active, return User. Uses `Cookie(default=None)` so missing cookie returns clean 401 (not 422).

## Step 3: Auth Schemas + Router + Registration

**`backend/app/schemas.py`** — add:
- `LoginRequest(email, password)`
- `UserOut(id, email, full_name, organisation_id, role)` — `from_attributes=True`
- `MeResponse(id, email, full_name, organisation_id, organisation_name, role)`

**Create `backend/app/routers/auth.py`:**
- `POST /api/auth/login` — verify creds, check is_active, `create_access_token`, `response.set_cookie(httponly=True, samesite="lax", secure=False, path="/", max_age=86400)`, return `{user: UserOut}`
- `GET /api/auth/me` → `MeResponse` — uses `get_current_user`, includes `organisation.name` via relationship
- `POST /api/auth/logout` — `response.delete_cookie(path="/")`, requires auth

**`backend/app/main.py`:**
- Import `auth` router, `settings`
- `allow_origins=[settings.FRONTEND_URL]` (was `["*"]`)
- `app.include_router(auth.router)`

## Step 4: Org-Scope Existing Endpoints

**`backend/app/routers/devices.py`** — add `current_user: User = Depends(get_current_user)` to all 3 endpoints:
- `list_devices`: filter `.filter(Device.organisation_id == current_user.organisation_id)`
- `get_device`: compound filter `Device.id == device_id, Device.organisation_id == current_user.organisation_id`
- `get_device_embed_urls`: same compound filter + scope dashboards by org

**`backend/app/routers/organisations.py`** — add `get_current_user` dependency:
- `list_organisations`: return only current user's org
- `get_organisation`: 404 if `org_id != current_user.organisation_id`
- `list_org_devices`: same org check

**`backend/app/routers/health.py`** — NO CHANGE (stays public)

## Step 5: Seed Data — Second Org

**`backend/app/seed.py`** — add after Demo Corp block:
- Org: "Acme IoT" (grafana_org_id=2)
- User: `viewer@acmeiot.com` / `viewer123`, role="viewer"
- Device: sensor03 "Temperature Sensor 03" type=temperature
- Dashboard: same template uid, org_id=2

Note: existing "already seeded" check means `docker compose down -v` is needed to re-seed.

## Step 6: Frontend — API + Types + Store

**`frontend/src/lib/api.ts`:**
- Add `credentials: 'include'` to `apiFetch`
- Add `apiPost<T, B>(path, body)` with `method: 'POST'`, `Content-Type: application/json`, `credentials: 'include'`

**`frontend/src/types/api.ts`** — add `User`, `MeResponse`, `LoginRequest`, `LoginResponse`

**`frontend/src/store/authStore.ts`** — replace placeholder:
- State: `user: MeResponse | null`, `isAuthenticated: boolean`, `isLoading: boolean` (starts `true`)
- Actions: `setUser`, `clearUser`, `setLoading`

## Step 7: Frontend — Auth Hooks

**Create `frontend/src/hooks/useAuth.ts`:**
- `useMe()` — `useQuery(['auth','me'])` calling `/api/auth/me`, `retry: false`, `staleTime: 5min`. On success → `setUser`, on error → `clearUser`
- `useLogin()` — `useMutation` calling `apiPost('/api/auth/login', creds)`. On success → `setUser` + `invalidateQueries(['auth','me'])`
- `useLogout()` — `useMutation` calling `apiPost('/api/auth/logout', {})`. On success → `clearUser` + `queryClient.clear()` (wipe cached data between users)

## Step 8: Frontend — Routes + Login Page

**Create `frontend/src/routes/login.tsx`:**
- Email + password form, `useLogin()` mutation, `useNavigate` to `/dashboard` on success
- Error message on failed login
- Redirect to `/dashboard` if already authenticated

**Create `frontend/src/routes/_authenticated.tsx`:**
- `beforeLoad`: read `useAuthStore.getState()` — if `!isLoading && !isAuthenticated`, `throw redirect({to: '/login'})`
- Component: show loading spinner while `isLoading`, else render `<Outlet />`

**Move routes:**
- `routes/dashboard/index.tsx` → `routes/_authenticated/dashboard/index.tsx`
- `routes/dashboard/$deviceId.tsx` → `routes/_authenticated/dashboard/$deviceId.tsx`
- Update import paths (add one more `../` level)
- Delete old `routes/dashboard/` directory

**`frontend/src/routes/__root.tsx`** — add `useMe()` call in component (hydrates auth store on app load)

**`frontend/src/routes/index.tsx`** — no change needed (redirect to `/dashboard` still works, `_authenticated` guard fires before dashboard renders)

## Step 9: Frontend — Layout Update

**`frontend/src/components/Layout.tsx`:**
- Read `user` and `isAuthenticated` from `useAuthStore`
- When authenticated: show `"{full_name} — {organisation_name}"` + Logout button
- When not authenticated: show version string (login page uses Layout)
- Logout handler: `useLogout().mutate()` then `navigate({to: '/login'})`

## Step 10: Backend Tests

**`backend/tests/conftest.py`** — add:
- `_hash(password)` helper
- `seed_user(db, seed_data)` fixture — creates test user in existing org
- `auth_client(client, seed_user)` fixture — logs in via POST, returns client with cookie
- `two_org_seed(db)` fixture — 2 orgs, 2 users, 2 devices, 1 dashboard

**Create `backend/tests/test_auth.py`:**
- `test_login_success` — 200, cookie set, user in response
- `test_login_wrong_password` — 401
- `test_login_nonexistent_user` — 401
- `test_me_authenticated` — 200, email + org_name
- `test_me_unauthenticated` — 401
- `test_logout` — 200, then /me returns 401
- `test_login_inactive_user` — 401

**Create `backend/tests/test_org_isolation.py`:**
- `test_org_a_sees_only_own_devices` — 1 device, correct code
- `test_org_b_sees_only_own_devices` — 1 device, correct code
- `test_org_b_cannot_access_org_a_device` — 404
- `test_org_a_cannot_access_org_b_device` — 404
- `test_org_b_cannot_access_org_a_embed_urls` — 404
- `test_org_a_sees_only_own_organisation` — list returns 1 org
- `test_org_a_cannot_access_org_b_details` — 404

**Update `backend/tests/test_devices.py`** — use `auth_client` fixture instead of `client`

**Update `backend/tests/test_organisations.py`** — use `auth_client` fixture

## Step 11: Documentation

- `docs/SPRINT-1-WEEK4-MANUAL-QA.md` — QA checklist: fresh start, login redirect, Demo Corp login, 2 devices, Acme IoT login, 1 device, logout, cookie persists, DevTools httponly check
- `docs/SPRINT-1-WEEK4-DECISIONS.md` — httponly cookie rationale, PyJWT choice, org scoping strategy, CORS tightening, route restructuring
- `docs/SPRINT-1-WEEK4-FEATURES.md` — features delivered, business value (first demo moment), gaps remaining

---

## Files Created (8)
- `backend/app/auth.py`
- `backend/app/routers/auth.py`
- `backend/tests/test_auth.py`
- `backend/tests/test_org_isolation.py`
- `frontend/src/hooks/useAuth.ts`
- `frontend/src/routes/login.tsx`
- `frontend/src/routes/_authenticated.tsx`
- `docs/SPRINT-1-WEEK4-*.md` (3 files)

## Files Modified (14)
- `backend/requirements.txt` — add PyJWT
- `backend/app/config.py` — JWT + FRONTEND_URL settings
- `backend/app/main.py` — CORS + auth router
- `backend/app/schemas.py` — auth schemas
- `backend/app/routers/devices.py` — auth + org scoping
- `backend/app/routers/organisations.py` — auth + org scoping
- `backend/app/seed.py` — second org/user/device
- `backend/tests/conftest.py` — auth fixtures
- `backend/tests/test_devices.py` — use auth_client
- `backend/tests/test_organisations.py` — use auth_client
- `frontend/src/lib/api.ts` — credentials + apiPost
- `frontend/src/types/api.ts` — auth types
- `frontend/src/store/authStore.ts` — full auth state
- `frontend/src/components/Layout.tsx` — user info + logout
- `frontend/src/routes/__root.tsx` — useMe hydration
- `docker-compose.yml` — JWT_SECRET_KEY env
- `.env.example` — JWT_SECRET_KEY, FRONTEND_URL

## Files Moved (2)
- `frontend/src/routes/dashboard/index.tsx` → `frontend/src/routes/_authenticated/dashboard/index.tsx`
- `frontend/src/routes/dashboard/$deviceId.tsx` → `frontend/src/routes/_authenticated/dashboard/$deviceId.tsx`

---

## Verification

1. `docker compose down -v && docker compose up --build -d` — 7 services, fresh DB
2. `docker compose exec backend python -m app.seed` — seeds 2 orgs, 2 users, 3 devices
3. `http://localhost:5173` → redirects to `/login`
4. Login `admin@democorp.com` / `admin123` → `/dashboard`, header shows "Admin User — Demo Corp"
5. See 2 devices (sensor01, sensor02), click one → Grafana embeds load
6. Click Logout → back to `/login`
7. Login `viewer@acmeiot.com` / `viewer123` → see only sensor03
8. DevTools → Application → Cookies → `access_token` is `HttpOnly` ✓
9. `docker compose exec backend pytest` — all tests pass (auth + isolation + existing)
10. `docker compose exec frontend npm test` — frontend tests pass
