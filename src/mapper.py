# =============================================================================
# src/mapper.py — Mapeamento de line items Jobber → cost items JobTread
# =============================================================================

import re
from config import JT_COST_TYPES, JT_COST_CODES, COST_TYPE_RULES, COST_CODE_RULES


def detect_cost_type(name: str, description: str = "") -> str:
    """Detecta o costType correto pelo nome e descrição do item."""
    text = (name + " " + (description or "")).lower()

    for cost_type, keywords in COST_TYPE_RULES:
        if any(kw in text for kw in keywords):
            return cost_type

    return "Labor"  # default conservador


def detect_cost_code(name: str, description: str = "") -> str:
    """Detecta o costCode correto pelo nome e descrição do item."""
    text = (name + " " + (description or "")).lower()

    for cost_code, keywords in COST_CODE_RULES:
        if any(kw in text for kw in keywords):
            return cost_code

    return "Uncategorized"


def calc_unit_cost(unit_price: float, cost_type_name: str) -> float:
    """
    Calcula o unitCost a partir do unitPrice e da margem do costType.
    unitCost = unitPrice × (1 - margin)
    """
    ct = JT_COST_TYPES.get(cost_type_name, JT_COST_TYPES["Labor"])
    return round(unit_price * (1 - ct["margin"]), 2)


def build_description(line_item: dict) -> str | None:
    """
    Constrói o campo description do cost item a partir do line item do Jobber.
    Retorna None se não houver descrição relevante.
    """
    desc = (line_item.get("description") or "").strip()
    return desc if desc else None


def map_line_item(line_item: dict, override_cost_type: str = None, override_cost_code: str = None) -> dict:
    """
    Converte um line item do Jobber em um cost item pronto para o JobTread.

    Parâmetros:
        line_item: dict com keys name, description, quantity, unitPrice, unitCost, taxable
        override_cost_type: força um costType específico (ex: "Labor")

    Retorna dict com todos os campos necessários para create_cost_item.
    """
    name        = line_item.get("name", "").strip()
    description = line_item.get("description", "") or ""
    quantity    = float(line_item.get("quantity", 1))
    unit_price  = float(line_item.get("unitPrice", 0))

    # CostType
    cost_type_name = override_cost_type or detect_cost_type(name, description)
    cost_type_id   = JT_COST_TYPES[cost_type_name]["id"]

    # CostCode
    cost_code_name = override_cost_code or detect_cost_code(name, description)
    cost_code_id   = JT_COST_CODES.get(cost_code_name, JT_COST_CODES["Uncategorized"])

    # UnitCost
    unit_cost = calc_unit_cost(unit_price, cost_type_name)

    # Description
    desc = build_description(line_item)

    return {
        "name":         name,
        "quantity":     quantity,
        "unitPrice":    unit_price,
        "unitCost":     unit_cost,
        "costTypeId":   cost_type_id,
        "costTypeName": cost_type_name,
        "costCodeId":   cost_code_id,
        "costCodeName": cost_code_name,
        "description":  desc,
        "isTaxable":    False,
    }


def map_quote(quote: dict, override_cost_type: str = None, override_cost_code: str = None) -> list:
    """
    Converte todos os line items de um quote do Jobber em cost items do JobTread.

    Retorna lista de cost items mapeados.
    """
    line_items = quote.get("lineItems", {}).get("nodes", [])
    mapped = []

    for li in line_items:
        item = map_line_item(li, override_cost_type=override_cost_type, override_cost_code=override_cost_code)
        mapped.append(item)

    return mapped


def preview_mapping(quote: dict, override_cost_type: str = None, override_cost_code: str = None) -> str:
    """
    Gera um preview legível do mapeamento de um quote.
    Útil para validação antes de executar a migração.
    """
    items = map_quote(quote, override_cost_type, override_cost_code)
    lines = [
        f"\n{'─'*70}",
        f"PREVIEW: {quote.get('title', 'N/A')} (#{quote.get('quoteNumber', 'N/A')})",
        f"{'─'*70}",
        f"{'Item':<40} {'Qty':>6} {'Unit Price':>12} {'Unit Cost':>12} {'Type':<14} {'Code'}",
        f"{'─'*70}",
    ]

    total = 0.0
    for item in items:
        total += item["quantity"] * item["unitPrice"]
        lines.append(
            f"{item['name'][:38]:<40} "
            f"{item['quantity']:>6.2f} "
            f"${item['unitPrice']:>11.2f} "
            f"${item['unitCost']:>11.2f} "
            f"{item['costTypeName']:<14} "
            f"{item['costCodeName']}"
        )

    lines.append(f"{'─'*70}")
    lines.append(f"{'TOTAL':>58} ${total:>11.2f}")
    return "\n".join(lines)
