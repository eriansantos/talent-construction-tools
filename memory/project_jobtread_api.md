---
name: JobTread Pave API — fluxo completo descoberto
description: Mutations, field names, custom field IDs e padrões descobertos para criar clientes e jobs na Talent Construction via Pave API
type: project
---

Fluxo completo para criar cliente + job do zero via Pave API (100% descoberto empiricamente em 2026-04-24).

**Why:** A documentação da Pave API é limitada — esse mapeamento evita re-descoberta.
**How to apply:** Usar esses IDs e formatos exatos ao implementar o estimator.py.

---

## 1. createAccount

```python
client.pave({"createAccount": {"$": {
    "organizationId": JT_ORG_ID,
    "name": "Cliente Nome",
    "type": "customer",  # ou "vendor"
}}})
# Retorna {} — buscar ID depois listando accounts
```

## 2. createLocation (endereço geocodado automaticamente)

```python
client.pave({"createLocation": {"$": {
    "accountId": account_id,
    "name": "Endereço completo como string",
    "address": "15168 Sunny Day Dr, Bradenton FL 34211",  # string — API geocoda
}}})
# Retorna {} — buscar ID depois via account.locations
```

## 3. createContact (com phone + email)

```python
client.pave({"createContact": {"$": {
    "accountId": account_id,
    "name": "Nome Completo",
    "customFieldValues": {
        "22PTSCqdgBQF": "(978) 270-1972",       # Phone
        "22PTSCqdTUsJ": "email@exemplo.com",      # Email
    }
}}})
```

## 4. updateAccount (Type + Needs)

```python
client.pave({"updateAccount": {"$": {
    "id": account_id,
    "customFieldValues": {
        "22PTsXZ3ZAd6": "Residential",   # Type
        "22PTsXhrYBgf": "Painting",       # Needs (pode ser lista: ["Painting", "Repair"])
    }
}}})
```

## 5. createJob

```python
client.pave({"createJob": {"$": {
    "locationId": location_id,
    # NÃO passar "name" — o sistema gera automaticamente "Job XXXX"
    "description": "Crack Repair + Touch-Up Painting",  # descrição vai aqui
    "customFieldValues": {
        "22PTSCqdc5Wv": "Estimating",   # Status (obrigatório)
    }
}}})
# Retorna {} — buscar ID depois listando jobs (pegar o de número mais alto)
```

⚠️ O campo `name` é gerado automaticamente pelo JobTread ("Job 2031", "Job 2032"...).
NÃO sobrescrever com texto descritivo — isso aparece no lugar do número do job na UI.
A descrição real do job vai no campo `description`.

## 6. createCostItem — já implementado em jobtread_client.py

✅ SEMPRE criar estes 2 itens em TODO job, antes e depois dos itens reais:
- "Inspection and evaluation labor" (qty=0, price=0, Labor/Foundation) — primeiro
- "Final inspection" (qty=0, price=0, Labor/Foundation) — último
O catálogo do JobTread tem esses itens mas não é acessível via Pave API — criamos direto.

---

## Custom Field IDs — Talent General Services Inc

### Account-level
| Campo | ID | Tipo | Opções |
|---|---|---|---|
| Type | `22PTsXZ3ZAd6` | option | Commercial, Residential, Other |
| Needs | `22PTsXhrYBgf` | option | New Build, Addition, Full Remodel, Remodel, Kitchen Remodel, Bathroom Remodel, Painting, Repair |
| Status (account) | `22PTsXmCmiaS` | option | — |
| Lead Source | `22PTsXR4ZsEq` | option | — |
| Notes | `22PTsXU8jCKn` | text | — |
| Referred By | `22PTsXWyP5RD` | text | — |

### Contact-level
| Campo | ID | Tipo |
|---|---|---|
| Phone | `22PTSCqdgBQF` | phoneNumber |
| Email | `22PTSCqdTUsJ` | emailAddress |
| Mobile | `22PTsXtjLXbi` | phoneNumber |
| Secondary Email | `22PTsXu4cM5T` | emailAddress |

### Job-level
| Campo | ID | Tipo | Opções válidas |
|---|---|---|---|
| Status | `22PTSCqdc5Wv` | option | New Lead, Appointment Set, Estimating, Awaiting Response, On Hold, Permitting, Design / Architect Review, Awaiting Start, In Progress, Closed Won, Archived |
| Remodel Type | `22PTsYe2zizA` | — | — |
| Job Type | `22PTsYZgaDBy` | — | — |
| Jobber Quote | `22PVu6hu5CCg` | — | — |
| Planned Start Date | `22PVu85BJfcw` | date | — |

---

## Paginação da API (cursor-based)

```python
cursor = None
while True:
    args = {"size": 100}
    if cursor:
        args["page"] = cursor   # "page" aceita cursor string, NÃO número inteiro
    data = client.pave({"organization": {"$": {"id": JT_ORG_ID},
        "jobs": {"$": args, "nodes": {...}, "nextPage": {}}}})
    nodes = data["organization"]["jobs"]["nodes"]
    cursor = data["organization"]["jobs"].get("nextPage")
    if not cursor:
        break
```

## Como obter ID após criação (mutations retornam {})

- **Account:** listar todos accounts e filtrar por name (943 accounts na org)
- **Location:** `account.locations` após criar
- **Contact:** `account.contacts` após criar
- **Job:** listar todos jobs, pegar o mais recente por `createdAt` (ou número mais alto)

## ⚠️ Como LER customFieldValues — formato CORRETO

A query `"customFieldValues": {}` (selection vazia) **sempre retorna `{}`, mesmo quando há valores salvos**. Isso é trap silenciosa — não dá erro, só mente. Para realmente ler os valores precisa pedir nodes com sub-selection:

```python
# ✅ CORRETO — retorna os valores
"customFieldValues": {
    "$": {"size": 50},
    "nodes": {
        "customField": {"id": {}, "name": {}},
        "value": {},
    }
}

# ❌ ERRADO — retorna {} mesmo quando há valores
"customFieldValues": {}

# ❌ ERRADO — campo não existe
"customFieldValues": {"22PVu6hu5CCg": {}}
```

Nota: `customFieldValues` é uma **lista de nodes**, cada um com `customField` (referência) e `value` (string). Para escrever (em createJob/updateAccount/etc) ainda usa o formato dict `{field_id: value}` — só a leitura que muda.

## Como PUXAR quote do Jobber pelo número

`quoteNumber` no filtro é `IntRangeInput`, não int direto:

```python
# ✅ CORRETO
quotes(first: 1, filter: {quoteNumber: {min: 1478, max: 1478}}) { nodes {...} }

# ❌ ERRADO — "Argument 'quoteNumber' has an invalid value (1478). Expected type 'IntRangeInput'"
quotes(first: 1, filter: {quoteNumber: 1478}) { nodes {...} }
```

Campo de subtotal é `amounts.subtotal` (não `subtotalPrice`).

## Estrutura de costItems (position field)

Cada cost item aparece em múltiplas "positions" (b, c, d...) na API — são colunas financeiras internas do JobTread (budget vs revenue vs actual). O UI mostra como uma linha só. Criar apenas 1 costItem por linha lógica.
