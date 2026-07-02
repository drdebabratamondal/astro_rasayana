import re
import pandas as pd
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Botanist")

_STOPWORDS = {
    "induced", "related", "associated", "and", "or", "the", "a", "of", "in",
    "on", "to", "for", "due", "from", "with",
}


def _keywords(phrase: str) -> list[str]:
    return [w for w in re.split(r"[\s\-]+", phrase.lower()) if w and w not in _STOPWORDS]


def _row_matches(clinical_targets: str, target_stressor: str) -> bool:
    if not isinstance(clinical_targets, str):
        return False
    text = clinical_targets.lower()
    phrase = target_stressor.lower()

    # 1. Exact phrase match (best case, keep it fast when it works).
    if phrase in text:
        return True

    # 2. Keyword overlap match -- handles differing terminology between
    #    the preset/custom stressor label and however the CSV author
    #    phrased the clinical_targets column (e.g. "radiation-induced DNA
    #    damage" vs. "DNA repair" or "Radiation protection").
    kws = _keywords(phrase)
    return any(k in text for k in kws)


@mcp.tool()
def filter_rasayana_herbs(csv_path: str, target_stressor: str = "") -> list[dict]:
    """Reads a CSV of Himalayan flora and returns herbs classified as Rasayana.

    If target_stressor is provided, herbs are preferentially filtered to
    those whose clinical_targets field is related to it (exact phrase or
    keyword overlap, case-insensitive). If nothing matches -- which usually
    means the CSV uses different terminology than the requested stressor --
    this falls back to returning all Rasayana herbs, since this CSV field
    is only a coarse pre-filter. The actual relevance check happens
    downstream via live PubMed and NASA GeneLab evidence, which is the
    real Triangulation Mandate gate.
    """
    try:
        df = pd.read_csv(csv_path)
        rasayana_df = df[df['traditional_property'].str.contains('Rasayana', na=False, case=False)]
        columns = ['scientific_name', 'active_compounds', 'clinical_targets']

        if not target_stressor:
            return rasayana_df[columns].to_dict(orient='records')

        mask = rasayana_df['clinical_targets'].apply(lambda t: _row_matches(t, target_stressor))
        filtered_df = rasayana_df[mask]

        if filtered_df.empty:
            print(
                f"[Botanist] No CSV rows matched target '{target_stressor}' by keyword. "
                f"Returning all {len(rasayana_df)} Rasayana herbs for evidence-based triangulation "
                f"instead of stopping early."
            )
            return rasayana_df[columns].to_dict(orient='records')

        return filtered_df[columns].to_dict(orient='records')
    except Exception as e:
        return [{"error": str(e)}]


if __name__ == "__main__":
    mcp.run(transport='stdio')
