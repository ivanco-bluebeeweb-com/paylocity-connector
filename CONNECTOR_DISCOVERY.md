# Paylocity Connector — Connector Discovery

## Official API Landscape
Paylocity exposes a company-scoped REST API v2:
- **Base Endpoint:** `https://api.paylocity.com/api/v2`
- **Company Hierarchy:** Every resource is routed under `/companies/{companyId}`.
- **Authentication:** Bearer token issued via Paylocity Web Services integration credentials.
- **Rate Limits & Throttling:** Paylocity enforces transactional rate limits with HTTP 429 and `Retry-After`.
