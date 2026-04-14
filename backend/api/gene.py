"""
BioFusion AI — Gene API Route
Full gene report with protein info, disease associations, and pathways.
"""

import asyncio
import logging
from typing import Optional

from fastapi import APIRouter, Query

from cache_manager import cache
from fusion_engine import merge_gene_data, deduplicate_diseases, deduplicate_pathways
from services import ensembl, uniprot, opentargets, reactome, kegg

logger = logging.getLogger("biofusion.api.gene")

router = APIRouter()


@router.get("/{gene_id}")
async def get_gene(
    gene_id: str,
    include: Optional[str] = Query(None, description="Comma-separated extras: pathways,kegg"),
):
    """
    Get comprehensive gene report.
    
    Args:
        gene_id: Gene symbol (e.g., TP53) or Ensembl ID (e.g., ENSG00000141510)
        include: Optional extras to load (pathways, kegg)
    """
    # Check cache
    cached = cache.get("gene", gene_id)
    if cached:
        return cached

    is_ensembl_id = gene_id.upper().startswith("ENSG")
    # UniProt accession pattern: 1 letter + 5 alphanumerics (e.g., P38398, A0A2R8Y7V5)
    is_uniprot = (not is_ensembl_id and len(gene_id) >= 6
                  and gene_id[0].isalpha() and gene_id[1:].replace("_", "").isalnum()
                  and not gene_id.upper().startswith("EFO")
                  and not gene_id.upper().startswith("MONDO")
                  and any(c.isdigit() for c in gene_id))
    warnings = []

    if is_uniprot:
        # Direct UniProt accession — fetch protein details first
        uniprot_data = None
        try:
            uniprot_data = await uniprot.get_protein(gene_id)
        except Exception as e:
            warnings.append("UniProt protein detail failed")

        # Resolve gene symbol from UniProt data to look up in Ensembl
        gene_symbol = ""
        if uniprot_data and uniprot_data.get("gene_names"):
            gene_symbol = uniprot_data["gene_names"][0]

        ensembl_data = None
        if gene_symbol:
            try:
                ensembl_data = await ensembl.lookup_gene(gene_symbol)
            except Exception:
                warnings.append("Ensembl lookup failed for {}".format(gene_symbol))

        # Resolve Ensembl ID for Open Targets
        ens_id = ""
        if ensembl_data and isinstance(ensembl_data, dict):
            ens_id = ensembl_data.get("ensembl_id", "")

        uniprot_results = []  # Not needed, we already have uniprot_data

    else:
        # Phase 1: Core data
        if is_ensembl_id:
            # For Ensembl IDs, fetch Ensembl first to get gene symbol
            try:
                ensembl_data = await ensembl.get_gene_by_id(gene_id)
            except Exception as e:
                warnings.append("Ensembl lookup failed: {}".format(str(e)))
                ensembl_data = None

            # Use resolved gene symbol for UniProt search (not Ensembl ID)
            gene_symbol_for_uniprot = ""
            if ensembl_data and isinstance(ensembl_data, dict):
                gene_symbol_for_uniprot = ensembl_data.get("display_name", "")

            uniprot_results = []
            if gene_symbol_for_uniprot:
                try:
                    uniprot_results = await uniprot.search_gene(gene_symbol_for_uniprot, limit=1)
                except Exception as e:
                    warnings.append("UniProt lookup failed: {}".format(str(e)))
            else:
                warnings.append("Could not resolve gene symbol for UniProt search")
        else:
            # For gene symbols, query both in parallel
            ensembl_task = ensembl.lookup_gene(gene_id)
            uniprot_task = uniprot.search_gene(gene_id, limit=1)

            ensembl_data, uniprot_results = await asyncio.gather(
                ensembl_task, uniprot_task, return_exceptions=True,
            )

            # Handle errors
            if isinstance(ensembl_data, Exception):
                warnings.append("Ensembl lookup failed: {}".format(str(ensembl_data)))
                ensembl_data = None
            if isinstance(uniprot_results, Exception):
                warnings.append("UniProt lookup failed: {}".format(str(uniprot_results)))
                uniprot_results = []

        # Get UniProt details if we have a result
        uniprot_data = None
        if uniprot_results and isinstance(uniprot_results, list) and len(uniprot_results) > 0:
            accession = uniprot_results[0].get("accession", "")
            if accession:
                try:
                    uniprot_data = await uniprot.get_protein(accession)
                except Exception as e:
                    warnings.append("UniProt protein detail failed")

        # Resolve Ensembl ID for Open Targets
        ens_id = gene_id if is_ensembl_id else ""
        if not ens_id and ensembl_data and isinstance(ensembl_data, dict):
            ens_id = ensembl_data.get("ensembl_id", "")

    # Phase 2: Disease associations (requires Ensembl ID)
    opentargets_data = None
    if ens_id:
        try:
            opentargets_data = await opentargets.get_disease_associations(ens_id, limit=15)
        except Exception as e:
            warnings.append("Open Targets lookup failed")

    # Merge core data
    merged = merge_gene_data(ensembl_data, uniprot_data, opentargets_data)
    merged["warnings"].extend(warnings)

    # Phase 3: Pathways (lazy loaded on request)
    include_set = set()
    if include:
        include_set = {x.strip().lower() for x in include.split(",")}

    if "pathways" in include_set or "all" in include_set:
        gene_symbol = merged.get("gene_symbol", gene_id)
        pathway_tasks = [reactome.get_pathways(gene_symbol)]
        results = await asyncio.gather(*pathway_tasks, return_exceptions=True)

        reactome_data = results[0]
        if isinstance(reactome_data, list):
            merged["pathways_reactome"] = reactome_data
        else:
            merged["pathways_reactome"] = []
            merged["warnings"].append("Reactome pathways failed")

    if "kegg" in include_set or "all" in include_set:
        gene_symbol = merged.get("gene_symbol", gene_id)
        try:
            kegg_genes = await kegg.search_gene(gene_symbol)
            if kegg_genes:
                kegg_id = kegg_genes[0].get("kegg_id", "")
                if kegg_id:
                    kegg_pathways = await kegg.get_gene_pathways(kegg_id)
                    merged["pathways_kegg"] = kegg_pathways
                else:
                    merged["pathways_kegg"] = []
            else:
                merged["pathways_kegg"] = []
        except Exception:
            merged["pathways_kegg"] = []
            merged["warnings"].append("KEGG pathways failed")

    # Deduplicate
    if "diseases" in merged:
        merged["diseases"] = deduplicate_diseases(merged["diseases"])

    # Cache result
    cache.set("gene", gene_id, merged)

    return merged
