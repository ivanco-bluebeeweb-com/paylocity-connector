# Paylocity Connector — Authentication & Credentials Standard

## Standard Alignment (B1–B10)
- **B1 (Real Provider Names):** Connects to Paylocity Web Services API v2.
- **B2 (No Secrets in Code):** All tokens stored securely in `ctx.secrets`.
- **B7 (Company Scoping):** Explicit `company_id` required for all API calls.
- **B8 (Sanitization & HTTP Status):** Masking tokens in error messages; classification of 401, 403, and 429.
- **B9 (Multi-tenant Isolation):** Dynamic resolution via `connection_id`.
