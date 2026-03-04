from typing import NamedTuple


class FieldDef(NamedTuple):
    source:     str            # Logischer Quellenname (via SOURCE_MAPPING)
    category:   str            # Regex für category-Spalte (".*" = beliebig)
    pattern:    str            # Regex für parameter-Spalte
    validation: str            # REDCap-Validierungstyp
