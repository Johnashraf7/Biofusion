"""
BioFusion AI — Data Fusion Engine
Merges, normalizes, deduplicates, and scores multi-API responses.
"""

import logging
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from config import DATA_DIR

logger = logging.getLogger("biofusion.fusion")

# ─── ICD-10 Local Data ────────────────────────────────────────────────────────

_icd10_data: List[Dict] = []


def load_icd10() -> None:
    """Load ICD-10 codes from local JSON file into memory."""
    global _icd10_data
    icd10_path = DATA_DIR / "icd10_codes.json"
    if icd10_path.exists():
        with open(icd10_path, "r", encoding="utf-8") as f:
            _icd10_data = json.load(f)
        logger.info("Loaded %d ICD-10 codes", len(_icd10_data))
    else:
        logger.warning("ICD-10 data file not found at %s", icd10_path)


def search_icd10(query: str, limit: int = 10) -> List[Dict]:
    """Search ICD-10 codes by tokenized word matching with synonym expansion."""
    if not _icd10_data:
        load_icd10()

    query_lower = query.lower().strip()

    # Synonym expansion for common disease terms
    synonyms = {
        "cancer": ["neoplasm", "malignant", "carcinoma", "tumor", "tumour"],
        "neoplasm": ["cancer", "malignant", "carcinoma"],
        "heart attack": ["myocardial infarction"],
        "stroke": ["cerebral infarction", "hemorrhage"],
        "sugar": ["diabetes", "glucose"],
        "high blood pressure": ["hypertension"],
        "tb": ["tuberculosis"],
        "copd": ["chronic obstructive pulmonary"],
        "ms": ["multiple sclerosis"],
        "als": ["amyotrophic lateral sclerosis", "motor neuron"],
        "lupus": ["systemic lupus erythematosus"],
        "cf": ["cystic fibrosis"],
        "hiv": ["hiv disease"],
        "aids": ["hiv disease"],
        "adhd": ["hyperkinetic", "attention deficit"],
        "autism": ["pervasive developmental"],
        "ptsd": ["severe stress", "post-traumatic"],
        "ocd": ["obsessive-compulsive"],
    }

    # Build expanded search tokens
    tokens = query_lower.split()
    expanded_tokens = set(tokens)

    # Add synonyms for single-word and multi-word queries
    for key, syns in synonyms.items():
        if key in query_lower:
            for syn in syns:
                for word in syn.split():
                    expanded_tokens.add(word)

    results = []
    scored_results = []

    for entry in _icd10_data:
        code = entry.get("code", "").lower()
        desc = entry.get("description", "").lower()
        cat = entry.get("category", "").lower()
        full_text = "{} {} {}".format(code, desc, cat)

        # Exact code match (highest priority)
        if query_lower == code:
            scored_results.append((100, entry))
            continue

        # Full query substring match
        if query_lower in desc or query_lower in cat:
            scored_results.append((80, entry))
            continue

        # Count how many expanded tokens match
        match_count = 0
        for token in expanded_tokens:
            if len(token) >= 2 and token in full_text:
                match_count += 1

        # Require at least half the original tokens to match,
        # or at least 2 expanded tokens
        min_required = max(1, len(tokens) // 2)
        if match_count >= min_required and match_count >= 1:
            score = match_count * 10
            scored_results.append((score, entry))

    # Sort by score descending, take top results
    scored_results.sort(key=lambda x: x[0], reverse=True)
    results = [entry for _, entry in scored_results[:limit]]

    return results


# ─── ID Normalization ──────────────────────────────────────────────────────────


def normalize_gene_id(data: Dict) -> Dict:
    """
    Normalize gene identifiers across different APIs.
    Creates a unified ID mapping from partial data.
    """
    mapping = {
        "gene_symbol": "",
        "ensembl_id": "",
        "uniprot_accession": "",
        "entrez_id": "",
    }

    # Extract from Ensembl data
    if "ensembl_id" in data:
        mapping["ensembl_id"] = data["ensembl_id"]
    if "display_name" in data:
        mapping["gene_symbol"] = data["display_name"]

    # Extract from UniProt data
    if "accession" in data:
        mapping["uniprot_accession"] = data["accession"]
    if "gene_names" in data and data["gene_names"]:
        mapping["gene_symbol"] = data["gene_names"][0]
    if "ensembl_ids" in data and data["ensembl_ids"]:
        mapping["ensembl_id"] = data["ensembl_ids"][0]

    return mapping


# ─── Data Merging ──────────────────────────────────────────────────────────────


def merge_gene_data(
    ensembl_data: Optional[Dict],
    uniprot_data: Optional[Dict],
    opentargets_data: Optional[Dict],
) -> Dict:
    """
    Merge gene data from Ensembl, UniProt, and Open Targets into a unified view.
    """
    merged = {
        "gene_symbol": "",
        "gene_name": "",
        "ensembl_id": "",
        "uniprot_accession": "",
        "description": "",
        "chromosome": "",
        "position": "",
        "biotype": "",
        "protein": {},
        "diseases": [],
        "warnings": [],
    }

    # Ensembl data (primary for genomic info)
    if ensembl_data:
        merged["gene_symbol"] = ensembl_data.get("display_name", "")
        merged["ensembl_id"] = ensembl_data.get("ensembl_id", "")
        merged["description"] = ensembl_data.get("description", "")
        merged["chromosome"] = ensembl_data.get("chromosome", "")
        merged["biotype"] = ensembl_data.get("biotype", "")
        start = ensembl_data.get("start", "")
        end = ensembl_data.get("end", "")
        if start and end:
            merged["position"] = "{}-{}".format(start, end)
    else:
        merged["warnings"].append("Ensembl data unavailable")

    # UniProt data (primary for protein info)
    if uniprot_data:
        merged["uniprot_accession"] = uniprot_data.get("accession", "")
        if not merged["gene_symbol"]:
            names = uniprot_data.get("gene_names", [])
            if names:
                merged["gene_symbol"] = names[0]
        merged["protein"] = {
            "name": uniprot_data.get("protein_name", ""),
            "length": uniprot_data.get("length", 0),
            "functions": uniprot_data.get("functions", []),
            "subcellular_locations": uniprot_data.get("subcellular_locations", []),
            "pdb_ids": uniprot_data.get("pdb_ids", []),
        }
    else:
        merged["warnings"].append("UniProt data unavailable")

    # Open Targets data (primary for disease associations)
    if opentargets_data:
        if not merged["gene_name"]:
            merged["gene_name"] = opentargets_data.get("gene_name", "")
        merged["diseases"] = opentargets_data.get("associations", [])
    else:
        merged["warnings"].append("Open Targets data unavailable")

    return merged


def merge_drug_data(
    chembl_data: Optional[Dict],
    rxnorm_data: Optional[Dict],
    targets: Optional[List[Dict]],
) -> Dict:
    """
    Merge drug data from ChEMBL and RxNorm.
    """
    merged = {
        "drug_name": "",
        "chembl_id": "",
        "rxcui": "",
        "molecule_type": "",
        "max_phase": 0,
        "properties": {},
        "targets": [],
        "synonyms": [],
        "warnings": [],
    }

    # ChEMBL data
    if chembl_data:
        merged["drug_name"] = chembl_data.get("pref_name", "")
        merged["chembl_id"] = chembl_data.get("chembl_id", "")
        merged["molecule_type"] = chembl_data.get("molecule_type", "")
        merged["max_phase"] = chembl_data.get("max_phase", 0)
        merged["properties"] = chembl_data.get("molecule_properties", {})
        merged["synonyms"] = chembl_data.get("synonyms", [])
    else:
        merged["warnings"].append("ChEMBL data unavailable")

    # RxNorm data
    if rxnorm_data:
        merged["rxcui"] = rxnorm_data.get("rxcui", "")
        if not merged["drug_name"]:
            merged["drug_name"] = rxnorm_data.get("name", "")
    else:
        merged["warnings"].append("RxNorm data unavailable")

    # Targets
    if targets:
        merged["targets"] = targets
    else:
        merged["warnings"].append("Drug target data unavailable")

    return merged


def merge_disease_data(
    opentargets_data: Optional[Dict],
    icd10_matches: List[Dict],
    drugs: List[Dict],
) -> Dict:
    """
    Merge disease data from Open Targets with ICD-10 codes.
    """
    merged = {
        "disease_name": "",
        "disease_id": "",
        "description": "",
        "associated_genes": [],
        "known_drugs": [],
        "icd10_codes": icd10_matches,
        "warnings": [],
    }

    if opentargets_data:
        merged["disease_name"] = opentargets_data.get("disease_name", "")
        merged["disease_id"] = opentargets_data.get("disease_id", "")
        merged["description"] = opentargets_data.get("disease_description", "")
        merged["associated_genes"] = opentargets_data.get("targets", [])
    else:
        merged["warnings"].append("Open Targets disease data unavailable")

    merged["known_drugs"] = drugs

    return merged


# ─── Scoring ───────────────────────────────────────────────────────────────────


def score_disease_relevance(association: Dict) -> float:
    """
    Score disease relevance using Open Targets association score.
    Returns 0.0-1.0.
    """
    return float(association.get("overall_score", 0))


def score_variant_risk(variant_data: Dict) -> Dict:
    """
    Score variant risk based on ClinVar + CADD.
    Returns a risk assessment dict.
    """
    risk_level = variant_data.get("risk_level", "uncertain")
    clinvar = variant_data.get("clinvar", {})
    cadd = variant_data.get("cadd_phred", None)

    # Numerical score
    risk_scores = {
        "high": 0.9,
        "moderate": 0.6,
        "low": 0.2,
        "uncertain": 0.5,
    }

    return {
        "risk_level": risk_level,
        "risk_score": risk_scores.get(risk_level, 0.5),
        "clinical_significance": clinvar.get("clinical_significance", "Unknown"),
        "cadd_phred": cadd,
        "evidence_sources": [],
    }


def score_drug_relevance(drug_data: Dict, gene_symbol: str) -> Dict:
    """
    Score drug relevance based on target match.
    """
    targets = drug_data.get("targets", [])
    has_match = False
    matched_target = ""

    for target in targets:
        target_name = target.get("target_name", "").upper()
        target_genes = target.get("target_genes", [])

        if gene_symbol.upper() in target_name:
            has_match = True
            matched_target = target.get("target_name", "")
            break

        for tg in target_genes:
            if gene_symbol.upper() == tg.upper():
                has_match = True
                matched_target = tg
                break

    return {
        "is_relevant": has_match,
        "matched_target": matched_target,
        "relevance_score": 1.0 if has_match else 0.0,
    }


# ─── Deduplication ─────────────────────────────────────────────────────────────


def deduplicate_diseases(diseases: List[Dict]) -> List[Dict]:
    """Remove duplicate disease entries based on disease ID."""
    seen = set()
    unique = []
    for d in diseases:
        did = d.get("disease_id", "") or d.get("disease_name", "")
        if did and did not in seen:
            seen.add(did)
            unique.append(d)
    return unique


def deduplicate_pathways(pathways: List[Dict]) -> List[Dict]:
    """Remove duplicate pathway entries."""
    seen = set()
    unique = []
    for p in pathways:
        pid = p.get("pathway_id", "") or p.get("kegg_pathway_id", "") or p.get("name", "")
        if pid and pid not in seen:
            seen.add(pid)
            unique.append(p)
    return unique


# ─── Query Type Detection ─────────────────────────────────────────────────────


def detect_query_type(query: str) -> str:
    """
    Auto-detect query type from the input string.
    Returns: "gene", "variant", "drug", "disease"
    """
    q = query.strip().lower()

    # 1. Variant patterns (highest specificity)
    if q.startswith("rs") and q[2:].isdigit():
        return "variant"
    if q.startswith("chr") and (":" in q or "g." in q):
        return "variant"
    if any(x in q for x in [">", "del", "ins", "dup"]):
        # HGVSc / HGVSp candidates
        return "variant"

    # 2. Specific IDs
    if q.startswith("chembl"):
        return "drug"
    if q.startswith("ensg"):
        return "gene"
    if q.startswith("efo_") or q.startswith("mondo_") or q.startswith("hp_"):
        return "disease"
    if q.startswith("uniprot:"):
        return "gene"

    # 3. Disease Keywords (commonly searched diseases)
    disease_keywords = [
        "cancer", "diabetes", "syndrome", "fever", "pain", "infection",
        "virus", "flu", "cold", "asthma", "disease", "carcinoma", "lymphoma",
        "leukemia", "sclerosis", "alzheimer", "parkinson", "dementia",
        "arrhythmia", "anemia", "hepatitis", "arthritis", "lupus", "stroke",
        "autism", "epilepsy", "migraine", "malaria", "tuberculosis", "aids",
        "hiv", "covid", "tumor", "neoplasm", "cyst", "adenoma", "sarcoma",
        "melanoma", "glioma", "fibrosis", "dystrophy", "psoriasis",
    ]
    if any(keyword in q for keyword in disease_keywords):
        return "disease"

    # 4. Drug Suffixes & Keywords
    drug_suffixes = [
        "mab", "nib", "ib", "ide", "cin", "mycin", "pril",
        "sartan", "olol", "pine", "zine", "statin", "cillin",
        "navir", "tidine", "prazole", "dronate", "setron",
    ]
    drug_keywords = [
        "aspirin", "tylenol", "paracetamol", "ibuprofen", "advil", "motrin",
        "panadol", "viagra", "lipitor", "humira", "nexium", "plavix", "rituxan",
        "herceptin", "avastin", "remicade", "lantus", "enbrel", "adderall",
        "xanax", "prozac", "zoloft", "lexapro", "ambien", "valium",
    ]
    if any(q.endswith(suffix) for suffix in drug_suffixes):
        return "drug"
    if any(keyword in q for keyword in drug_keywords):
        return "drug"

    # 5. Multi-word strings are rarely just a gene symbol
    if " " in q:
        # Check if it could be a disease or drug (heuristic)
        return "disease"

    # Default to gene (most common bioinfo query)
    return "gene"


# ─── Synthesis Prompt Generation ──────────────────────────────────────────────


def generate_gene_synthesis_prompt(data: Dict) -> str:
    """Generate a prompt for AI synthesis of gene data."""
    symbol = data.get("gene_symbol", "this gene")
    name = data.get("gene_name", "")
    desc = data.get("description", "")
    protein = data.get("protein", {})
    diseases = data.get("diseases", [])[:10]

    diseases_str = ", ".join([d.get("disease_name", "Unknown") for d in diseases])

    prompt = (
        f"Synthesize a brief, professional clinical insight for the gene {symbol} ({name}).\n"
        f"Description: {desc}\n"
        f"Protein: {protein.get('name', 'N/A')}. "
        f"Function: {', '.join(protein.get('functions', []))}\n"
        f"Associated Diseases: {diseases_str}\n\n"
        "Provide a 3-sentence summary highlighting its primary biological role and clinical significance."
    )
    return prompt


def generate_drug_synthesis_prompt(data: Dict) -> str:
    """Generate a prompt for AI synthesis of drug data."""
    name = data.get("drug_name", "this drug")
    targets = data.get("targets", [])[:5]
    targets_str = ", ".join([t.get("target_name", "Unknown") for t in targets])

    prompt = (
        f"Synthesize a brief clinical profile for the drug {name}.\n"
        f"Molecule Type: {data.get('molecule_type', 'N/A')}. "
        f"Max Clinical Phase: {data.get('max_phase', 0)}.\n"
        f"Primary Targets: {targets_str}\n\n"
        "What is the mechanism of action and the primary therapeutic focus for this drug? (2-3 sentences)"
    )
    return prompt


def generate_disease_synthesis_prompt(data: Dict) -> str:
    """Generate a prompt for AI synthesis of disease data."""
    name = data.get("disease_name", "this disease")
    desc = data.get("description", "")
    genes = data.get("associated_genes", [])[:10]
    genes_str = ", ".join([g.get("gene_symbol", "Unknown") for g in genes])

    prompt = (
        f"Synthesize a summary for the disease {name}.\n"
        f"Clinical Description: {desc}\n"
        f"Top Associated Genes: {genes_str}\n\n"
        "Summarize the pathophysiology and key genetic drivers of this condition. (2-3 sentences)"
    )
    return prompt
