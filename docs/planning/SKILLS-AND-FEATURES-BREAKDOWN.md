# IoTDash — Skills & Features Breakdown

> **Purpose:** Every tool, every feature you need to learn to build this project solo.
> **How to use:** Work through each tool section. Request walkthroughs for any feature you're not confident in. Features are tagged with the sprint where you first need them.

---

## 1. Python (Language Fundamentals)

You don't need to master all of Python — just the patterns this project uses.

| Feature | What You Need It For | Sprint |
|---------|---------------------|--------|
| Type hints (`str`, `int`, `Optional`, `list[dict]`) | FastAPI requires them for request/response validation | S0 |
| Async/await (`async def`, `await`) | FastAPI async endpoints, async DB queries | S0 |
| Decorators (`@app.get`, `@router.post`) | FastAPI routing, dependency injection | S0 |
| Dataclasses / Pydantic models | Request/response schemas, config objects | S0 |
| Context managers (`with`, `async with`) | Database sessions, HTTP clients | S0 |
| Dictionary unpacking (`**kwargs`) | Passing config, constructing API payloads | S0 |
| List/dict comprehensions | Transforming query results, building responses | S0 |
| Exception handling (`try/except`, custom exceptions) | API error handling, Grafana client errors | S0 |
| Environment variables (`os.environ`, `python-dotenv`) | Config management, secrets | S0 |
| f-strings | URL construction, log messages | S0 |
| `datetime` and `timezone` | Timestamps in DB records, alert scheduling | S2 |
| `hashlib` / `secrets` | Token generation, password reset tokens | S1 |
| Generators (`yield`) | FastAPI dependency injection for DB sessions | S0 |
| `httpx` (async HTTP client) | Calling Grafana API from backend | S2 |

---

## 2. FastAPI

| Feature | What You Need It For | Sprint |
|---------|---------------------|--------|
| **Routing** | | |
| `@app.get`, `@app.post`, `@app.put`, `@app.delete` | CRUD endpoints for all resources | S0 |
| `APIRouter` and `include_router` | Organize routes into modules (`/api/auth`, `/api/devices`, `/admin`) | S0 |
| Path parameters (`/devices/{device_id}`) | Get single resource by ID | S0 |
| Query parameters (`?page=1&limit=20`) | Pagination, filtering | S0 |
| **Request / Response** | | |
| Pydantic `BaseModel` for request bodies | Validate incoming JSON (create device, create alert) | S0 |
| Pydantic `BaseModel` for response schemas | Control what JSON is returned (hide passwords, internal IDs) | S0 |
| `response_model` parameter | Auto-serialize SQLAlchemy objects to JSON | S0 |
| `status_code` parameter | Return 201 on create, 204 on delete | S0 |
| `HTTPException` | Return 404, 403, 400 errors with messages | S0 |
| **Dependency Injection** | | |
| `Depends()` | Inject DB session, current user, auth check into routes | S0 |
| Dependency chains (depends on depends) | `get_current_user` depends on `get_db` | S1 |
| **Middleware** | | |
| CORS middleware (`CORSMiddleware`) | Allow frontend at `localhost:5173` to call API | S1 |
| Custom middleware (request logging) | Log every request with timing | S5 |
| **Auth** | | |
| Cookie-based JWT (`Response.set_cookie`) | Set httponly JWT cookie on login | S1 |
| Reading cookies from request (`Request.cookies`) | Extract JWT on every request | S1 |
| **Other** | | |
| Lifespan events (`@asynccontextmanager`) | Initialize DB pool, Grafana client on startup | S0 |
| Background tasks (`BackgroundTasks`) | Async operations after response (e.g., sync to Grafana) | S2 |
| File structure (multi-module project) | `app/api/`, `app/models/`, `app/schemas/`, `app/services/` | S0 |
| Auto-generated OpenAPI docs (`/docs`) | Testing API without frontend | S0 |

---

## 3. SQLAlchemy + Alembic (ORM + Migrations)

### SQLAlchemy

| Feature | What You Need It For | Sprint |
|---------|---------------------|--------|
| `DeclarativeBase` / `mapped_column` | Define tables as Python classes | S0 |
| Column types (`String`, `Integer`, `Boolean`, `DateTime`, `JSON`) | Schema fields | S0 |
| `ForeignKey` and `relationship()` | Org → Devices, Org → Users, Device → Alerts | S0 |
| `Enum` columns | User roles (`admin`, `viewer`), alert status (`active`, `paused`) | S0 |
| `create_engine` and `sessionmaker` | Connect to PostgreSQL | S0 |
| `Session.query()` or `select()` (2.0 style) | Read data from DB | S0 |
| `.filter()` / `.where()` | Filter by org_id, device_id, user email | S0 |
| `.join()` | Query devices with their org name | S0 |
| `session.add()`, `session.commit()`, `session.refresh()` | Create/update records | S0 |
| `session.delete()` | Delete records | S0 |
| Cascade deletes (`cascade="all, delete-orphan"`) | Delete org → deletes its devices, users, alerts | S3 |
| Unique constraints (`UniqueConstraint`) | No duplicate device codes, no duplicate emails | S0 |
| Index (`Index`) | Speed up queries by org_id, device_code | S0 |
| `server_default` (e.g., `func.now()`) | Auto-set created_at timestamps | S0 |
| Async SQLAlchemy (`AsyncSession`, `create_async_engine`) | Non-blocking DB queries in FastAPI | S0 |

### Alembic

| Feature | What You Need It For | Sprint |
|---------|---------------------|--------|
| `alembic init` | Initialize migration folder | S0 |
| `alembic revision --autogenerate -m "message"` | Generate migration from model changes | S0 |
| `alembic upgrade head` | Apply all pending migrations | S0 |
| `alembic downgrade -1` | Roll back last migration | S0 |
| `env.py` configuration | Point Alembic at your database URL and models | S0 |
| Migration dependencies (linear chain) | Ensure migrations apply in order | S0 |
| Data migrations (not just schema) | Seed default admin user, backfill columns | S3 |

---

## 4. PostgreSQL

| Feature | What You Need It For | Sprint |
|---------|---------------------|--------|
| Basic SQL (`SELECT`, `INSERT`, `UPDATE`, `DELETE`) | Debug data, manual queries, seed scripts | S0 |
| `CREATE TABLE`, `ALTER TABLE` | Understand what Alembic generates | S0 |
| `JOIN` (INNER, LEFT) | Understand ORM-generated queries | S0 |
| `WHERE`, `ORDER BY`, `LIMIT`, `OFFSET` | Pagination, filtering | S0 |
| Indexes (`CREATE INDEX`) | Performance for org_id lookups | S0 |
| Foreign keys and constraints | Referential integrity | S0 |
| `ENUM` types | User roles, alert statuses | S0 |
| `UUID` type | Primary keys | S0 |
| `psql` CLI | Connect to DB, inspect tables, debug | S0 |
| `\dt`, `\d tablename` | List tables, describe schema | S0 |
| `pg_dump` / `pg_restore` | Backups | S5 |
| Connection strings (`postgresql://user:pass@host/db`) | Configure SQLAlchemy, Alembic | S0 |
| JSON/JSONB columns | Store flexible device metadata, alert config | S2 |

---

## 5. JWT + Auth (python-jose / PyJWT + bcrypt)

| Feature | What You Need It For | Sprint |
|---------|---------------------|--------|
| `bcrypt.hashpw()` / `bcrypt.checkpw()` | Hash passwords on user create, verify on login | S1 |
| `jwt.encode()` | Create JWT token with user_id, org_id, role, expiry | S1 |
| `jwt.decode()` | Validate JWT on every request, extract claims | S1 |
| Token expiry (`exp` claim) | Tokens expire after N hours | S1 |
| httponly cookies (vs Authorization header) | Secure token storage, no XSS access to token | S1 |
| `SameSite`, `Secure`, `Path` cookie attributes | Cross-origin cookie behavior, HTTPS enforcement | S1 |
| Password hashing cost factor (rounds) | Balance security vs login speed | S1 |
| Refresh token pattern (optional for MVP) | Extend sessions without re-login | S5 |

---

## 6. React + TypeScript

| Feature | What You Need It For | Sprint |
|---------|---------------------|--------|
| **Core React** | | |
| Functional components | Every UI element | S1 |
| JSX syntax | Rendering HTML in components | S1 |
| Props (passing data to child components) | Reusable components (DeviceCard, AlertRow) | S1 |
| `useState` | Local component state (form inputs, toggles) | S1 |
| `useEffect` | Side effects (subscriptions, manual DOM work — rare with TanStack Query) | S1 |
| `useCallback` / `useMemo` | Prevent unnecessary re-renders (optional optimization) | S3 |
| Conditional rendering (`{condition && <Component/>}`) | Show/hide based on role, loading state | S1 |
| List rendering (`.map()` with `key`) | Render list of devices, alerts | S1 |
| **Routing — TanStack Router** | | |
| `@tanstack/react-router` setup | Type-safe routing for the entire app | S1 |
| `createRootRoute` / `createRoute` | Define route tree | S1 |
| `createRouter` and `<RouterProvider>` | Initialize router, provide to app | S1 |
| File-based routing (`routeTree.gen.ts`) | Auto-generate routes from `routes/` folder structure | S1 |
| `Route` with `component` | Map URL path to a React component | S1 |
| `useParams()` | Read `/devices/$deviceId` from URL (type-safe) | S1 |
| `useNavigate()` | Programmatic redirect (after login, after create) | S1 |
| `useSearch()` | Read type-safe search/query params (`?page=1&filter=active`) | S2 |
| `<Outlet>` and layout routes | Layout wrapper (sidebar + content area) | S1 |
| `beforeLoad` guard | Auth check — redirect to `/login` if not authenticated | S1 |
| `loader` functions | Pre-fetch data before route renders (integrates with TanStack Query) | S1 |
| Path params with `$` prefix | `/devices/$deviceId` instead of `:deviceId` | S1 |
| `<Link>` component | Type-safe navigation links (autocompletes valid routes) | S1 |
| `NotFoundRoute` | Custom 404 page | S1 |
| **Data Fetching — TanStack Query** | | |
| `@tanstack/react-query` setup | Server state management for the entire app | S1 |
| `QueryClientProvider` and `QueryClient` | Initialize query client, provide to app | S1 |
| `useQuery` | Fetch data (GET requests — devices, alerts, orgs) | S1 |
| `queryKey` arrays | Cache identity (`["devices"]`, `["devices", deviceId]`) | S1 |
| `queryFn` | The actual fetch function that calls your API | S1 |
| `isLoading` / `isError` / `data` | Handle loading, error, success states declaratively | S1 |
| `useMutation` | Write data (POST/PUT/DELETE — create alert, login) | S1 |
| `onSuccess` / `onError` callbacks | Navigate after create, show error toast | S1 |
| `queryClient.invalidateQueries` | Refetch data after mutation (create device → refresh list) | S1 |
| `staleTime` / `gcTime` | Control how long data stays fresh / in cache | S2 |
| `enabled` option | Conditional fetching (only fetch if user is logged in) | S1 |
| `select` option | Transform/filter data from cache | S2 |
| `credentials: "include"` in fetch wrapper | Send httponly cookies with cross-origin requests | S1 |
| React Query Devtools (`@tanstack/react-query-devtools`) | Debug queries, cache state during development | S1 |
| **State — Zustand** | | |
| `create` store | Define a store (`useAuthStore`, `useUIStore`) | S1 |
| State + actions in one object | `{ user: null, login: (u) => set({ user: u }) }` | S1 |
| `useStore(selector)` | Select specific state slice to prevent re-renders | S1 |
| `persist` middleware | Persist auth state to localStorage (survive refresh) | S1 |
| `devtools` middleware | Debug state changes with Redux DevTools | S1 |
| Multiple stores (not one global) | `useAuthStore` for auth, `useUIStore` for sidebar/theme | S3 |
| **Forms** | | |
| Controlled inputs (`value` + `onChange`) | Login form, alert creation form, admin forms | S1 |
| Form submission (`onSubmit`, `preventDefault`) | POST to API via `useMutation` on form submit | S1 |
| Form validation (client-side) | Required fields, email format, number ranges | S2 |
| Select dropdowns | Pick device, pick metric, pick condition | S2 |
| **iframe Embedding** | | |
| `<iframe src={url}>` | Embed Grafana panels | S1 |
| `sandbox` attribute | Security restrictions on embedded content | S1 |
| iframe sizing (responsive) | Grafana panels fit the page layout | S1 |
| **TypeScript** | | |
| Interfaces for API responses | `interface Device { id: string; name: string; ... }` | S1 |
| Type annotations on props | `function DeviceCard({ device }: { device: Device })` | S1 |
| Generic types for API wrapper | `async function api<T>(url): Promise<T>` used in `queryFn` | S1 |
| `enum` or union types | `type Role = "admin" \| "viewer"` | S1 |
| `tsconfig.json` basics | Compiler settings, path aliases | S1 |
| Route type safety | TanStack Router infers param/search types from route definitions | S1 |

---

## 7. Tailwind CSS

| Feature | What You Need It For | Sprint |
|---------|---------------------|--------|
| Utility classes (`flex`, `p-4`, `text-lg`, `bg-white`) | All styling | S1 |
| Flexbox (`flex`, `justify-between`, `items-center`, `gap-4`) | Layout: sidebar + content, header, card grids | S1 |
| Grid (`grid`, `grid-cols-2`, `gap-4`) | Device card grid, dashboard layout | S1 |
| Responsive (`sm:`, `md:`, `lg:` prefixes) | Mobile-friendly layouts | S1 |
| Colors (`text-gray-700`, `bg-blue-500`, `border-red-300`) | Theming, status indicators | S1 |
| Spacing (`m-`, `p-`, `space-y-`, `gap-`) | Margins, padding, gaps | S1 |
| Typography (`text-sm`, `font-bold`, `leading-relaxed`) | Headings, body text, labels | S1 |
| Borders (`border`, `rounded-lg`, `shadow-md`) | Cards, inputs, buttons | S1 |
| Hover/focus states (`hover:bg-blue-600`, `focus:ring-2`) | Interactive buttons, inputs | S1 |
| `@apply` in custom CSS (use sparingly) | Reusable button/input styles | S1 |
| `tailwind.config.js` | Custom colors, fonts if needed | S1 |

---

## 8. Vite

| Feature | What You Need It For | Sprint |
|---------|---------------------|--------|
| `npm create vite@latest` | Scaffold React + TypeScript project | S1 |
| `npm run dev` (dev server with HMR) | Local development with hot reload | S1 |
| `npm run build` (production build) | Build static files for Docker/deployment | S4 |
| `vite.config.ts` proxy (`server.proxy`) | Proxy `/api` calls to FastAPI during local dev | S1 |
| `@tanstack/router-plugin/vite` | Vite plugin for TanStack Router file-based route generation | S1 |
| Environment variables (`import.meta.env.VITE_*`) | API base URL per environment | S4 |
| Build output (`dist/` folder) | Serve from Nginx or FastAPI static files | S4 |

---

## 9. Docker + Docker Compose

### Dockerfile

| Feature | What You Need It For | Sprint |
|---------|---------------------|--------|
| `FROM` (base image selection) | `python:3.12-slim` for backend, `node:20-alpine` for frontend build | S0 |
| `WORKDIR` | Set working directory inside container | S0 |
| `COPY` and `.dockerignore` | Copy source code, exclude `node_modules`, `.venv`, `.git` | S0 |
| `RUN` (install dependencies) | `pip install`, `npm install` | S0 |
| `EXPOSE` | Document which port the app listens on | S0 |
| `CMD` / `ENTRYPOINT` | Start command (`uvicorn app.main:app`) | S0 |
| Multi-stage builds | Build frontend in Node stage, serve from Nginx stage | S4 |
| Layer caching (order of COPY) | Copy `requirements.txt` before source code for faster rebuilds | S0 |
| `HEALTHCHECK` | Container health monitoring | S5 |

### Docker Compose

| Feature | What You Need It For | Sprint |
|---------|---------------------|--------|
| `services` definition | Define all 7+ services (backend, frontend, postgres, grafana, emqx, telegraf, influxdb) | S0 |
| `image` vs `build` | Use pre-built images (postgres, grafana) vs build your own (backend) | S0 |
| `ports` mapping | Expose services to host (`8000:8000`, `3000:3000`) | S0 |
| `environment` variables | Pass config to containers | S0 |
| `env_file` | Load `.env` file into container | S0 |
| `volumes` (named volumes) | Persist postgres data, influxdb data across restarts | S0 |
| `volumes` (bind mounts) | Mount source code for live reload during dev | S0 |
| `networks` | All services on same network (`iot_net`) | S0 |
| `depends_on` with `condition: service_healthy` | Start backend after postgres is ready | S0 |
| `healthcheck` | Define health checks for services | S0 |
| `restart: unless-stopped` | Auto-restart crashed services | S0 |
| `profiles` | Optional services (e.g., mailhog only in dev profile) | S2 |
| `docker compose up -d` | Run in background | S0 |
| `docker compose logs -f service_name` | Debug a specific service | S0 |
| `docker compose down -v` | Clean restart (wipe volumes) | S0 |

---

## 10. Grafana

| Feature | What You Need It For | Sprint |
|---------|---------------------|--------|
| **Basics** | | |
| Grafana UI navigation | Understand what you're automating via API | S0 |
| Datasource configuration (InfluxDB/Flux) | Connect Grafana to time-series data | S0 |
| Dashboard creation (panels, queries) | Build template dashboards for devices | S0 |
| Panel types (time series, gauge, stat, table) | Different visualizations for device metrics | S0 |
| Variables in dashboards (`$device_id`) | One dashboard template, filtered per device | S0 |
| **Multi-Org** | | |
| Organisation concept | One org per client for isolation | S0 |
| Create org via API (`POST /api/orgs`) | Auto-create on client onboarding | S3 |
| Switch org context (`X-Grafana-Org-Id` header) | All API calls scoped to specific org | S3 |
| Add datasource to org via API | Each org needs its own InfluxDB datasource | S3 |
| Import dashboard to org via API (`POST /api/dashboards/db`) | Deploy template dashboard per org | S3 |
| **Embedding** | | |
| `GF_SECURITY_ALLOW_EMBEDDING=true` | Allow iframes | S0 |
| `GF_AUTH_ANONYMOUS_ENABLED=true` | No login required for embedded views | S0 |
| `GF_AUTH_ANONYMOUS_ORG_NAME` | Set which org anonymous users see | S0 |
| Panel embed URL format (`/d-solo/{uid}/{slug}?orgId=X&panelId=Y`) | Construct URLs from backend | S0 |
| `GF_SECURITY_COOKIE_SAMESITE=none` | Cross-origin iframe cookies | S1 |
| **Service Account** | | |
| Create service account (admin level) | Backend authenticates to Grafana API | S2 |
| Generate service account token | Bearer token for API calls | S2 |
| **Alerting API** | | |
| Alert rule concept (query → reduce → threshold) | Understand the data model before API calls | S2 |
| `POST /api/v1/provisioning/alert-rules` | Create alert from web app | S2 |
| `PUT /api/v1/provisioning/alert-rules/{uid}` | Update alert | S2 |
| `DELETE /api/v1/provisioning/alert-rules/{uid}` | Delete alert | S2 |
| Alert rule `data[]` array (refId A=query, B=reduce, C=threshold) | Build the correct alert payload | S2 |
| Contact points API (`POST /api/v1/provisioning/contact-points`) | Set email destination per alert | S2 |
| Notification policies API | Route alerts to correct contact point | S2 |
| Folders API (`POST /api/folders`) | Alerts must belong to a folder | S2 |
| `X-Disable-Provenance` header | Allow API-created alerts to be modified | S2 |
| **SMTP** | | |
| `GF_SMTP_ENABLED`, `GF_SMTP_HOST`, `GF_SMTP_USER`, etc. | Grafana sends alert emails | S2 |
| Mailhog for local SMTP testing | Catch emails locally without real email service | S2 |
| **Provisioning (file-based)** | | |
| `provisioning/datasources/*.yaml` | Pre-configure datasources on startup | S0 |
| `provisioning/dashboards/*.yaml` + JSON files | Pre-load dashboards on startup | S0 |

---

## 11. InfluxDB

| Feature | What You Need It For | Sprint |
|---------|---------------------|--------|
| Buckets (create, configure retention) | Store time-series data, set data expiry | S0 |
| Organisations and tokens | Auth for Telegraf and Grafana | S0 |
| Flux query language (basics) | Grafana queries, alert queries | S0 |
| `from(bucket:)` | Select data source | S0 |
| `\|> range(start:)` | Time window filter | S0 |
| `\|> filter(fn: (r) => ...)` | Filter by measurement, device_id, field | S0 |
| `\|> aggregateWindow()` | Downsample data (mean per 5m, per 1h) | S0 |
| `\|> last()` / `\|> mean()` | Get latest or average value | S0 |
| Measurements, tags, fields (data model) | Understand how Telegraf writes data | S0 |
| Tag vs field (when to use which) | Tags = indexed (device_id), fields = values (temperature) | S0 |
| Retention policies | Auto-delete old data (30d, 90d, 1y) | S5 |
| InfluxDB UI (`localhost:8086`) | Browse data, test queries manually | S0 |
| `influx` CLI | Backup, restore, manage buckets from terminal | S5 |
| Token management | Generate read-only tokens per Grafana org | S3 |

---

## 12. EMQX (MQTT Broker)

| Feature | What You Need It For | Sprint |
|---------|---------------------|--------|
| EMQX dashboard UI (`localhost:18083`) | Monitor connections, topics, messages | S0 |
| MQTT listener configuration (port 1883) | Devices connect here | S0 |
| Topic structure (`device_id/from/message`) | Understand topic hierarchy | S0 |
| Wildcard subscriptions (`+` single level, `#` multi level) | Telegraf subscribes to `+/from/+` | S0 |
| QoS levels (0, 1, 2) | Choose reliability vs throughput | S0 |
| Anonymous access (default, dev only) | Devices connect without credentials in dev | S0 |
| **Authentication** | | |
| Built-in database auth | Username/password per device | S5 |
| ACLs (Access Control Lists) | Device X can only publish to `X/from/#` | S5 |
| Auth via HTTP API (external auth backend) | Your backend validates MQTT credentials | S5 |
| **Monitoring** | | |
| Client list (connected devices) | See which devices are online | S3 |
| Topic metrics | Messages per second, per topic | S5 |
| REST API (`/api/v5/clients`) | Query connected clients from your backend | S3 |

---

## 13. Telegraf

| Feature | What You Need It For | Sprint |
|---------|---------------------|--------|
| `telegraf.conf` structure | `[agent]`, `[[inputs.*]]`, `[[outputs.*]]` sections | S0 |
| `[[inputs.mqtt_consumer]]` | Subscribe to MQTT topics from EMQX | S0 |
| `topics` array | Which MQTT topics to consume (`+/from/+`) | S0 |
| `topic_tag` | Extract parts of topic as InfluxDB tags | S0 |
| `data_format = "json"` | Parse JSON payloads from devices | S0 |
| `json_string_fields` | Which JSON fields to treat as strings vs numbers | S0 |
| `tag_keys` | Which JSON fields become InfluxDB tags | S0 |
| `[[outputs.influxdb_v2]]` | Write to InfluxDB | S0 |
| `name_override` | Control the InfluxDB measurement name | S0 |
| Topic parsing (`[[inputs.mqtt_consumer.topic_parsing]]`) | Extract device_id, direction, message_type from topic path | S0 |
| Reload config (`docker compose restart telegraf`) | Apply config changes | S0 |
| Debug logging (`[agent] debug = true`) | Troubleshoot data pipeline issues | S0 |

---

## 14. MQTT Protocol (for device communication)

| Feature | What You Need It For | Sprint |
|---------|---------------------|--------|
| Publish/subscribe model | Core concept — devices publish, Telegraf subscribes | S0 |
| Topics and topic hierarchy | `device_id/from/message`, `device_id/to/command` | S0 |
| QoS 0 (fire and forget) | Telemetry data (acceptable to lose occasional message) | S0 |
| QoS 1 (at least once) | Commands to devices (must be delivered) | S0 |
| JSON payloads | `{"temperature": 22.5, "humidity": 45}` | S0 |
| `paho-mqtt` Python client | Fake device simulator, backend device commands | S0 |
| `client.connect()`, `client.publish()`, `client.loop_start()` | Basic MQTT operations in Python | S0 |
| Last Will and Testament (LWT) | Auto-publish "device offline" on disconnect | S5 |
| Retained messages | Device publishes status; new subscribers get latest | S5 |

---

## 15. Git

| Feature | What You Need It For | Sprint |
|---------|---------------------|--------|
| `git init`, `git add`, `git commit` | Basic version control | S0 |
| `.gitignore` | Exclude `.env`, `node_modules`, `__pycache__`, volumes | S0 |
| Branching (`git checkout -b feature/name`) | Work on features without breaking main | S0 |
| Merging (`git merge`) | Bring feature branch into main | S0 |
| `git log`, `git diff`, `git status` | Understand what changed | S0 |
| Conventional commits (`feat:`, `fix:`, `chore:`) | Consistent commit messages | S0 |
| `.gitkeep` in empty directories | Track empty folders (frontend/, infra/) | S0 |
| `git stash` | Temporarily save uncommitted changes | S0 |
| `git remote add origin` + `git push` | Push to GitHub | S4 |
| Pull requests (GitHub UI or `gh` CLI) | Code review workflow (even solo — good habit) | S4 |
| Branch protection rules | Require CI to pass before merge to main | S4 |

---

## 16. GitHub Actions (CI/CD)

| Feature | What You Need It For | Sprint |
|---------|---------------------|--------|
| Workflow files (`.github/workflows/*.yml`) | Define CI/CD pipelines | S4 |
| `on: push`, `on: pull_request` triggers | When to run pipelines | S4 |
| `jobs` and `steps` | Structure of a pipeline | S4 |
| `uses: actions/checkout@v4` | Check out code in CI | S4 |
| `uses: actions/setup-python@v5` | Install Python in CI | S4 |
| `uses: actions/setup-node@v4` | Install Node in CI | S4 |
| `run:` steps | Execute shell commands (lint, test, build) | S4 |
| Secrets (`${{ secrets.AZURE_CREDENTIALS }}`) | Store Azure credentials, API keys | S4 |
| Environment variables in workflows | Pass config to build/deploy steps | S4 |
| `services:` (service containers) | Run postgres in CI for integration tests | S4 |
| Docker build + push to ACR | Build backend/frontend images, push to Azure Container Registry | S4 |
| `az containerapp update` | Deploy new image to Azure Container Apps | S4 |
| Job dependencies (`needs: [build]`) | Deploy only after tests pass | S4 |
| Manual trigger (`on: workflow_dispatch`) | Manual deployment trigger | S4 |
| Caching (`actions/cache`) | Speed up pip/npm installs | S4 |

---

## 17. Terraform

| Feature | What You Need It For | Sprint |
|---------|---------------------|--------|
| **Basics** | | |
| HCL syntax (blocks, attributes, strings) | Write `.tf` files | S4 |
| `terraform init` | Initialize providers, download plugins | S4 |
| `terraform plan` | Preview changes before applying | S4 |
| `terraform apply` | Create/update infrastructure | S4 |
| `terraform destroy` | Tear down infrastructure | S4 |
| **Configuration** | | |
| `provider "azurerm"` | Configure Azure provider | S4 |
| `resource` blocks | Define Azure resources | S4 |
| `variable` blocks and `terraform.tfvars` | Parameterize config (region, SKU, names) | S4 |
| `output` blocks | Export values (URLs, connection strings) | S4 |
| `locals` | Computed values, naming conventions | S4 |
| **State** | | |
| `terraform.tfstate` | Tracks what exists in Azure | S4 |
| Remote state backend (Azure Storage) | Share state across CI/CD, don't commit to git | S4 |
| `terraform state list` / `terraform state show` | Inspect managed resources | S4 |
| **Modules** | | |
| Module structure (`modules/client-stack/`) | Reusable components for single-tenant deployment | S4 |
| `module` block and `source` | Reference modules | S4 |
| **Azure Resources You'll Define** | | |
| `azurerm_resource_group` | Logical container for all resources | S4 |
| `azurerm_container_registry` | Store Docker images | S4 |
| `azurerm_container_app_environment` | Shared environment for Container Apps | S4 |
| `azurerm_container_app` | Deploy each service (backend, grafana, emqx, etc.) | S4 |
| `azurerm_key_vault` + `azurerm_key_vault_secret` | Store secrets securely | S4 |
| `azurerm_storage_account` + file shares | Persistent storage for databases | S4 |
| `azurerm_postgresql_flexible_server` | Managed PostgreSQL (instead of container) | S4 |

---

## 18. Azure (Cloud Concepts)

| Feature | What You Need It For | Sprint |
|---------|---------------------|--------|
| **Core** | | |
| Resource Groups | Organize all project resources | S4 |
| Azure CLI (`az login`, `az account set`) | Authenticate, manage resources from terminal | S4 |
| Subscriptions and billing | Understand cost structure | S4 |
| **Container Apps** | | |
| Container Apps Environment | Shared VNET, logging for all apps | S4 |
| Container App (revision-based deployment) | Deploy backend, frontend, grafana | S4 |
| Ingress (HTTP, TCP) | Expose services externally (HTTP for web, TCP for MQTT) | S4 |
| Scaling rules (HTTP, KEDA) | Auto-scale based on requests/connections | S4 |
| Custom domains + managed TLS | HTTPS on your domain | S4 |
| Environment variables and secrets | Config injection | S4 |
| Volume mounts (Azure Files) | Persistent data for databases | S4 |
| `az containerapp logs show` | Debug deployed services | S4 |
| **Supporting Services** | | |
| Azure Container Registry (ACR) | Store Docker images | S4 |
| Azure Key Vault | Manage secrets (DB passwords, API tokens) | S4 |
| Azure Files | Persistent file storage for containers | S4 |
| Azure Database for PostgreSQL (Flexible Server) | Managed PostgreSQL with backups, scaling | S4 |
| Azure Log Analytics | Centralized logging and monitoring | S5 |
| Azure Monitor alerts | Infra-level alerting (CPU, memory, errors) | S5 |
| **Networking** | | |
| VNET basics | Container Apps private networking | S4 |
| DNS zones | Custom domain management | S4 |

---

## 19. Testing

| Feature | What You Need It For | Sprint |
|---------|---------------------|--------|
| **Python / Backend** | | |
| `pytest` basics (test functions, assertions) | Test API endpoints, services | S0 |
| `pytest` fixtures (`@pytest.fixture`) | Set up test DB, test client | S0 |
| FastAPI `TestClient` | HTTP-level endpoint testing | S0 |
| Test database (separate from dev DB) | Isolated test data | S0 |
| Mocking (`unittest.mock`, `pytest-mock`) | Mock Grafana API, email sending | S2 |
| `pytest-asyncio` | Test async functions | S0 |
| **Frontend** | | |
| Vitest basics | Unit test React components | S3 |
| React Testing Library (`render`, `screen`, `fireEvent`) | Test UI interactions | S3 |
| Testing with TanStack Query (`QueryClientProvider` wrapper) | Wrap components in test QueryClient for isolated cache | S3 |
| Testing with Zustand (store reset between tests) | Reset store state to avoid test pollution | S3 |
| **Other** | | |
| `httpx` for API integration tests | Test real API with test database | S3 |
| Load testing with `locust` or `k6` | Simulate 100 devices, verify performance | S5 |

---

## 20. Email (SMTP + SendGrid)

| Feature | What You Need It For | Sprint |
|---------|---------------------|--------|
| SMTP protocol concept | How email sending works | S2 |
| Mailhog (local SMTP server) | Catch and view emails locally | S2 |
| Grafana SMTP configuration | Grafana sends alert emails directly | S2 |
| SendGrid account setup | Production email sending | S4 |
| SendGrid API key | Authenticate email sends | S4 |
| SPF, DKIM DNS records | Email deliverability (not landing in spam) | S4 |
| SendGrid Python SDK (or SMTP relay) | Send emails from backend (password reset, notifications) | S4 |

---

## 21. Security Essentials

| Feature | What You Need It For | Sprint |
|---------|---------------------|--------|
| HTTPS (TLS) | Encrypt all traffic | S4 |
| CORS configuration | Control which origins can call your API | S1 |
| httponly cookies | Prevent XSS from accessing auth tokens | S1 |
| Input validation (Pydantic) | Reject malformed requests before they hit DB | S0 |
| SQL injection prevention (ORM) | SQLAlchemy parameterizes queries automatically | S0 |
| Rate limiting (`slowapi`) | Prevent brute-force login attempts | S5 |
| Content Security Policy (CSP) header | Control what can be embedded/loaded | S5 |
| HSTS header | Force HTTPS | S5 |
| Secrets management (env vars, never in code) | Keep credentials out of git | S0 |
| `.env` + `.env.example` pattern | Document required env vars without committing values | S0 |

---

## 22. DevOps / Shell Skills

| Feature | What You Need It For | Sprint |
|---------|---------------------|--------|
| Terminal navigation (`cd`, `ls`, `pwd`, `mkdir`) | Basic file operations | S0 |
| Environment variables (`export`, `echo $VAR`) | Set and read config values | S0 |
| `curl` for API testing | Quick API calls without Postman | S0 |
| `docker logs`, `docker exec -it container bash` | Debug containers | S0 |
| `pip install`, `pip freeze` | Python dependency management | S0 |
| `npm install`, `npm run` | Node dependency management, scripts | S1 |
| Process management (`ps`, `kill`) | Find and stop stuck processes | S0 |
| SSH basics | Access Azure VMs if needed | S4 |
| `jq` for JSON processing | Parse API responses in terminal | S0 |

---

## Quick Reference: What to Learn Per Sprint

| Sprint | Key New Tools/Skills |
|--------|---------------------|
| **S0** (Wk 1-2) | Python, FastAPI, SQLAlchemy, Alembic, PostgreSQL, Docker, Docker Compose, Telegraf config, InfluxDB Flux, Grafana UI, MQTT basics, Git, pytest |
| **S1** (Wk 3-4) | React, TypeScript, Tailwind, Vite, TanStack Router, TanStack Query, Zustand, JWT, bcrypt, CORS, iframe embedding |
| **S2** (Wk 5-6) | Grafana Alerting API, Grafana Service Accounts, httpx (async HTTP), Mailhog, SMTP concepts, form validation |
| **S3** (Wk 7-8) | Grafana Multi-Org API, Grafana dashboard provisioning API, EMQX REST API, admin patterns, audit logging |
| **S4** (Wk 9-10) | Terraform, Azure CLI, Azure Container Apps, ACR, Key Vault, GitHub Actions, SendGrid, DNS |
| **S5** (Wk 11-12) | EMQX auth/ACL, rate limiting, security headers, monitoring, backups, load testing |

---

## Learning Priority Order

If you're short on time, learn these first — they unblock the most work:

1. **FastAPI** (routes, Pydantic, dependency injection) — the backbone of your backend
2. **SQLAlchemy** (models, queries, sessions) — every endpoint touches the DB
3. **Docker Compose** (services, networks, volumes) — your entire dev environment
4. **React + TanStack Router + TanStack Query + Zustand** (components, type-safe routing, declarative data fetching, state) — the entire frontend
5. **Grafana HTTP API** (orgs, dashboards, alerting) — the integration that makes the product unique
6. **Terraform + Azure** (resources, state, Container Apps) — deployment

Everything else you can pick up along the way as you hit each sprint.

---

*Companion to [`TECH-LEAD-PLAYBOOK.md`](./TECH-LEAD-PLAYBOOK.md) — see sprint details for how each skill maps to deliverables.*
