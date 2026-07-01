import requests
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("FlightSurgeon")

@mcp.tool()
def search_genelab_biomarkers(stressor: str) -> list[dict]:
    """Queries NASA GeneLab for spaceflight datasets related to a physiological stressor."""
    try:
        # Using the public NASA GeneLab Search API
        search_url = "https://genelab-data.ndc.nasa.gov/genelab/data/search"
        
        # Searching for terms related to the stressor and spaceflight environments
        params = {
            "term": f"{stressor} microgravity",
            "type": "cgene",
            "size": 3
        }
        
        response = requests.get(search_url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        hits = data.get("hits", {}).get("hits", [])
        
        if not hits:
            return [{"status": f"No GeneLab datasets found for {stressor}."}]
            
        results = []
        for hit in hits:
            source = hit.get("_source", {})
            accession = source.get("Accession", "Unknown")
            results.append({
                "accession": accession,
                "title": source.get("Project_Title", "Untitled"),
                "url": f"https://osdr.nasa.gov/bio/repo/data/studies/{accession}"
            })
            
        return results
        
    except Exception as e:
        return [{"error": str(e)}]

if __name__ == "__main__":
    mcp.run(transport='stdio')