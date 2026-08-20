"""Configuration for the NeuroNZ Zotero automation."""

ZOTERO_USER_ID = "21117133"
ZOTERO_API_BASE = "https://api.zotero.org"

COLLECTIONS = {
    "catalogue": {
        "name": "01 Catalogue Sources",
        "key": "VNEB8Z2T",
        "stable_id_field": "NeuroNZ Record ID",
    },
    "evidence": {
        "name": "02 Evidence Log",
        "key": "CI4SRMX3",
        "stable_id_field": "NeuroNZ Evidence ID",
    },
    "taxonomy": {
        "name": "03 Condition Taxonomy",
        "key": "Q3ZM44NE",
        "stable_id_field": "NeuroNZ Condition ID",
    },
}

OUTPUT_DIR = "outputs"

