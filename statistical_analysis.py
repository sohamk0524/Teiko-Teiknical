"""
Part 3: Statistical Analysis
- Compare cell population relative frequencies: responders vs non-responders
  (melanoma, miraclib, PBMC samples only)
- Boxplot visualization per cell population
- Report statistically significant differences (Mann-Whitney U test)
"""

import os
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt

from database import get_connection, init_and_load, DB_PATH

# Query: frequency table filtered to melanoma + miraclib + PBMC
FILTERED_FREQUENCY_SQL = """
SELECT
    cc.sample_id AS sample,
    s.response,
    cc.population,
    ROUND(cc.count * 100.0 / totals.total_count, 2) AS percentage
FROM cell_counts cc
JOIN samples s ON cc.sample_id = s.sample_id
JOIN subjects sub ON s.subject_id = sub.subject_id
JOIN (
    SELECT sample_id, SUM(count) AS total_count
    FROM cell_counts
    GROUP BY sample_id
) totals ON cc.sample_id = totals.sample_id
WHERE sub.condition = 'melanoma'
  AND s.treatment = 'miraclib'
  AND s.sample_type = 'PBMC'
ORDER BY cc.sample_id, cc.population;
"""


def get_filtered_frequency(conn):
    """Return frequency table for melanoma/miraclib/PBMC samples."""
    return pd.read_sql_query(FILTERED_FREQUENCY_SQL, conn)


def run_statistical_tests(df):
    """Run Mann-Whitney U tests comparing responders vs non-responders for each population.

    Returns a DataFrame with population, U-statistic, p-value, and significance flag.
    """
    populations = sorted(df["population"].unique())
    results = []

    for pop in populations:
        pop_data = df[df["population"] == pop]
        responders = pop_data[pop_data["response"] == "yes"]["percentage"]
        non_responders = pop_data[pop_data["response"] == "no"]["percentage"]

        stat, p_value = stats.mannwhitneyu(responders, non_responders, alternative="two-sided")

        results.append({
            "population": pop,
            "responder_median": round(responders.median(), 2),
            "non_responder_median": round(non_responders.median(), 2),
            "U_statistic": stat,
            "p_value": round(p_value, 6),
            "significant (p<0.05)": "Yes" if p_value < 0.05 else "No",
        })

    return pd.DataFrame(results)


def create_boxplot(df, output_path="boxplot_responders_vs_nonresponders.png"):
    """Create boxplots comparing responders vs non-responders for each cell population."""
    populations = sorted(df["population"].unique())

    fig, axes = plt.subplots(1, len(populations), figsize=(4 * len(populations), 6), sharey=False)

    for ax, pop in zip(axes, populations):
        pop_data = df[df["population"] == pop]
        resp = pop_data[pop_data["response"] == "yes"]["percentage"]
        non_resp = pop_data[pop_data["response"] == "no"]["percentage"]

        bp = ax.boxplot(
            [non_resp, resp],
            tick_labels=["Non-responder", "Responder"],
            patch_artist=True,
            widths=0.6,
        )
        bp["boxes"][0].set_facecolor("#e74c3c")
        bp["boxes"][1].set_facecolor("#2ecc71")

        ax.set_title(pop.replace("_", " ").title(), fontsize=12, fontweight="bold")
        ax.set_ylabel("Relative Frequency (%)")

    fig.suptitle(
        "Cell Population Frequencies: Responders vs Non-Responders\n(Melanoma, Miraclib, PBMC)",
        fontsize=14,
        fontweight="bold",
    )
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Boxplot saved to {output_path}")


if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        conn = init_and_load()
    else:
        conn = get_connection()

    # Get filtered data
    df = get_filtered_frequency(conn)
    print(f"Filtered dataset: {len(df)} rows, {df['sample'].nunique()} samples\n")

    # Statistical tests
    results = run_statistical_tests(df)
    pd.set_option("display.width", 120)
    print("=== Statistical Comparison: Responders vs Non-Responders ===\n")
    print(results.to_string(index=False))

    sig = results[results["significant (p<0.05)"] == "Yes"]
    print(f"\n{len(sig)} of {len(results)} populations show a significant difference (p < 0.05).")
    if not sig.empty:
        print("Significant populations:", ", ".join(sig["population"].tolist()))

    # Boxplot
    output_dir = os.path.join(os.path.dirname(__file__), "outputs")
    os.makedirs(output_dir, exist_ok=True)
    create_boxplot(df, output_path=os.path.join(output_dir, "boxplot_responders_vs_nonresponders.png"))

    conn.close()
