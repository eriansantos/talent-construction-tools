# =============================================================================
# src/jobber_client.py — Cliente GraphQL do Jobber com OAuth auto-refresh
# =============================================================================

import re
import requests
from pathlib import Path
from config import (
    JOBBER_CLIENT_ID, JOBBER_CLIENT_SECRET, JOBBER_REFRESH_TOKEN,
    JOBBER_API_URL, JOBBER_TOKEN_URL, JOBBER_API_VERSION
)

_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.py"


def _persist_refresh_token(token: str) -> None:
    """Persiste o refresh_token rotacionado no config.py."""
    text = _CONFIG_PATH.read_text()
    new_text = re.sub(
        r'JOBBER_REFRESH_TOKEN\s*=\s*"[^"]*"',
        f'JOBBER_REFRESH_TOKEN = "{token}"',
        text,
    )
    if new_text != text:
        _CONFIG_PATH.write_text(new_text)


class JobberClient:
    """Cliente GraphQL do Jobber com renovação automática de access_token."""

    def __init__(self):
        self._refresh_token = JOBBER_REFRESH_TOKEN
        self._access_token  = None
        self._refresh_access_token()

    # ── Auth ──────────────────────────────────────────────────────────────────

    def _refresh_access_token(self):
        """Troca o refresh_token por um novo access_token."""
        resp = requests.post(JOBBER_TOKEN_URL, data={
            "client_id":     JOBBER_CLIENT_ID,
            "client_secret": JOBBER_CLIENT_SECRET,
            "grant_type":    "refresh_token",
            "refresh_token": self._refresh_token,
        })
        resp.raise_for_status()
        data = resp.json()

        if "access_token" not in data:
            raise RuntimeError(f"Jobber token refresh failed: {data}")

        self._access_token  = data["access_token"]
        # Jobber rotates the refresh_token on every use — persist the new one
        if "refresh_token" in data:
            self._refresh_token = data["refresh_token"]
            _persist_refresh_token(self._refresh_token)

        print(f"  [Jobber] Access token refreshed ✓")

    def _headers(self):
        return {
            "Content-Type":               "application/json",
            "Authorization":              f"Bearer {self._access_token}",
            "X-JOBBER-GRAPHQL-VERSION":   JOBBER_API_VERSION,
        }

    def query(self, gql: str, variables: dict = None) -> dict:
        """Executa uma query GraphQL; faz auto-retry com token renovado em 401."""
        payload = {"query": gql}
        if variables:
            payload["variables"] = variables

        resp = requests.post(JOBBER_API_URL, json=payload, headers=self._headers())

        if resp.status_code == 401:
            self._refresh_access_token()
            resp = requests.post(JOBBER_API_URL, json=payload, headers=self._headers())

        resp.raise_for_status()
        data = resp.json()

        if "errors" in data:
            raise RuntimeError(f"Jobber GraphQL error: {data['errors']}")

        return data.get("data", {})

    # ── Queries ───────────────────────────────────────────────────────────────

    def get_quote(self, quote_id: str) -> dict:
        """
        Busca um quote pelo ID numérico (ex: '57649446').
        Retorna o quote completo com lineItems e client info.
        """
        # Jobber usa IDs em formato Global ID (base64)
        # Converter: Z2lkOi8vSm9iYmVyL1F1b3RlLzU3NjQ5NDQ2
        import base64
        global_id = base64.b64encode(
            f"gid://Jobber/Quote/{quote_id}".encode()
        ).decode()

        gql = """
        query GetQuote($id: EncodedId!) {
            quote(id: $id) {
                id
                title
                quoteNumber
                quoteStatus
                message
                client {
                    id
                    name
                    companyName
                    emails { address primary }
                    phones { number primary }
                }
                property {
                    id
                    address {
                        street1 street2 city province postalCode
                    }
                }
                lineItems {
                    nodes {
                        name
                        description
                        quantity
                        unitPrice
                        unitCost
                        taxable
                    }
                }
                createdAt
                updatedAt
            }
        }
        """
        data = self.query(gql, {"id": global_id})
        return data.get("quote")

    def get_quotes_page(self, after: str = None, page_size: int = 50) -> dict:
        """
        Busca uma página de quotes para migração em massa.
        Retorna nodes + pageInfo para paginação.
        """
        gql = """
        query GetQuotes($first: Int!, $after: String) {
            quotes(first: $first, after: $after) {
                nodes {
                    id
                    title
                    quoteNumber
                    quoteStatus
                    client { id name companyName }
                    lineItems {
                        nodes {
                            name description quantity unitPrice unitCost taxable
                        }
                    }
                    createdAt
                }
                pageInfo {
                    hasNextPage
                    endCursor
                }
                totalCount
            }
        }
        """
        variables = {"first": page_size}
        if after:
            variables["after"] = after

        data = self.query(gql, variables)
        return data.get("quotes", {})

    def get_all_quotes(self, status_filter: list = None) -> list:
        """
        Busca TODOS os quotes via paginação automática.
        status_filter: lista de status a incluir (ex: ['approved', 'converted'])
        """
        all_quotes = []
        after = None

        print("  [Jobber] Buscando quotes...")
        while True:
            page = self.get_quotes_page(after=after, page_size=50)
            nodes = page.get("nodes", [])

            for q in nodes:
                if status_filter is None or q.get("quoteStatus") in status_filter:
                    all_quotes.append(q)

            page_info = page.get("pageInfo", {})
            if not page_info.get("hasNextPage"):
                break
            after = page_info.get("endCursor")
            print(f"  [Jobber]   → {len(all_quotes)} quotes carregados...")

        print(f"  [Jobber] Total: {len(all_quotes)} quotes encontrados")
        return all_quotes
