"""
BioFusion AI — UniProt Service Client
Query UniProt for protein information by gene name or accession.
"""

import logging
from typing import Any, Dict, List, Optional

from config import API_URLS
from services.base_client import http_client

logger = logging.getLogger("biofusion.services.uniprot")

BASE_URL = API_URLS["uniprot"]


async def search_gene(gene_name: str, organism: str = "human", limit: int = 5) -> List[Dict]:
    """
    Search UniProt for a gene by name.
    Returns a list of matching protein entries.
    """
    url = "{}/uniprotkb/search".format(BASE_URL)
    query = "(gene:{}) AND (organism_name:{}) AND (reviewed:true)".format(gene_name, organism)
    params = {
        "query": query,
        "format": "json",
        "size": str(limit),
        "fields": "accession,id,gene_names,protein_name,organism_name,length,sequence",
    }

    data = await http_client.fetch_json("uniprot", url, params=params)
    if not data or "results" not in data:
        return []

    results = []
    for entry in data.get("results", []):
        protein_name = ""
        if "proteinDescription" in entry:
            rec = entry["proteinDescription"].get("recommendedName", {})
            if rec:
                protein_name = rec.get("fullName", {}).get("value", "")
            elif entry["proteinDescription"].get("submissionNames"):
                protein_name = entry["proteinDescription"]["submissionNames"][0].get("fullName", {}).get("value", "")

        gene_symbols = []
        for gene in entry.get("genes", []):
            if "geneName" in gene:
                gene_symbols.append(gene["geneName"].get("value", ""))

        results.append({
            "accession": entry.get("primaryAccession", ""),
            "entry_id": entry.get("uniProtkbId", ""),
            "gene_names": gene_symbols,
            "protein_name": protein_name,
            "organism": entry.get("organism", {}).get("scientificName", ""),
            "length": entry.get("sequence", {}).get("length", 0),
        })

    logger.info("UniProt search for '%s': %d results", gene_name, len(results))
    return results


async def get_protein(accession: str) -> Optional[Dict]:
    """
    Get full protein details by UniProt accession (e.g., P04637).
    """
    url = "{}/uniprotkb/{}".format(BASE_URL, accession)
    params = {"format": "json"}

    data = await http_client.fetch_json("uniprot", url, params=params)
    if not data:
        return None

    # Extract key information
    protein_name = ""
    if "proteinDescription" in data:
        rec = data["proteinDescription"].get("recommendedName", {})
        if rec:
            protein_name = rec.get("fullName", {}).get("value", "")

    gene_symbols = []
    for gene in data.get("genes", []):
        if "geneName" in gene:
            gene_symbols.append(gene["geneName"].get("value", ""))

    # Extract function annotations
    functions = []
    for comment in data.get("comments", []):
        if comment.get("commentType") == "FUNCTION":
            for text in comment.get("texts", []):
                functions.append(text.get("value", ""))

    # Extract subcellular location
    locations = []
    for comment in data.get("comments", []):
        if comment.get("commentType") == "SUBCELLULAR LOCATION":
            for loc in comment.get("subcellularLocations", []):
                loc_val = loc.get("location", {}).get("value", "")
                if loc_val:
                    locations.append(loc_val)

    # Extract cross-references (for ID mapping)
    ensembl_ids = []
    pdb_ids = []
    for xref in data.get("uniProtKBCrossReferences", []):
        if xref.get("database") == "Ensembl":
            ensembl_ids.append(xref.get("id", ""))
        elif xref.get("database") == "PDB":
            pdb_ids.append(xref.get("id", ""))

    result = {
        "accession": data.get("primaryAccession", ""),
        "entry_id": data.get("uniProtkbId", ""),
        "gene_names": gene_symbols,
        "protein_name": protein_name,
        "organism": data.get("organism", {}).get("scientificName", ""),
        "length": data.get("sequence", {}).get("length", 0),
        "functions": functions,
        "subcellular_locations": locations,
        "ensembl_ids": ensembl_ids,
        "pdb_ids": pdb_ids[:5],  # Limit PDB IDs
        "sequence": data.get("sequence", {}).get("value", "")[:100] + "...",  # First 100 AA
    }

    logger.info("UniProt protein fetched: %s (%s)", accession, protein_name)
    return result
