import pandas as pd
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Botanist")

@mcp.tool()
def filter_rasayana_herbs(csv_path: str) -> list[dict]:
    """Reads a CSV of Himalayan flora and returns herbs classified as Rasayana."""
    try:
        df = pd.read_csv(csv_path)
        rasayana_df = df[df['traditional_property'].str.contains('Rasayana', na=False, case=False)]
        return rasayana_df[['scientific_name', 'active_compounds', 'clinical_targets']].to_dict(orient='records')
    except Exception as e:
        return [{"error": str(e)}]

if __name__ == "__main__":
    mcp.run(transport='stdio')