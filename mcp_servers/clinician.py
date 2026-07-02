import requests
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Clinician")

ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
ESUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"


def _pubmed_search(query: str, retmax: int = 3) -> list[str]:
    params = {"db": "pubmed", "term": query, "retmode": "json", "retmax": retmax}
    response = requests.get(ESEARCH_URL, params=params, timeout=10)
    response.raise_for_status()
    return response.json().get("esearchresult", {}).get("idlist", [])


def _pubmed_titles(pmids: list[str]) -> dict[str, str]:
    if not pmids:
        return {}
    params = {"db": "pubmed", "id": ",".join(pmids), "retmode": "json"}
    response = requests.get(ESUMMARY_URL, params=params, timeout=10)
    response.raise_for_status()
    result = response.json().get("result", {})
    return {pmid: result.get(pmid, {}).get("title", "Untitled") for pmid in pmids}


@mcp.tool()
def search_pubmed_clinical_trials(herb_name: str, active_compound: str, clinical_target: str) -> list[dict]:
    """Queries PubMed for evidence linking a compound to a clinical target.

    herb_name is used only for traceability so the Supervisor can attribute
    results back to the correct herb regardless of how the compound name is
    phrased in the query itself. It is not used to build the search query.

    The search first tries a strict query restricted to Clinical Trial
    publication types. If nothing is found, it falls back to a broader
    search and labels the evidence_tier as 'preclinical_or_review' rather
    than 'clinical_trial', so downstream reporting never overstates the
    strength of the evidence.
    """
    try:
        strict_query = (
            f"{active_compound}[Title/Abstract] AND {clinical_target}[Title/Abstract] "
            f"AND Clinical Trial[Publication Type]"
        )
        pmids = _pubmed_search(strict_query)
        evidence_tier = "clinical_trial"

        if not pmids:
            broad_query = f"{active_compound}[Title/Abstract] AND {clinical_target}[Title/Abstract]"
            pmids = _pubmed_search(broad_query)
            evidence_tier = "preclinical_or_review"

        if not pmids:
            return [{"herb_name": herb_name, "status": "No PubMed evidence found.", "evidence_tier": "none"}]

        titles = _pubmed_titles(pmids)
        return [
            {
                "herb_name": herb_name,
                "pubmed_id": pmid,
                "title": titles.get(pmid, "Untitled"),
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                "evidence_tier": evidence_tier,
            }
            for pmid in pmids
        ]

    except Exception as e:
        return [{"herb_name": herb_name, "error": str(e)}]


if __name__ == "__main__":
    mcp.run(transport='stdio')
