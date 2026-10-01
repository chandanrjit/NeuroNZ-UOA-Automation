"""Configuration for the NeuroNZ Zotero automation."""

ZOTERO_LIBRARY_TYPE = "groups"
ZOTERO_LIBRARY_ID = "6643086"
ZOTERO_COLLECTION_KEY = "PA2ESN45"
ZOTERO_API_BASE = "https://api.zotero.org"

COLLECTIONS = {
    "catalogue": {
        "name": "01 Catalogue Sources",
        "stable_id_field": "NeuroNZ Record ID",
    },
    "evidence": {
        "name": "02 Evidence Log",
        "stable_id_field": "NeuroNZ Evidence ID",
    },
    "taxonomy": {
        "name": "03 Condition Taxonomy",
        "stable_id_field": "NeuroNZ Condition ID",
    },
}

OUTPUT_DIR = "outputs"
