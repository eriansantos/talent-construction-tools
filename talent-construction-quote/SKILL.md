---
name: talent-construction-quote
description: "Criar novo orçamento (estimate/quote) para a Talent Construction e enviar ao JobTread via API. Use este skill SEMPRE que o usuário quiser: criar orçamento, gerar proposta, montar estimate, colocar job no JobTread, push estimate to JobTread, novo cliente com orçamento, quote para cliente, precificar um serviço, calcular cost items no JobTread. Trigger phrases: 'cria um orçamento', 'crie um orçamento', 'criar orçamento', 'novo quote', 'quote', 'criar quote', 'create quote', 'estimate', 'criar estimate', 'fazer estimate', 'faz um estimate', 'proposta', 'criar proposta', 'precisa de proposta', 'novo job no JobTread', 'manda pro JobTread', 'novo cliente', 'envia pro sistema'."
---

# Talent Construction — Quote Creator

Skill para criar orçamentos conversacionalmente e enviar ao JobTread via API (100% automatizado).

**Repositório:** `https://github.com/eriansantos/talent-construction-tools`

> **Princípio desta skill:** ela aprende com cada orçamento criado. Toda correção de preço,
> novo escopo ou observação operacional é registrada no repositório e fica disponível para
> todas as máquinas na próxima vez que a skill for usada. Sempre sincronize antes de começar
> (FASE 0) e sempre registre o aprendizado ao terminar (FASE 4).

---

## Fluxo de Trabalho

> **Regra de ouro:** este ciclo se repete para **cada quote individual** — mesmo que sejam
> vários na mesma sessão. Pull antes, push depois. Sempre.

0. **Setup + Sync** — verificar instalação; `git pull` para pegar melhorias mais recentes
1. **Intake** — coletar info do cliente e escopo (UMA pergunta por vez)
2. **Proposta** — gerar preview em markdown
3. **Confirmação** — usuário aprova preços
4. **Execução** — criar no JobTread via API
5. **Aprendizado** — registrar aprendizados e fazer `git push`

Se houver um segundo quote na mesma sessão: voltar para a **FASE 0.2** (git pull) antes de iniciar o intake do próximo.

---

## FASE 0 — Setup + Sync

### 0.1 — Verificar instalação

```bash
python3 -c "import os; print(os.path.exists(os.path.expanduser('~/Projects/talent-construction-tools')))"
```

**Se `True`:** usar `~/Projects/talent-construction-tools` como PROJECT_DIR.

**Se `False`:** exibir ao usuário:

> Este skill precisa do projeto instalado localmente.
>
> ```bash
> git clone https://github.com/eriansantos/talent-construction-tools
> ```
> Em qual diretório você clonou (ou quer clonar)?

Após o usuário informar o caminho, verificar se `src/jobtread_client.py` existe. Guardar como **PROJECT_DIR**.

Configurar venv se necessário:
```bash
cd PROJECT_DIR && python3 -m venv .venv 2>/dev/null; .venv/bin/pip install requests -q
```

### 0.2 — Sincronizar melhorias do repositório

Executar **antes de cada novo quote** — inclusive o segundo, terceiro, etc. na mesma sessão:

```bash
cd PROJECT_DIR && git pull --rebase origin main
```

Se houver conflito: avisar o usuário e pedir para resolver manualmente antes de continuar.

Se bem-sucedido: informar brevemente quantos commits foram baixados (ou "já atualizado").

---

## FASE 1 — Intake (uma pergunta por vez, nessa ordem)

Pergunte exatamente uma coisa por vez. Não agrupe perguntas. Avance só quando tiver a resposta.

### Sequência obrigatória

1. **Nome do cliente**
2. **Telefone**
3. **Email**
4. **Endereço da obra** (rua, cidade, estado, zip)
5. **Tipo** — mostrar como lista numerada:
   ```
   1. Commercial
   2. Residential
   3. Other
   ```
6. **Needs** — mostrar como lista (múltipla escolha, ex: "7, 8"):
   ```
   1. New Build
   2. Addition
   3. Full Remodel
   4. Remodel
   5. Kitchen Remodel
   6. Bathroom Remodel
   7. Painting
   8. Repair
   ```
7. **Descrição do escopo** — texto livre, o que precisa ser feito
8. **Perguntas de follow-up** sobre dimensões/quantidades conforme o escopo (SF, LF, EA, etc.)

**Regra de follow-up (passo 8):** Só faça perguntas se forem necessárias para precificar. Ex:
- Pintura → perguntar SF de parede ou confirmar "interior only"?
- Tile → perguntar SF da área
- Drywall → perguntar SF
- Crack repair pequeno → não precisa de dimensão, use LS
- Repair genérico → perguntar localização/escopo se não ficou claro

---

## FASE 2 — Gerar Proposta em Markdown

Após coletar tudo, gerar preview ANTES de executar. Formato:

```markdown
# TALENT CONSTRUCTION — PROPOSAL
**Client:** [Nome]
**Address:** [Endereço]
**Date:** [data de hoje]
**Validity:** 15 days

---

## Scope of Work

### [Nome da Seção, ex: Crack Repair + Touch-Up Painting]

| Item | Qty | Unit | Unit Price | Total |
|------|-----|------|-----------|-------|
| [descrição LS] | 1 | LS | $X,XXX | $X,XXX |

**Subtotal:** $X,XXX

---

## Financial Summary

| | |
|---|---|
| **Subtotal** | $X,XXX |
| **Total** | $X,XXX |

## Payment Terms
- 50% due upon signing
- 50% due upon completion

## Schedule
[X–Y weeks from start date, depending on material availability]

## Assumptions
- [Lista de premissas]

## Exclusions
- Permits (unless noted)
- Material supply unless included
- [outros exclusions relevantes]
```

Depois do preview, perguntar:

> **Preço bate com o que você faria manualmente? Confirma para criar no JobTread.**

Se o usuário corrigir algum preço antes de confirmar: **anotar a correção** — ela será registrada na FASE 5 como aprendizado.

---

## FASE 3 — Executar no JobTread

Ao receber confirmação, executar via Python inline. Substituir PROJECT_DIR pelo caminho real:

```python
import sys
sys.path.insert(0, 'PROJECT_DIR')
from src.jobtread_client import JobTreadClient
from config import JT_ORG_ID, JT_COST_TYPES, JT_COST_CODES

client = JobTreadClient()

# 1. Criar account (cliente)
client.pave({"createAccount": {"$": {
    "organizationId": JT_ORG_ID,
    "name": "[NOME_CLIENTE]",
    "type": "customer",
}}})

# 2. Buscar account_id
data = client.pave({"organization": {"$": {"id": JT_ORG_ID},
    "accounts": {"$": {"size": 100},
        "nodes": {"id": {}, "name": {}},
        "nextPage": {}
    }
}})
account_id = [a["id"] for a in data["organization"]["accounts"]["nodes"]
              if a["name"] == "[NOME_CLIENTE]"][0]

# 3. Criar location
client.pave({"createLocation": {"$": {
    "accountId": account_id,
    "name": "[ENDERECO_COMPLETO]",
    "address": "[ENDERECO_COMPLETO]",
}}})

# 4. Buscar location_id
data2 = client.pave({"account": {"$": {"id": account_id},
    "locations": {"$": {"size": 10},
        "nodes": {"id": {}, "name": {}}
    }
}})
location_id = data2["account"]["locations"]["nodes"][0]["id"]

# 5. Criar contact (phone + email)
PHONE_FIELD = "22PTSCqdgBQF"
EMAIL_FIELD = "22PTSCqdTUsJ"
client.pave({"createContact": {"$": {
    "accountId": account_id,
    "name": "[NOME_CLIENTE]",
    "customFieldValues": {
        PHONE_FIELD: "[TELEFONE]",
        EMAIL_FIELD: "[EMAIL]",
    }
}}})

# 6. Atualizar account (Type + Needs)
TYPE_FIELD = "22PTsXZ3ZAd6"
NEEDS_FIELD = "22PTsXhrYBgf"
client.pave({"updateAccount": {"$": {
    "id": account_id,
    "customFieldValues": {
        TYPE_FIELD: "[TIPO]",
        NEEDS_FIELD: "[NEEDS]",
    }
}}})

# 7. Criar job
STATUS_FIELD = "22PTSCqdc5Wv"
client.pave({"createJob": {"$": {
    "locationId": location_id,
    "description": "[DESCRICAO_DO_SCOPE]",
    "customFieldValues": {
        STATUS_FIELD: "Estimating",
    }
}}})

# 8. Buscar job_id (número mais alto = mais recente)
data3 = client.pave({"organization": {"$": {"id": JT_ORG_ID},
    "jobs": {"$": {"size": 50},
        "nodes": {"id": {}, "name": {}}
    }
}})
jobs = data3["organization"]["jobs"]["nodes"]
job = max(jobs, key=lambda j: int(j["name"].replace("Job ", "").strip()) if j["name"].startswith("Job ") else 0)
job_id = job["id"]

# 9. Criar cost items (placeholder + reais + placeholder)
FOUNDATION_CODE = JT_COST_CODES["Foundation"]
LABOR_TYPE = JT_COST_TYPES["Labor"]["id"]

client.create_cost_item(job_id, {
    "name": "Inspection and evaluation labor",
    "quantity": 0, "unitPrice": 0, "unitCost": 0,
    "costTypeId": LABOR_TYPE, "costCodeId": FOUNDATION_CODE,
})

# [ itens reais aqui ]

client.create_cost_item(job_id, {
    "name": "Final inspection",
    "quantity": 0, "unitPrice": 0, "unitCost": 0,
    "costTypeId": LABOR_TYPE, "costCodeId": FOUNDATION_CODE,
})

print(f"Job criado: {job['name']} (ID: {job_id})")
print(f"Account: {account_id} | Location: {location_id}")
```

Executar com:
```bash
cd PROJECT_DIR && .venv/bin/python -c "..."
```

---

## FASE 4 — Aprendizado + Commit

Esta fase é **obrigatória** após cada quote criado com sucesso. É aqui que a skill melhora.

### 4.1 — Coletar aprendizados

Perguntar ao usuário:

> **Quote criado com sucesso!**
> Antes de fechar — alguma observação para registrar?
> - Preços que você ajustaria diferente?
> - Algum detalhe de escopo que surgiu e não estava no roteiro?
> - Algo que ficou faltando perguntar no intake?
> (Pode digitar livremente ou responder "nenhuma" para pular)

### 4.2 — Registrar nos arquivos corretos

Com base na resposta do usuário (e nas correções feitas na FASE 2):

**Se houver novo rate ou correção de preço:**
Atualizar `PROJECT_DIR/references/pricing.md` — adicionar ou corrigir a linha relevante na tabela, com nota de data e contexto.

**Se houver novo padrão de escopo ou pergunta de intake:**
Atualizar `PROJECT_DIR/memory/project_estimator_patterns.md` — adicionar na seção apropriada.

**Se houver nova descoberta da API JobTread:**
Atualizar `PROJECT_DIR/memory/project_jobtread_api.md`.

**Se houver mudança estrutural no fluxo da skill:**
Atualizar o próprio `SKILL.md` dentro do PROJECT_DIR (se existir cópia local) **e** informar o usuário que o `.skill` packaged precisará ser regerado.

### 4.3 — Commit e push automático

```bash
cd PROJECT_DIR && \
git add references/pricing.md memory/ && \
git commit -m "Learn: [ESCOPO] — [NOME_CLIENTE] ([DATA])" && \
git push origin main
```

Substituir:
- `[ESCOPO]` = tipo de trabalho (ex: "Crack Repair", "Interior Painting", "Tile Floor")
- `[NOME_CLIENTE]` = nome do cliente do quote (primeiro nome basta)
- `[DATA]` = data de hoje no formato YYYY-MM-DD

### 4.4 — Confirmar sincronização

Após o push bem-sucedido, informar:

> ✓ Aprendizado registrado e publicado. A outra máquina receberá essas melhorias na próxima vez que usar a skill.

---

## Regras de Cost Items

### Margens (unitCost = unitPrice × fator)

| CostType | Margem | Fator |
|----------|--------|-------|
| Labor | 40% | 0.60 |
| Materials | 40.91% | 0.5909 |
| Subcontractor | 50% | 0.50 |
| Equipment | 20% | 0.80 |

**Fórmula:** `unitCost = unitPrice * fator`

### Estrutura de cost item

```python
client.create_cost_item(job_id, {
    "name": "Nome do item",
    "quantity": 1,
    "unitPrice": 1100.00,
    "unitCost": 660.00,        # unitPrice * 0.60 para Labor
    "costTypeId": JT_COST_TYPES["Labor"]["id"],
    "costCodeId": JT_COST_CODES["Uncategorized"],
    "description": "- Passo 1\n- Passo 2\n- Passo 3",
    "isTaxable": False,
})
```

### Campos fixos em TODOS os itens
- `isTaxable`: False
- `unit`: Each (default no `create_cost_item`)

### Regra de ordem (CRÍTICO)
1. "Inspection and evaluation labor" (qty=0, price=0, Labor/Foundation) — PRIMEIRO
2. Itens reais do escopo
3. "Final inspection" (qty=0, price=0, Labor/Foundation) — ÚLTIMO

---

## IDs de Referência

```python
# Cost Types
LABOR_ID          = "22PTSCqzPHrM"
MATERIALS_ID      = "22PTSCqzPHrN"
SUBCONTRACTOR_ID  = "22PTSCqzPHrP"
EQUIPMENT_ID      = "22PULkCuttun"

# Cost Codes mais usados
UNCATEGORIZED  = "22PTSCqeDeQQ"
FOUNDATION     = "22PTSCqeDeQV"
DEMOLITION     = "22PTSCqeDeQS"
FRAMING        = "22PTSCqeDeQW"
MASONRY        = "22PTSCqeDeQX"
ELECTRICAL     = "22PTSCqeDeQa"
PLUMBING       = "22PTSCqeDeQb"
DRYWALL        = "22PTSCqeDeQe"
DOORS_WINDOWS  = "22PTSCqeDeQf"
FLOORING       = "22PTSCqeDeQh"
TILING         = "22PTSCqeDeQi"
PAINTING       = "22PTSCqeDeQp"
CONCRETE       = "22PTSCqeDeQu"
MISCELLANEOUS  = "22PTSCqeDeQx"
```

---

## Reference Pricing (Sarasota/Bradenton FL, 2026)

Consultar `references/pricing.md` para tabela completa de unit rates.

| Escopo | CostType | Rate |
|--------|----------|------|
| Crack repair + touch-up | Labor LS | ~$1,100 |
| Interior painting full (residência) | Labor LS | ~$15,800 |
| Drywall repair (por ocorrência) | Labor LS | ~$3,890 |
| Cement block wall (inclui stucco+paint) | Labor LS | ~$4,990–$9,980 |
| Shower remodel (completo) | Labor LS | ~$8,965 |
| Permits | Labor LS | ~$1,250 |
| Tile material | Materials SF | $15/SF |
| Tile installation | Labor SF | $12.50/SF |
| Window installation | Labor EA | $450/EA |
| Mobilization (small job) | Labor LS | $650 |
| Engineering plans | Subcontractor LS | ~$950 |

Para rates detalhados: ver `references/pricing.md`.

---

## Troubleshooting

**"API retorna {} em mutations"** — normal. Buscar o ID criado via query separada.

**Paginação** — usar cursor `nextPage` (string), não número inteiro. Max size: 100.

**Job name** — NUNCA setar `name` ao criar job. O JobTread gera "Job XXXX" automaticamente.

**Account duplicado** — checar se cliente já existe antes de criar.

**git push rejeitado** — fazer `git pull --rebase` antes e tentar novamente.

**Módulo não encontrado** — confirmar PROJECT_DIR e venv: `cd PROJECT_DIR && python3 -m venv .venv && .venv/bin/pip install requests`.
