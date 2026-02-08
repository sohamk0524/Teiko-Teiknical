"""
Part 2: Initial Analysis - Data Overview
Computes relative frequency of each cell population per sample.
"""

import pandas as pd
from database import get_connection, init_and_load, DB_PATH
import os

FREQUENCY_SQL = """
SELECT
    cc.sample_id AS sample,
    totals.total_count,
    cc.population,
    cc.count,
    ROUND(cc.count * 100.0 / totals.total_count, 2) AS percentage
FROM cell_counts cc
JOIN (
    SELECT sample_id, SUM(count) AS total_count
    FROM cell_counts
    GROUP BY sample_id
) totals ON cc.sample_id = totals.sample_id
ORDER BY cc.sample_id, cc.population;
"""


def get_frequency_table(conn):
    """Return a DataFrame with the relative frequency of each cell population per sample."""
    return pd.read_sql_query(FREQUENCY_SQL, conn)


if __name__ == "__main__":
    # Ensure database exists
    if not os.path.exists(DB_PATH):
        conn = init_and_load()
    else:
        conn = get_connection()

    df = get_frequency_table(conn)

    pd.set_option("display.max_rows", 30)
    pd.set_option("display.width", 120)
    print(df)
    print(f"\n{len(df)} rows total ({df['sample'].nunique()} samples x {df['population'].nunique()} populations)")

    output_dir = os.path.join(os.path.dirname(__file__), "outputs")
    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, "frequency_table.csv")
    df.to_csv(csv_path, index=False)
    print(f"Saved to {csv_path}")

    conn.close()
