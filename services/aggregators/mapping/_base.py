from typing import NamedTuple, Optional


class FieldDef(NamedTuple):
    source:            str            # Logischer Quellenname (via SOURCE_MAPPING)
    category:          str            # Regex für category-Spalte (".*" = beliebig)
    pattern:           str            # Regex für parameter-Spalte
    validation:        str            # REDCap-Validierungstyp
    min_val:           Optional[str]   = None   # REDCap-Validierung min
    max_val:           Optional[str]   = None   # REDCap-Validierung max
    conversion_factor: Optional[float] = None   # Quelldaten × factor = REDCap-Wert (z.B. 0.1 für g/L→g/dL)
