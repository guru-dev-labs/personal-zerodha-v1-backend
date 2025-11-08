# Revised Backend Setup Plan: User-Facing Zerodha API Tool

The objective is to build a backend that allows users to log in with their Zerodha accounts, with a middleware layer to manage API interactions and optimize calls. The current workspace directory `/Users/deevanshu/My Files/Development/Personal Zerodha/personal-zerodha-v1-backend` is considered the root of the backend project.

## Phase 1: Project Setup and Core Authentication

- [ ] Create the `app` directory within the current workspace.
- [ ] Set up a Python virtual environment within the current workspace.
- [ ] Install core dependencies: `fastapi`, `uvicorn`, `kiteconnect`, `python-dotenv`, `pydantic`.
- [ ] Create a `config.py` for environment variables and settings within `app`.
- [ ] Implement a `main.py` FastAPI application with:
    - **Login Endpoint:** Redirects users to Zerodha's login page.
    - **Callback Endpoint:** Handles the Zerodha redirect, exchanges the request token for an access token, and stores it securely (e.g., in a session or a temporary database for the initial phase).
- [ ] Create a `zerodha_client.py` to encapsulate `kiteconnect` interactions within `app`.
- [ ] Create a `.env.example` and `.env` file for `KITE_API_KEY`, `KITE_API_SECRET`, and potentially a `SECRET_KEY` for session management within the current workspace.

## Phase 2: Middleware and API Interaction Layer

- [ ] Design a middleware concept within FastAPI to:
    - Validate user sessions/authentication.
    - Inject the `Kite` client instance (with the user's access token) into request context.
    - **Consider API Call Optimization:** Implement basic caching or data storage mechanisms (e.g., in-memory cache, simple JSON file) for frequently accessed, less dynamic data to reduce redundant Zerodha API calls. This will be a placeholder for now, to be expanded later.
- [ ] Create `models.py` for Pydantic models to define request/response data structures within `app`.

## Phase 3: Initial User-Facing Endpoints

- [ ] Add initial API endpoints to `app/main.py` that leverage the authenticated `Kite` client:
    - `/api/user/profile`: Fetch and return user profile details.
    - `/api/market/quote/{instrument_token}`: Get real-time market quotes.
    - `/api/portfolio/holdings`: View user's portfolio holdings.
- [ ] Implement basic error handling and logging.

## Phase 4: Documentation and Testing

- [ ] Update `plan.md` with clear instructions on how to:
    - Set up the project.
    - Run the FastAPI application.
    - Test the authentication flow.
    - Test the initial API endpoints (e.g., using `curl` or a browser).
- [ ] Consider adding a `README.md` for the backend.

## Backend Architecture (User-Centric)

```mermaid
graph TD
    A[User] --> B(Browser/Frontend)
    B --> C{FastAPI Backend}
    C --> D[Auth Endpoint]
    D --> E[Zerodha Login Page]
    E --> D
    D --> F[Callback Endpoint]
    F --> G[Kiteconnect Library]
    G --> H[Zerodha API]
    F --> I[Secure Session/Token Storage]
    C --> J{Middleware}
    J --> I
    J --> G
    J --> K[API Endpoints]
    K --> G
    K --> L[Data Cache/Storage (Optional)]
    G --> H
```

This plan provides a solid foundation for a user-facing backend, allowing for future expansion into features like stock screening and real-time data.
