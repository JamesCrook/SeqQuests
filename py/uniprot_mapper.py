
import datetime
import re
from Bio import SwissProt

def _format_date(date_str):
    if not date_str:
        return None
    try:
        # BioPython SwissProt dates are typically 'DD-MMM-YYYY'
        dt = datetime.datetime.strptime(date_str, "%d-%b-%Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return date_str

def map_record_to_json(record: SwissProt.Record):
    """
    Maps a Bio.SwissProt.Record object to a dictionary matching the UniProt JSON API format.
    """

    # 1. Entry Info
    entry_type = "UniProtKB reviewed (Swiss-Prot)" # simplified
    primary_accession = record.accessions[0] if record.accessions else ""
    secondary_accessions = record.accessions[1:] if len(record.accessions) > 1 else []
    uniprot_kb_id = record.entry_name

    # 2. Entry Audit
    # record.created is like ('28-JUN-2011', 0)
    # record.sequence_update is like ('19-JUL-2004', 1)
    # record.annotation_update is like ('09-APR-2025', 45)

    entry_audit = {}
    if record.created:
        entry_audit["firstPublicDate"] = _format_date(record.created[0])
        entry_audit["entryVersion"] = record.created[1]

    if record.sequence_update:
        entry_audit["lastSequenceUpdateDate"] = _format_date(record.sequence_update[0])
        entry_audit["sequenceVersion"] = record.sequence_update[1]

    if record.annotation_update:
        entry_audit["lastAnnotationUpdateDate"] = _format_date(record.annotation_update[0])
        # entryVersion is usually tracked here for the entry itself?
        # UniProt JSON separates entryVersion and sequenceVersion.

    # 3. Organism
    organism = {
        "scientificName": record.organism,
        "commonName": "", # Not always directly available in simple string
        "taxonId": int(record.taxonomy_id[0]) if record.taxonomy_id else 0,
        "lineage": record.organism_classification
    }

    # 4. Description
    # record.description is complex, e.g. "RecName: Full=Putative transcription factor 001R;"
    # We will do a basic parse
    full_name = "Unknown"
    rec_name_match = re.search(r"RecName:\s*Full=([^;]+)", record.description)
    if rec_name_match:
        full_name = rec_name_match.group(1)

    protein_description = {
        "recommendedName": {
            "fullName": {
                "value": full_name
            }
        }
    }

    # 5. Comments
    # record.comments is a list of strings
    comments_json = []
    for c in record.comments:
        # Simple parsing of "TYPE: Text."
        parts = c.split(': ', 1)
        if len(parts) == 2:
            c_type, c_text = parts
            comments_json.append({
                "commentType": c_type,
                "texts": [{"value": c_text}]
            })
        else:
             comments_json.append({
                "commentType": "UNKNOWN",
                "texts": [{"value": c}]
            })

    # 6. Features
    features_json = []
    for f in record.features:
        # f is a SeqFeature
        # location is [start:end]
        # BioPython uses 0-based indexing, UniProt API uses 1-based (usually)
        # But let's check. UniProt JSON "start": {"value": 1}, "end": {"value": 19}
        # BioPython feature.location.start is ExactPosition(0) for 1.

        # We need to handle ExactPosition, etc.
        # simple: start + 1, end

        feat = {
            "type": f.type,
            "location": {
                "start": {"value": int(f.location.start) + 1, "modifier": "EXACT"},
                "end": {"value": int(f.location.end), "modifier": "EXACT"}
            },
            "description": f.qualifiers.get("note", ""),
            "featureId": f.id
        }
        features_json.append(feat)

    # 7. Keywords
    keywords_json = [{"name": k} for k in record.keywords]

    # 8. References
    references_json = []
    for i, ref in enumerate(record.references):
        # ref is a Reference object
        # ref.title, ref.authors, ref.journal, ref.pubmed_id

        # Citations
        citation_refs = []
        if hasattr(ref, 'references'):
            for r_db, r_id in ref.references:
                citation_refs.append({"database": r_db, "id": r_id})

        citation = {
            "title": ref.title,
            "publicationDate": "",
            "authors": ref.authors.split(', ') if ref.authors else [],
            "journal": ref.location,
            "citationType": "journal article",
            "citationCrossReferences": citation_refs
        }

        ref_obj = {
            "referenceNumber": i + 1,
            "citation": citation,
            "referencePositions": ref.positions if hasattr(ref, 'positions') else []
        }
        references_json.append(ref_obj)

    # 9. Cross References
    # record.cross_references is list of tuples ('EMBL', 'AY548484', 'AAT09660.1', '-', 'Genomic_DNA')
    xref_json = []
    for xref in record.cross_references:
        db = xref[0]
        db_id = xref[1]
        props = []
        if len(xref) > 2:
            props.append({"key": "Description", "value": str(xref[2:])})

        xref_json.append({
            "database": db,
            "id": db_id,
            "properties": props
        })

    # 10. Sequence
    # record.seqinfo might have crc64, molweight. In BioPython 1.78+ it is a tuple (length, molecular_weight, crc64)
    mol_weight = 0
    crc64 = ""
    if hasattr(record, 'seqinfo'):
        if isinstance(record.seqinfo, dict):
            mol_weight = record.seqinfo.get('molecular_weight', 0)
            crc64 = record.seqinfo.get('crc64', "")
        elif isinstance(record.seqinfo, tuple) and len(record.seqinfo) >= 3:
            mol_weight = record.seqinfo[1]
            crc64 = record.seqinfo[2]

    sequence_json = {
        "value": record.sequence,
        "length": record.sequence_length,
        "molWeight": mol_weight,
        "crc64": crc64
    }

    # Construct final object
    result = {
        "entryType": entry_type,
        "primaryAccession": primary_accession,
        "secondaryAccessions": secondary_accessions,
        "uniProtkbId": uniprot_kb_id,
        "entryAudit": entry_audit,
        "annotationScore": 0.0, # Placeholder
        "organism": organism,
        "proteinExistence": str(record.protein_existence), # e.g. "1" or "4"
        "proteinDescription": protein_description,
        "comments": comments_json,
        "features": features_json,
        "keywords": keywords_json,
        "references": references_json,
        "uniProtKBCrossReferences": xref_json,
        "sequence": sequence_json,
        "extraAttributes": {
            "uniParcId": "" # Not available
        }
    }

    return result
