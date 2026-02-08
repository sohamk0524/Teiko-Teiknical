"""
Part 1: Data Management
- Relational database schema using SQLite
- Loading function to initialize the database and load data from cell-count.csv
"""

import sqlite3
import csv
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "clinical_trial.db")
CSV_PATH = os.path.join(os.path.dirname(__file__), "cell-count.csv")

CELL_POPULATIONS = ["b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"]

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS subjects (
    subject_id TEXT PRIMARY KEY,
    condition TEXT NOT NULL,
    age INTEGER NOT NULL,
    sex TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS samples (
    sample_id TEXT PRIMARY KEY,
    subject_id TEXT NOT NULL,
    project TEXT NOT NULL,
    treatment TEXT NOT NULL,
    response TEXT NOT NULL,
    sample_type TEXT NOT NULL,
    time_from_treatment_start INTEGER NOT NULL,
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
);

CREATE TABLE IF NOT EXISTS cell_counts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sample_id TEXT NOT NULL,
    population TEXT NOT NULL,
    count INTEGER NOT NULL,
    FOREIGN KEY (sample_id) REFERENCES samples(sample_id),
    UNIQUE(sample_id, population)
);
"""


def get_connection(db_path=DB_PATH):
    """Return a connection to the SQLite database."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn):
    """Create the database tables."""
    conn.executescript(SCHEMA_SQL)
    conn.commit()


def load_csv(conn, csv_path=CSV_PATH):
    """Load all rows from cell-count.csv into the database."""
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)

        subjects_seen = set()
        samples_seen = set()

        for row in reader:
            subject_id = row["subject"]
            sample_id = row["sample"]

            # Insert subject if not already inserted
            if subject_id not in subjects_seen:
                conn.execute(
                    "INSERT OR IGNORE INTO subjects (subject_id, condition, age, sex) VALUES (?, ?, ?, ?)",
                    (subject_id, row["condition"], int(row["age"]), row["sex"]),
                )
                subjects_seen.add(subject_id)

            # Insert sample if not already inserted
            if sample_id not in samples_seen:
                conn.execute(
                    "INSERT OR IGNORE INTO samples (sample_id, subject_id, project, treatment, response, sample_type, time_from_treatment_start) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        sample_id,
                        subject_id,
                        row["project"],
                        row["treatment"],
                        row["response"],
                        row["sample_type"],
                        int(row["time_from_treatment_start"]),
                    ),
                )
                samples_seen.add(sample_id)

            # Insert cell counts (one row per population)
            for population in CELL_POPULATIONS:
                conn.execute(
                    "INSERT OR IGNORE INTO cell_counts (sample_id, population, count) VALUES (?, ?, ?)",
                    (sample_id, population, int(row[population])),
                )

        conn.commit()


def init_and_load(db_path=DB_PATH, csv_path=CSV_PATH):
    """Initialize the database schema and load the CSV data. Returns the connection."""
    conn = get_connection(db_path)
    init_db(conn)
    load_csv(conn, csv_path)
    return conn


if __name__ == "__main__":
    # Remove existing DB to start fresh
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = init_and_load()

    # Verify the load
    subject_count = conn.execute("SELECT COUNT(*) FROM subjects").fetchone()[0]
    sample_count = conn.execute("SELECT COUNT(*) FROM samples").fetchone()[0]
    cell_count_rows = conn.execute("SELECT COUNT(*) FROM cell_counts").fetchone()[0]

    print(f"Loaded {subject_count} subjects, {sample_count} samples, {cell_count_rows} cell count records.")
    conn.close()
