import requests
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Clinician")

@mcp.tool()
def search_pubmed_clinical_trials(active_compound: str, clinical_target: str) -> list[dict]:
    """Queries the PubMed API for clinical trials matching the active compound and target."""
    try:
        query = f"{active_compound}[Title/Abstract] AND {clinical_target}[Title/Abstract]"
        search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        
        params = {
            "db": "pubmed",
            "term": query,
            "retmode": "json",
            "retmax": 3
        }
        
        response = requests.get(search_url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        id_list = data.get("esearchresult", {}).get("idlist", [])
        
        if not id_list:
            return [{"status": "No clinical trials found."}]
            
        return [{"pubmed_id": pmid, "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"} for pmid in id_list]
        
    except Exception as e:
        return [{"error": str(e)}]

if __name__ == "__main__":
    mcp.run(transport='stdio')