# =============================================================================
# src/jobtread_client.py — Cliente Pave API do JobTread
# =============================================================================

import requests
from config import JT_GRANT_KEY, JT_API_URL


class JobTreadClient:
    """Cliente para a API Pave do JobTread."""

    def _headers(self):
        return {"Content-Type": "application/json"}

    def pave(self, query: dict) -> dict:
        """Executa uma query/mutation na API Pave do JobTread."""
        payload = {"query": {"$": {"grantKey": JT_GRANT_KEY}, **query}}
        resp = requests.post(JT_API_URL, json=payload, headers=self._headers())
        resp.raise_for_status()
        data = resp.json()

        # Checar erros de texto plano (API retorna string de erro)
        if isinstance(data, str):
            raise RuntimeError(f"JobTread API error: {data}")

        return data

    # ── Queries ───────────────────────────────────────────────────────────────

    def get_job(self, job_id: str) -> dict:
        """Busca um job pelo ID incluindo cost items existentes."""
        data = self.pave({
            "job": {
                "$": {"id": job_id},
                "id": {}, "name": {},
                "costItems": {
                    "$": {"size": 100},
                    "nodes": {
                        "id": {}, "name": {}, "quantity": {},
                        "unitCost": {}, "unitPrice": {},
                        "costType": {"id": {}, "name": {}},
                        "costCode": {"id": {}, "name": {}},
                        "description": {}, "isTaxable": {},
                    }
                }
            }
        })
        return data.get("job")

    def get_cost_groups(self, job_id: str) -> list:
        """Busca os cost groups de um job."""
        data = self.pave({
            "job": {
                "$": {"id": job_id},
                "costGroups": {
                    "$": {"size": 50},
                    "nodes": {"id": {}, "name": {}}
                }
            }
        })
        return data.get("job", {}).get("costGroups", {}).get("nodes", [])

    # ── Mutations ─────────────────────────────────────────────────────────────

    def create_cost_item(self, job_id: str, item: dict) -> dict:
        """
        Cria um cost item no budget de um job.

        item keys:
            name, quantity, unitCost, unitPrice,
            costCodeId, costTypeId,
            description (optional), isTaxable (default False),
            unitId (default Each), costGroupId (optional)
        """
        from config import JT_UNIT_EACH

        params = {
            "jobId":      job_id,
            "name":       item["name"],
            "quantity":   item["quantity"],
            "unitCost":   round(item["unitCost"], 2),
            "unitPrice":  round(item["unitPrice"], 2),
            "costCodeId": item["costCodeId"],
            "costTypeId": item["costTypeId"],
            "isTaxable":  item.get("isTaxable", False),
            "unitId":     item.get("unitId", JT_UNIT_EACH),
        }

        if item.get("description"):
            params["description"] = item["description"]

        if item.get("costGroupId"):
            params["costGroupId"] = item["costGroupId"]

        data = self.pave({"createCostItem": {"$": params}})
        return data.get("createCostItem", {})

    def update_cost_item(self, item_id: str, updates: dict) -> dict:
        """Atualiza campos de um cost item existente."""
        params = {"id": item_id, **updates}
        data = self.pave({"updateCostItem": {"$": params}})
        return data.get("updateCostItem", {})

    def delete_cost_item(self, item_id: str) -> dict:
        """Remove um cost item."""
        data = self.pave({"deleteCostItem": {"$": {"id": item_id}}})
        return data.get("deleteCostItem", {})
