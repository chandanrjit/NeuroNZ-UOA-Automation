# Metadata and update gap register

Evidence checked on 2 October 2026: GitHub run 36942703891 failed at Zotero PATCH with HTTP 400. Its response body was not logged. Live item 6ESVE4NS remained at version 267, with its original dateModified. The rejected request includes an ISO accessDate with fractional seconds and timezone; this is now formatted as YYYY-MM-DD HH:MM:SS UTC. Confirmation of the rejection cause still requires a pipeline rerun with the improved error logging.

| Gap | Fix and current acceptance status |
|---|---|
| Missing article bibliography | Mapper and fill-only repair implemented; live repair pending. |
| Invalid access date and hidden API response | Timestamp format validated; HTTP response body reported; tests pass. Live rerun pending. |
| Imported articles have no condition links | Existing taxonomy names and reviewed aliases matched against article titles; IDs and tags added during repair. Eight of ten last-run articles match; E041 and E043 need taxonomy review. |
| Search query terms presented as condition classification | Removed; condition_terms now contains actual matched controlled names. |
| Dataset discovery never writes | Public NZ datasets with title, description, organisation, licence, HTTPS resources and controlled condition matches can be imported into Catalogue Sources. Missing facts go to review. Live acceptance pending. |
| Source query failures | CKAN success=false recorded explicitly; discovery failures retained in combined review queue. Prior non-JSON errors need GitHub runner recheck; current direct CKAN probe returned JSON. |
| Repair depends on newest 20 papers | Existing phase2 PMIDs included in source retrieval. Discovery beyond newest 20 still needs a cursor/history strategy. |
| Exports omit bibliography and dates | Cache includes bibliography, condition IDs, dateAdded and dateModified. Catalogue export includes condition IDs. |
| Review queue misses candidate and taxonomy gaps | Combined queue now includes source candidates and per-record metadata/taxonomy gaps. |
| Old success summary uploaded after failed repair | Running/failure summary written with GitHub run ID and error; write manifest retains pending/failed receipts. |
| Duplicate audit lacks match keys | Matched Zotero keys retained for PubMed candidates; DOI conflict blocks repair. Broader metadata conflict review remains. |
| Taxonomy synonyms incomplete | Existing synonyms used; missing synonyms reported. New taxonomy concepts and synonyms require authoritative source review; none invented. |
| Evidence-to-dataset relationships | Missing catalogue relationships reported. Cannot infer that a paper used a dataset merely because their conditions match. |
| Legacy catalogue field gaps | Existing required/filter validation remains; absent type, age and access facts need source verification. |
| WordPress publication | JSON export exists; no live WordPress sync/deployment receipt. Not claimed complete. |
| Operational write gate | Local push and direct repair rejected by malfunctioning automatic approval reviewer (missing outcome). Publication and live acceptance remain blocked until it works. |

Every successful pipeline run produces metadata_taxonomy_audit.json and a combined review_queue.csv. A green job means execution finished; completed_with_review means unresolved data remains. Zero-gap acceptance requires source verification, live write readback, and downstream publication evidence, not only passing unit tests.
