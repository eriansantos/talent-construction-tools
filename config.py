# =============================================================================
# config.py — Talent Construction Migration Tool
# Jobber → JobTread
# =============================================================================

# ─── JOBBER OAuth ─────────────────────────────────────────────────────────────
JOBBER_CLIENT_ID     = "b461e924-5ad8-43b1-bcd1-3fa386cc955b"
JOBBER_CLIENT_SECRET = "4dc6012cf1cb5700bfd0ef35b78edc4590d6457472b5ff27d06c296128c1c85b"
JOBBER_REFRESH_TOKEN = "94138f7d83f0000d6a13bbf4f2024e3d"
JOBBER_API_URL       = "https://api.getjobber.com/api/graphql"
JOBBER_TOKEN_URL     = "https://api.getjobber.com/api/oauth/token"
JOBBER_API_VERSION   = "2026-04-16"

# ─── JOBTREAD API ─────────────────────────────────────────────────────────────
JT_GRANT_KEY = "22TNA7yjhjmzG9CiqUqp9WmtS5Tt8U74bR"
JT_API_URL   = "https://api.jobtread.com/pave"

# ─── JOBTREAD — IDs da organização Talent General Services Inc ────────────────
JT_ORG_ID    = "22PTSCpmQVf5"
JT_UNIT_EACH = "22PTSCqe6CSX"

JT_COST_TYPES = {
    "Labor":         {"id": "22PTSCqzPHrM", "margin": 0.40},
    "Materials":     {"id": "22PTSCqzPHrN", "margin": 0.4091},
    "Subcontractor": {"id": "22PTSCqzPHrP", "margin": 0.50},
    "Other":         {"id": "22PTSCqzPHrQ", "margin": 0.05},
    "Equipment":     {"id": "22PULkCuttun", "margin": 0.20},
}

JT_COST_CODES = {
    "Uncategorized":      "22PTSCqeDeQQ",
    "Planning":           "22PTSCqeDeQR",
    "Demolition":         "22PTSCqeDeQS",
    "Excavation":         "22PTSCqeDeQT",
    "Utilities":          "22PTSCqeDeQU",
    "Foundation":         "22PTSCqeDeQV",
    "Framing":            "22PTSCqeDeQW",
    "Masonry":            "22PTSCqeDeQX",
    "Siding":             "22PTSCqeDeQY",
    "Roofing":            "22PTSCqeDeQZ",
    "Electrical":         "22PTSCqeDeQa",
    "Plumbing":           "22PTSCqeDeQb",
    "Mechanical":         "22PTSCqeDeQc",
    "Insulation":         "22PTSCqeDeQd",
    "Drywall":            "22PTSCqeDeQe",
    "Doors & Windows":    "22PTSCqeDeQf",
    "Garage":             "22PTSCqeDeQg",
    "Flooring":           "22PTSCqeDeQh",
    "Tiling":             "22PTSCqeDeQi",
    "Cabinetry":          "22PTSCqeDeQj",
    "Countertops":        "22PTSCqeDeQk",
    "Trimwork":           "22PTSCqeDeQm",
    "Specialty Finishes": "22PTSCqeDeQn",
    "Painting":           "22PTSCqeDeQp",
    "Appliances":         "22PTSCqeDeQq",
    "Decking":            "22PTSCqeDeQr",
    "Fencing":            "22PTSCqeDeQs",
    "Pools":              "22PTSCqeDeQt",
    "Concrete":           "22PTSCqeDeQu",
    "Landscaping":        "22PTSCqeDeQv",
    "Furnishings":        "22PTSCqeDeQw",
    "Miscellaneous":      "22PTSCqeDeQx",
    "Patio Screen":       "22PV9qCimiam",
    "Staircase":          "22PVKNv6tqZk",
}

# ─── MAPEAMENTO: palavras-chave → costType ────────────────────────────────────
COST_TYPE_RULES = [
    ("Labor",         ["install", "labor", "service", "inspection", "evaluat",
                       "permit", "plan", "review", "demo", "demolit", "repair",
                       "paint", "maintenance", "pressure wash", "recaulk", "texture"]),
    ("Materials",     ["window", "door", "material", "supply", "product", "glass",
                       "panel", "unit", "tile material", "flooring material"]),
    ("Subcontractor", ["sub", "electrici", "plumb", "hvac", "roofing contractor"]),
    ("Equipment",     ["equip", "tool", "rental", "machine", "dumpster"]),
]

# ─── MAPEAMENTO: palavras-chave → costCode ────────────────────────────────────
COST_CODE_RULES = [
    ("Doors & Windows",   ["window", "door", "glass", "impact", "slider", "entry"]),
    ("Flooring",          ["floor", "lvp", "laminate", "hardwood", "vinyl plank"]),
    ("Tiling",            ["tile", "ceramic", "porcelain", "grout", "thinset"]),
    ("Painting",          ["paint", "primer", "texture", "popcorn", "ceiling paint"]),
    ("Drywall",           ["drywall", "sheetrock", "mud", "tape", "level 4", "level 5",
                           "orange peel", "knockdown"]),
    ("Electrical",        ["electric", "circuit", "outlet", "panel", "light", "fan",
                           "switch", "wiring"]),
    ("Plumbing",          ["plumb", "pipe", "drain", "faucet", "toilet", "shower valve",
                           "water heater"]),
    ("Roofing",           ["roof", "shingle", "fascia", "soffit", "gutter"]),
    ("Masonry",           ["cement", "block", "masonry", "stucco", "brick", "mortar"]),
    ("Concrete",          ["concrete", "slab", "pour", "grind", "epoxy floor"]),
    ("Framing",           ["frame", "framing", "stud", "header", "partition"]),
    ("Cabinetry",         ["cabinet", "vanity", "millwork"]),
    ("Countertops",       ["counter", "granite", "quartz", "backsplash"]),
    ("Trimwork",          ["baseboard", "molding", "trim", "casing", "crown"]),
    ("Demolition",        ["demo", "demolit", "remov", "tear out", "strip"]),
    ("Insulation",        ["insul", "foam", "batt"]),
    ("Fencing",           ["fence", "fencing"]),
    ("Decking",           ["deck", "patio deck"]),
    ("Pools",             ["pool"]),
    ("Landscaping",       ["landscap", "lawn", "sod", "irrigation", "mulch"]),
    ("Patio Screen",      ["screen", "lanai", "patio screen", "rescree"]),
    ("Staircase",         ["stair", "step", "riser", "nosing"]),
    ("Appliances",        ["appliance", "oven", "refrigerator", "dishwasher",
                           "washer", "dryer", "hood"]),
    ("Mechanical",        ["hvac", "ac", "duct", "vent", "mechanical", "hood"]),
    ("Miscellaneous",     ["maintenance", "repair", "general", "misc", "service",
                           "inspection", "evaluat", "pressure wash"]),
]
