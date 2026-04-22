# Talent Construction — Migration Tool
## Contexto para Claude Code

---

## 1. Sobre o Projeto

Este é o sistema de migração de dados da **Talent General Services Inc** (CGC #1537905), uma empresa de construção civil baseada em Sarasota, FL. O projeto migra quotes e line items do **Jobber** (sistema antigo) para o **JobTread** (sistema novo) via API, eliminando a necessidade de entrada manual de dados.

O repositório está em: `https://github.com/eriansantos/talent-migration`

---

## 2. Setup Inicial

```bash
# 1. Clonar o repositório
git clone https://github.com/eriansantos/talent-migration
cd talent-migration

# 2. Instalar dependência
pip install requests

# 3. Verificar estrutura
ls -la
```

Estrutura esperada:
```
talent-migration/
├── migrate.py              ← CLI principal — PONTO DE ENTRADA
├── config.py               ← Credenciais e IDs (já configurados)
├── src/
│   ├── jobber_client.py    ← API Jobber (OAuth 2.0 com auto-refresh)
│   ├── jobtread_client.py  ← API JobTread (Pave GraphQL)
│   ├── mapper.py           ← Mapeamento automático de campos
│   └── migrator.py         ← Motor de migração com logging
├── data/
│   └── jobs.json           ← Lista de jobs já migrados (histórico)
└── logs/                   ← Logs gerados automaticamente
```

---

## 3. Credenciais (já configuradas em config.py)

### Jobber
- **OAuth 2.0** com refresh token automático
- Client ID: `b461e924-5ad8-43b1-bcd1-3fa386cc955b`
- Refresh Token: `2e79af9c9f1a5caa5ffc1e97fe4c9472` (longa duração, auto-renovável)
- API: `https://api.getjobber.com/api/graphql`
- API Version: `2026-04-16`

### JobTread
- **Grant Key** (API Pave)
- Grant Key: `22TNA7yjhjmzG9CiqUqp9WmtS5Tt8U74bR`
- API: `https://api.jobtread.com/pave`
- Org ID: `22PTSCpmQVf5`

---

## 4. Como Executar

### Migrar um job específico
```bash
python migrate.py run --quote JOBBER_QUOTE_ID --job JOBTREAD_JOB_ID
```

### Forçar costType (normalmente "Labor")
```bash
python migrate.py run --quote 57649446 --job 22PVxgFHbqdU --type Labor
```

### Ver preview antes de executar (sem inserir nada)
```bash
python migrate.py run --quote 57649446 --job 22PVxgFHbqdU --type Labor --dry-run
```

### Migrar lista de jobs de uma vez (batch)
```bash
python migrate.py batch --file data/jobs.json
```

### Batch inline com pares
```bash
python migrate.py batch --pairs "57649446:22PVxgFHbqdU,57674580:22PW2eZiNRyH" --type Labor
```

---

## 5. Fluxo de Migração por Job

Quando o usuário fornece um par de links:
- **Jobber**: `https://secure.getjobber.com/quotes/QUOTE_ID`
- **JobTread**: `https://app.jobtread.com/jobs/JOB_ID/budget`

O processo é:
1. Extrair o `QUOTE_ID` da URL do Jobber (número no final)
2. Extrair o `JOB_ID` da URL do JobTread (string alfanumérica)
3. Executar: `python migrate.py run --quote QUOTE_ID --job JOB_ID --type Labor`

**Exemplo:**
- Jobber URL: `https://secure.getjobber.com/quotes/57649446` → QUOTE_ID = `57649446`
- JobTread URL: `https://app.jobtread.com/jobs/22PVxgFHbqdU/budget` → JOB_ID = `22PVxgFHbqdU`
- Comando: `python migrate.py run --quote 57649446 --job 22PVxgFHbqdU --type Labor`

---

## 6. Regras de Mapeamento

### costType (margem aplicada ao unitCost)
| Tipo de item | costType | Margem |
|---|---|---|
| Install, labor, service, repair, paint, demo, maintenance | **Labor** | 40% |
| Window, door, material, glass, tile material | **Materials** | 40.91% |
| Electrician, plumber, HVAC subcontratado | **Subcontractor** | 50% |
| Equipment, tool, rental, dumpster | **Equipment** | 20% |

> **Regra geral da Talent Construction**: usar `--type Labor` para a maioria dos jobs.

### unitCost calculado automaticamente
```
unitCost = unitPrice × (1 - margin)
```
- Labor: unitCost = unitPrice × 0.60
- Materials: unitCost = unitPrice × 0.5909
- Subcontractor: unitCost = unitPrice × 0.50

### Campos fixos em todos os itens
- `isTaxable`: false
- `unit`: Each (`22PTSCqe6CSX`)
- `description`: texto extraído do Jobber (quando disponível)

### costCode detectado automaticamente por palavras-chave
- window/door/glass/impact → Doors & Windows
- floor/lvp/laminate → Flooring
- tile/ceramic/porcelain → Tiling
- paint/texture/popcorn → Painting
- drywall/sheetrock → Drywall
- electric/circuit/fan → Electrical
- plumb/pipe/drain → Plumbing
- cement/block/masonry/stucco → Masonry
- frame/framing/stud → Framing
- demo/demolit/remov → Demolition
- maintenance/repair/general → Miscellaneous

---

## 7. IDs da Organização (Talent General Services Inc)

### Cost Types
| Nome | ID | Margem |
|---|---|---|
| Labor | `22PTSCqzPHrM` | 40% |
| Materials | `22PTSCqzPHrN` | 40.91% |
| Subcontractor | `22PTSCqzPHrP` | 50% |
| Other | `22PTSCqzPHrQ` | 5% |
| Equipment | `22PULkCuttun` | 20% |

### Cost Codes (prefixo `22PTSCqeDe`)
| Nome | Sufixo |
|---|---|
| Uncategorized | QQ |
| Demolition | QS |
| Foundation | QV |
| Framing | QW |
| Masonry | QX |
| Roofing | QZ |
| Electrical | Qa |
| Plumbing | Qb |
| Mechanical | Qc |
| Drywall | Qe |
| Doors & Windows | Qf |
| Flooring | Qh |
| Tiling | Qi |
| Cabinetry | Qj |
| Countertops | Qk |
| Trimwork | Qm |
| Painting | Qp |
| Appliances | Qq |
| Concrete | Qu |
| Miscellaneous | Qx |
| Patio Screen | `22PV9qCimiam` |
| Staircase | `22PVKNv6tqZk` |

---

## 8. Jobs Já Migrados (Histórico)

| Quote Jobber | Job JobTread | Cliente | costType |
|---|---|---|---|
| 57649446 | 22PVxgFHbqdU | Impact Windows | Materials/Labor |
| 57674580 | 22PW2eZiNRyH | Jacob Dybas | Labor |
| 57617192 | 22PW2iqdJsnb | Kristela Myteberi | Labor |
| 57759185 | 22PW2nyNmafs | Solarzanos Pizza Express | Labor |
| 57275516 | 22PW2reGDbX9 | A Sharper Edge | Labor |
| 57276465 | 22PW2tHMMFez | A Sharper Edge #2 | Labor |
| 54929934 | 22PW2u4ZjGVJ | Loren Cook | Labor |
| 53215077 | 22PW2vXVvbKL | Jonathan Clermont | Labor |

---

## 9. Comportamento Esperado ao Receber Novos Jobs

Quando o usuário fornecer novos links para migrar:

1. Extrair IDs das URLs
2. Executar preview primeiro: `python migrate.py run --quote X --job Y --type Labor --dry-run`
3. Confirmar o mapeamento com o usuário se necessário
4. Executar a migração: `python migrate.py run --quote X --job Y --type Labor`
5. Verificar o resultado no log
6. Atualizar `data/jobs.json` com o novo job
7. Fazer commit no GitHub:
   ```bash
   git add data/jobs.json
   git commit -m "Add job: quote X → JT job Y"
   git push
   ```

---

## 10. Troubleshooting

### Erro: "Quote not found"
- Verificar se o ID do quote está correto
- O Jobber usa Global IDs em base64 — o `jobber_client.py` faz a conversão automaticamente

### Erro: "Job already has cost items — skipping"
- O job já tem itens migrados
- Usar `--force` para inserir mesmo assim: `python migrate.py run --quote X --job Y --force`

### Erro de autenticação Jobber (401)
- O refresh token expirou — gerar novo via fluxo OAuth
- Atualizar `JOBBER_REFRESH_TOKEN` em `config.py`

### Refresh token do Jobber
- O token é renovado automaticamente a cada chamada
- Se der erro persistente, o fluxo OAuth precisa ser refeito no Developer Center:
  `https://developer.getjobber.com/apps/MTU0NTk3`

---

## 11. Contexto do Negócio

A **Talent General Services Inc** é uma empreiteira geral (CGC #1537905) baseada em Sarasota, FL. Serviços: remodeling, pintura, drywall, piso, manutenção e permits. Está migrando do Jobber para o JobTread como sistema principal de gestão de projetos. Esta ferramenta garante que o histórico de quotes aprovados seja preservado no novo sistema com o mapeamento correto de custos e categorias.
