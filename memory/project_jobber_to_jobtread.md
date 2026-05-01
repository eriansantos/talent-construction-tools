---
name: Fluxo Jobber → JobTread (puxar quote pelo número)
description: Como ler um quote existente no Jobber pelo quoteNumber e recriá-lo como Job no JobTread, preservando preços e mapeando cost types/codes
type: project
---

Fluxo descoberto e validado em 2026-04-30 e expandido em 2026-05-01 com Erian (10 quotes migrados: 1478, 1476, 1461, 1458, 1355, 1354, 1353, 1351, 1349, 1334 — total $1,214,240.20).

**Why:** Antes do Jobber ser desligado, Erian quer migrar quotes individuais sob demanda — não migração em massa. Pedir o número do quote e a skill puxa, mostra preview e cria no JobTread.
**How to apply:** Quando o usuário pedir "pega o quote XXXX do Jobber e traz pro JobTread", seguir esse fluxo em vez do intake conversacional padrão.

---

## 1. Buscar quote no Jobber pelo número

```python
gql = '''
query FindQuote {
    quotes(first: 1, filter: {quoteNumber: {min: NUMERO, max: NUMERO}}) {
        nodes {
            id title quoteNumber quoteStatus message
            amounts { subtotal total depositAmount taxAmount }
            client {
                id name companyName
                emails { address primary }
                phones { number primary }
            }
            property { id address { street1 street2 city province postalCode } }
            lineItems { nodes { name description quantity unitPrice unitCost taxable } }
            createdAt
        }
        totalCount
    }
}
'''
data = client.query(gql, {})
```

Substituir os dois `NUMERO` pelo número do quote. Filtro é `IntRangeInput` (`{min, max}`), não int direto.

## 2. Pesquisar cliente no JobTread (igual à FASE 1 padrão)

Buscar por nome + emails + phones do quote. Sempre confirmar o match com o usuário antes de seguir.

## 3. Pesquisar location existente

Antes de criar location nova, listar `account.locations` e ver se o `address.street1` do Jobber bate com alguma já existente. Em endereços que já existem, o JobTread normaliza ("4887 Greencroft Road" → "4887 Greencroft Rd, Sarasota, FL 34235, USA"). Comparar pelo número da rua + nome principal.

## 4. Criar Job + cost items preservando preços do Jobber

- `unitPrice` = exato do Jobber.
- `unitCost`:
  - Se Jobber tinha `unitCost > 0` (sub conhecido) → preservar.
  - Senão → calcular pela margem do cost type escolhido (Labor 0.60, Materials 0.5909, Sub 0.50).
- Sempre incluir 2 placeholders (Inspection inicial + Final inspection).

## 5. Campos custom obrigatórios no Job

Sempre setar via `createJob`:

```python
"customFieldValues": {
    "22PTSCqdc5Wv": "Awaiting Response",  # Status (ou outro que o usuário pedir)
    "22PVu6hu5CCg": "1478",               # Jobber Quote — preservar rastreabilidade
}
```

⚠️ Os valores **persistem corretamente** via createJob — mas a leitura via `customFieldValues: {}` retorna vazio. Para verificar de verdade, ver `project_jobtread_api.md` (seção "Como LER customFieldValues").

## 6. Mapeamento de line item → costType / costCode

Mapping aplicado nos quotes 1478 e 1476 (ajustar conforme necessário):

| Tipo de item Jobber | costType | costCode |
|---|---|---|
| Roofing (subcontracted) | Subcontractor | Roofing |
| Drywall / popcorn / texture / level 4 / orange peel | Labor | Drywall |
| Cabinets | Labor | Cabinetry |
| Painting (interior, exterior, ceiling, frames) | Labor | Painting |
| Countertops (subcontracted) | Subcontractor | Countertops |
| Lanai rescreen / patio screen | Subcontractor | Patio Screen |
| Doors (front, side, interior, double) | Labor | Doors & Windows |
| HVAC / duct cleaning | Subcontractor | Mechanical |
| Demo (drop ceiling) | Labor | Demolition |
| Cement floor / grind / level | Labor | Concrete |
| LVP / hardwood / vinyl plank | Labor | Flooring |
| Baseboard / molding / trim | Labor | Trimwork |
| Electrical (panels, outlets, fans, lights) | Labor | Electrical |
| Plumbing (valves, faucets, disposal) | Labor | Plumbing |
| Tile (tub, shower, floor) | Labor | Tiling |
| Framing (metal stud / wood) | Labor | Framing |
| Landscaping (subcontracted) | Subcontractor | Landscaping |
| Appliances (Frigidaire kit) | Materials | Appliances |
| Mirrors / blinds / shelves / permits | Labor | Miscellaneous |
| Dumpster | Subcontractor | Miscellaneous |

## 7. Padrões aprendidos em sessões reais

### Endereço incompleto no Jobber
Quando a property tem só "Lorraine Road, Lakewood Ranch, FL" (sem número/zip), usar opção C: criar location com nome descritivo ("Harbor 58 — Lorraine Road, Lakewood Ranch") e endereço parcial. Avisar Erian para completar manualmente depois.

### Múltiplos quotes no mesmo projeto/building
Quando vários quotes são do mesmo building (ex: Harbor 58 — ADA, Residence, Staff, Lodge), **reusar a mesma location** para todos os jobs. Diferenciar pelos campos `description` do job (ex: "Harbor 58 — Typical ADA" vs "Harbor 58 — Lodge").

### Quote "converted" no Jobber → status no JobTread
Mesmo quando `quoteStatus: "converted"` no Jobber (quote já aceito/virou job), usar **"Awaiting Response"** no JobTread por padrão, a menos que Erian peça diferente. Erian gerencia o status manualmente.

### Itens de exclusão ($0)
Itens de exclusão/nota (ex: "A/C removal NOT included", qty=1, price=$0) devem ser incluídos **100% fiéis ao Jobber** como cost items com $0. Não omitir. Erian pediu "incluir 100%".

### Clientes com múltiplas LLCs
Erian às vezes usa nomes de LLC diferentes para o mesmo cliente. Ex: "A Strong Tower Construction LLC" (Jobber) = "Strong Tower Ventures LLC" (JobTread). Quando Erian confirma "é a mesma empresa", usar o account existente e atualizar o contato com os dados mais completos do Jobber.

## 8. Verificação obrigatória

Após criar tudo, somar `quantity × unitPrice` de todos os cost items e comparar com `amounts.subtotal` do Jobber. Delta deve ser **$0.00**. Mostrar a comparação ao Erian — ele pediu isso explicitamente em 2026-04-30.
