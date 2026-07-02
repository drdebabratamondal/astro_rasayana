import requests
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("FlightSurgeon")

SEARCH_URL = "https://genelab-data.ndc.nasa.gov/genelab/data/search"


def _genelab_search(term: str, size: int = 3) -> list[dict]:
    params = {"term": term, "type": "cgene", "size": size}
    response = requests.get(SEARCH_URL, params=params, timeout=10)
    response.raise_for_status()
    hits = response.json().get("hits", {}).get("hits", [])
    results = []
    for hit in hits:
        source = hit.get("_source", {})
        accession = source.get("Accession", "Unknown")
        results.append({
            "accession": accession,
            "title": source.get("Project_Title", "Untitled"),
            "url": f"https://osdr.nasa.gov/bio/repo/data/studies/{accession}",
        })
    return results


@mcp.tool()
def search_genelab_biomarkers(stressor: str, herb_name: str = "", active_compound: str = "") -> list[dict]:
    """Queries NASA GeneLab for spaceflight datasets related to a physiological stressor.

    herb_name is used only for traceability so the Supervisor can attribute
    results back to the correct herb.

    NASA GeneLab studies model organisms and astronaut biology in spaceflight,
    not individual phytochemicals, so a compound-specific hit is rare. This
    tool first attempts a compound-specific search when active_compound is
    given. If nothing is found, it falls back to a stressor-level search and
    labels the result 'target_level' rather than 'compound_specific' -- this
    keeps the report honest about what NASA's data actually validates: that
    the physiological target is genuinely perturbed by spaceflight, not that
    the herb itself has been tested in space.
    """
    try:
        if active_compound:
            results = _genelab_search(f"{stressor} {active_compound} microgravity")
            if results:
                for r in results:
                    r["herb_name"] = herb_name
                    r["evidence_tier"] = "compound_specific"
                return results

        results = _genelab_search(f"{stressor} microgravity")
        if not results:
            return [{
                "herb_name": herb_name,
                "status": f"No GeneLab datasets found for {stressor}.",
                "evidence_tier": "none",
            }]

        for r in results:
            r["herb_name"] = herb_name
            r["evidence_tier"] = "target_level"
        return results

    except Exception as e:
        return [{"herb_name": herb_name, "error": str(e)}]


if __name__ == "__main__":
    mcp.run(transport='stdio')
