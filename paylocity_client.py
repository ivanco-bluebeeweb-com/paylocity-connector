"""Official Paylocity Web Services REST API client aligned with v2 companyId architecture."""
from __future__ import annotations
import httpx
from typing import Any, Optional

DEFAULT_PAYLOCITY_BASE = "https://api.paylocity.com/api/v2"

class PaylocityClient:
    def __init__(self, api_token: str, company_id: str, base_url: str = ""):
        self.api_token = api_token.strip()
        self.company_id = str(company_id).strip()
        self.base_url = (base_url.strip() if base_url else DEFAULT_PAYLOCITY_BASE).rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Imperal-Paylocity/0.1.0"
        }
        self.timeout = httpx.Timeout(30.0, connect=10.0)

    def _sanitize_msg(self, msg: str) -> str:
        if not msg:
            return ""
        if self.api_token and len(self.api_token) > 6:
            msg = msg.replace(self.api_token, self.api_token[:3] + "..." + self.api_token[-3:])
        return msg

    def _classify_error(self, resp: httpx.Response, action_name: str) -> dict[str, Any]:
        status = resp.status_code
        err_msg = ""
        try:
            data = resp.json()
            if "errors" in data and isinstance(data["errors"], list) and len(data["errors"]) > 0:
                err_msg = "; ".join(e.get("message", "") for e in data["errors"])
            elif "message" in data:
                err_msg = data["message"]
            elif "error" in data:
                err_msg = str(data["error"])
        except Exception:
            err_msg = resp.text[:200]
        err_msg = self._sanitize_msg(err_msg)

        if status == 429:
            retry_after = resp.headers.get("Retry-After", "60")
            return {
                "status": "error",
                "code": "RATE_LIMITED",
                "message": f"Paylocity rate limit reached during {action_name}. Retry after {retry_after}s.",
                "retry_after": int(retry_after) if retry_after.isdigit() else 60
            }
        if status == 401:
            return {
                "status": "error",
                "code": "UNAUTHORIZED",
                "message": f"Paylocity authentication failed during {action_name}: {err_msg or 'Invalid token or credentials'}"
            }
        if status == 403:
            return {
                "status": "error",
                "code": "FORBIDDEN",
                "message": f"Paylocity permission denied for {action_name}: {err_msg or 'Insufficient company scopes'}"
            }
        return {
            "status": "error",
            "code": "HTTP_ERROR",
            "message": f"Paylocity returned HTTP {status} during {action_name}: {err_msg}"
        }

    async def verify_auth(self) -> dict[str, Any]:
        """Verify API token against Paylocity company endpoint."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                url = f"{self.base_url}/companies/{self.company_id}" if self.company_id else f"{self.base_url}/companies"
                resp = await client.get(url, headers=self.headers)
                if resp.status_code in (200, 201):
                    return {"status": "connected", "verified": True, "data": resp.json()}
                return self._classify_error(resp, "verify_auth")
            except Exception as e:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(e))}

    async def list_employees(self, limit: int = 50, cursor: str = "") -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                url = f"{self.base_url}/companies/{self.company_id}/employees"
                params = {"pagesize": limit}
                if cursor:
                    params["pagenumber"] = cursor
                resp = await client.get(url, headers=self.headers, params=params)
                if resp.status_code in (200, 201):
                    data = resp.json()
                    items = data if isinstance(data, list) else data.get("employees", [])
                    return {"items": items, "total": len(items)}
                return self._classify_error(resp, "list_employees")
            except Exception as e:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(e))}

    async def get_employee(self, item_id: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                url = f"{self.base_url}/companies/{self.company_id}/employees/{item_id}"
                resp = await client.get(url, headers=self.headers)
                if resp.status_code in (200, 201):
                    return resp.json()
                return self._classify_error(resp, "get_employee")
            except Exception as e:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(e))}

    async def create_employee(self, name: str, details: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        payload = {"name": name, **(details or {})}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                url = f"{self.base_url}/companies/{self.company_id}/employees"
                resp = await client.post(url, headers=self.headers, json=payload)
                if resp.status_code in (200, 201):
                    return resp.json()
                return self._classify_error(resp, "create_employee")
            except Exception as e:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(e))}

    async def update_employee(self, item_id: str, details: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                url = f"{self.base_url}/companies/{self.company_id}/employees/{item_id}"
                resp = await client.put(url, headers=self.headers, json=details)
                if resp.status_code in (200, 201, 204):
                    return resp.json() if resp.text else {"id": item_id, "updated": True}
                return self._classify_error(resp, "update_employee")
            except Exception as e:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(e))}

    async def delete_employee(self, item_id: str) -> bool:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                url = f"{self.base_url}/companies/{self.company_id}/employees/{item_id}"
                resp = await client.delete(url, headers=self.headers)
                return resp.status_code in (200, 204)
            except Exception:
                return False

    async def list_payroll_runs(self, limit: int = 50, cursor: str = "") -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                url = f"{self.base_url}/companies/{self.company_id}/payentry"
                resp = await client.get(url, headers=self.headers)
                if resp.status_code in (200, 201):
                    data = resp.json()
                    items = data if isinstance(data, list) else data.get("payrolls", [])
                    return {"items": items, "total": len(items)}
                return self._classify_error(resp, "list_payroll_runs")
            except Exception as e:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(e))}

    async def get_payroll_run(self, item_id: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                url = f"{self.base_url}/companies/{self.company_id}/payentry/{item_id}"
                resp = await client.get(url, headers=self.headers)
                if resp.status_code in (200, 201):
                    return resp.json()
                return self._classify_error(resp, "get_payroll_run")
            except Exception as e:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(e))}

    async def create_payroll_run(self, name: str, details: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        payload = {"name": name, **(details or {})}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                url = f"{self.base_url}/companies/{self.company_id}/payentry"
                resp = await client.post(url, headers=self.headers, json=payload)
                if resp.status_code in (200, 201):
                    return resp.json()
                return self._classify_error(resp, "create_payroll_run")
            except Exception as e:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(e))}

    async def update_payroll_run(self, item_id: str, details: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                url = f"{self.base_url}/companies/{self.company_id}/payentry/{item_id}"
                resp = await client.put(url, headers=self.headers, json=details)
                if resp.status_code in (200, 201, 204):
                    return resp.json() if resp.text else {"id": item_id, "updated": True}
                return self._classify_error(resp, "update_payroll_run")
            except Exception as e:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(e))}

    async def delete_payroll_run(self, item_id: str) -> bool:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                url = f"{self.base_url}/companies/{self.company_id}/payentry/{item_id}"
                resp = await client.delete(url, headers=self.headers)
                return resp.status_code in (200, 204)
            except Exception:
                return False

    async def list_departments(self, limit: int = 50, cursor: str = "") -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                url = f"{self.base_url}/companies/{self.company_id}/costcenters"
                resp = await client.get(url, headers=self.headers)
                if resp.status_code in (200, 201):
                    data = resp.json()
                    items = data if isinstance(data, list) else data.get("costCenters", [])
                    return {"items": items, "total": len(items)}
                return self._classify_error(resp, "list_departments")
            except Exception as e:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(e))}

    async def get_department(self, item_id: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                url = f"{self.base_url}/companies/{self.company_id}/costcenters/{item_id}"
                resp = await client.get(url, headers=self.headers)
                if resp.status_code in (200, 201):
                    return resp.json()
                return self._classify_error(resp, "get_department")
            except Exception as e:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(e))}

    async def create_department(self, name: str, details: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        payload = {"name": name, **(details or {})}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                url = f"{self.base_url}/companies/{self.company_id}/costcenters"
                resp = await client.post(url, headers=self.headers, json=payload)
                if resp.status_code in (200, 201):
                    return resp.json()
                return self._classify_error(resp, "create_department")
            except Exception as e:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(e))}

    async def update_department(self, item_id: str, details: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                url = f"{self.base_url}/companies/{self.company_id}/costcenters/{item_id}"
                resp = await client.put(url, headers=self.headers, json=details)
                if resp.status_code in (200, 201, 204):
                    return resp.json() if resp.text else {"id": item_id, "updated": True}
                return self._classify_error(resp, "update_department")
            except Exception as e:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(e))}

    async def delete_department(self, item_id: str) -> bool:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                url = f"{self.base_url}/companies/{self.company_id}/costcenters/{item_id}"
                resp = await client.delete(url, headers=self.headers)
                return resp.status_code in (200, 204)
            except Exception:
                return False

    async def list_time_off_requests(self, limit: int = 50, cursor: str = "") -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                url = f"{self.base_url}/companies/{self.company_id}/timeoff"
                resp = await client.get(url, headers=self.headers)
                if resp.status_code in (200, 201):
                    data = resp.json()
                    items = data if isinstance(data, list) else data.get("timeOffRequests", [])
                    return {"items": items, "total": len(items)}
                return self._classify_error(resp, "list_time_off_requests")
            except Exception as e:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(e))}

    async def get_time_off_request(self, item_id: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                url = f"{self.base_url}/companies/{self.company_id}/timeoff/{item_id}"
                resp = await client.get(url, headers=self.headers)
                if resp.status_code in (200, 201):
                    return resp.json()
                return self._classify_error(resp, "get_time_off_request")
            except Exception as e:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(e))}

    async def create_time_off_request(self, name: str, details: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        payload = {"name": name, **(details or {})}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                url = f"{self.base_url}/companies/{self.company_id}/timeoff"
                resp = await client.post(url, headers=self.headers, json=payload)
                if resp.status_code in (200, 201):
                    return resp.json()
                return self._classify_error(resp, "create_time_off_request")
            except Exception as e:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(e))}

    async def update_time_off_request(self, item_id: str, details: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                url = f"{self.base_url}/companies/{self.company_id}/timeoff/{item_id}"
                resp = await client.put(url, headers=self.headers, json=details)
                if resp.status_code in (200, 201, 204):
                    return resp.json() if resp.text else {"id": item_id, "updated": True}
                return self._classify_error(resp, "update_time_off_request")
            except Exception as e:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(e))}

    async def delete_time_off_request(self, item_id: str) -> bool:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                url = f"{self.base_url}/companies/{self.company_id}/timeoff/{item_id}"
                resp = await client.delete(url, headers=self.headers)
                return resp.status_code in (200, 204)
            except Exception:
                return False

    async def list_benefit_plans(self, limit: int = 50, cursor: str = "") -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                url = f"{self.base_url}/companies/{self.company_id}/benefits"
                resp = await client.get(url, headers=self.headers)
                if resp.status_code in (200, 201):
                    data = resp.json()
                    items = data if isinstance(data, list) else data.get("benefits", [])
                    return {"items": items, "total": len(items)}
                return self._classify_error(resp, "list_benefit_plans")
            except Exception as e:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(e))}

    async def get_benefit_plan(self, item_id: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                url = f"{self.base_url}/companies/{self.company_id}/benefits/{item_id}"
                resp = await client.get(url, headers=self.headers)
                if resp.status_code in (200, 201):
                    return resp.json()
                return self._classify_error(resp, "get_benefit_plan")
            except Exception as e:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(e))}

    async def create_benefit_plan(self, name: str, details: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        payload = {"name": name, **(details or {})}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                url = f"{self.base_url}/companies/{self.company_id}/benefits"
                resp = await client.post(url, headers=self.headers, json=payload)
                if resp.status_code in (200, 201):
                    return resp.json()
                return self._classify_error(resp, "create_benefit_plan")
            except Exception as e:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(e))}

    async def update_benefit_plan(self, item_id: str, details: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                url = f"{self.base_url}/companies/{self.company_id}/benefits/{item_id}"
                resp = await client.put(url, headers=self.headers, json=details)
                if resp.status_code in (200, 201, 204):
                    return resp.json() if resp.text else {"id": item_id, "updated": True}
                return self._classify_error(resp, "update_benefit_plan")
            except Exception as e:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(e))}

    async def delete_benefit_plan(self, item_id: str) -> bool:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                url = f"{self.base_url}/companies/{self.company_id}/benefits/{item_id}"
                resp = await client.delete(url, headers=self.headers)
                return resp.status_code in (200, 204)
            except Exception:
                return False

    async def list_direct_deposits(self, limit: int = 50, cursor: str = "") -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                url = f"{self.base_url}/companies/{self.company_id}/directdeposit"
                resp = await client.get(url, headers=self.headers)
                if resp.status_code in (200, 201):
                    data = resp.json()
                    items = data if isinstance(data, list) else data.get("directDeposits", [])
                    return {"items": items, "total": len(items)}
                return self._classify_error(resp, "list_direct_deposits")
            except Exception as e:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(e))}

    async def get_direct_deposit(self, item_id: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                url = f"{self.base_url}/companies/{self.company_id}/directdeposit/{item_id}"
                resp = await client.get(url, headers=self.headers)
                if resp.status_code in (200, 201):
                    return resp.json()
                return self._classify_error(resp, "get_direct_deposit")
            except Exception as e:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(e))}

    async def create_direct_deposit(self, name: str, details: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        payload = {"name": name, **(details or {})}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                url = f"{self.base_url}/companies/{self.company_id}/directdeposit"
                resp = await client.post(url, headers=self.headers, json=payload)
                if resp.status_code in (200, 201):
                    return resp.json()
                return self._classify_error(resp, "create_direct_deposit")
            except Exception as e:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(e))}

    async def update_direct_deposit(self, item_id: str, details: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                url = f"{self.base_url}/companies/{self.company_id}/directdeposit/{item_id}"
                resp = await client.put(url, headers=self.headers, json=details)
                if resp.status_code in (200, 201, 204):
                    return resp.json() if resp.text else {"id": item_id, "updated": True}
                return self._classify_error(resp, "update_direct_deposit")
            except Exception as e:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(e))}

    async def delete_direct_deposit(self, item_id: str) -> bool:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                url = f"{self.base_url}/companies/{self.company_id}/directdeposit/{item_id}"
                resp = await client.delete(url, headers=self.headers)
                return resp.status_code in (200, 204)
            except Exception:
                return False
