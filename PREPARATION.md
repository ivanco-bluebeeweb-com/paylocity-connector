# Paylocity Connector — Preparation

## Product Scope
Build a comprehensive Imperal connector for **Paylocity** (C28. Payroll & Benefits Administration). The integration connects directly to the official **Paylocity Web Services API** (`https://api.paylocity.com/api/v2`), allowing organizations to manage workforce records, payroll runs, departments, time-off requests, benefit plans, and direct deposits scoped by `companyId`.

## Official API Specifications
- **API Version:** Paylocity Web Services REST API v2
- **Base URL:** `https://api.paylocity.com/api/v2`
- **Core Endpoints:**
  - `GET /companies/{companyId}/employees` — list employees
  - `GET /companies/{companyId}/employees/{employeeId}` — employee details
  - `GET /companies/{companyId}/payentry/payroll` — list payroll batches
  - `GET /companies/{companyId}/departments` — cost centers and departments
  - `GET /companies/{companyId}/timeoff` — leave requests
  - `GET /companies/{companyId}/benefits` — benefit plan elections
  - `GET /companies/{companyId}/directdeposit` — banking distribution
- **Authentication Model:** Bearer Token via `Authorization: Bearer <api_token>`
- **Mandatory Requirements:**
  - Scoping all tenant operations by `company_id` (Standard B7).
  - Explicit rate limit detection (HTTP 429) and auth classification (HTTP 401/403).
  - Sanitization of Bearer tokens in error traces (Standard B8).
  - Multi-tenant connection tracking via `connection_id` (Standard B9).

## Delivery Gates
1. [x] Official API discovery completed with Paylocity Web Services v2 specifications.
2. [x] Scoping by company_id and Bearer authentication verified.
3. [x] Five mandatory specification documents authored.
4. [x] Client implemented with B7-B10 compliance, secret redaction, and 429/401 classification.
5. [x] Panel sidebar implemented conforming to UI_INTERFACE_STANDARD.md.
6. [x] Action prices calibrated per PRICING_POLICY.md.
