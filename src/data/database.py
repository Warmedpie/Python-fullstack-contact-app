import sqlite3


def get_connection(db_path):
    """Return a new SQLite connection with row access by column name."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def _row_to_dict(row):
    return dict(row) if row is not None else None

def _rows_to_list(rows):
    return [dict(r) for r in rows]

def init_db(db_path):
    """Create tables (and indexes) if they don't exist yet.

    Safe to call every time the app starts.
    """

    # Contact table
    #
    # Contact table will be One to Many with email_table; One contact can own many emails, as such reference to this table will belong with email_table
    #
    # id           | int (auto increment)
    # first_name   | text
    # last_name    | text
    contact_table = """
                        CREATE TABLE IF NOT EXISTS contacts (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            first_name TEXT NOT NULL,
                            last_name TEXT
                        );
                    """

    # Email table
    #
    # Email table will be Many to One with Contact Table; Many emails can be associated to a single contact, as such contact_id gets refferenced within this table
    #
    # id           | int (auto increment)
    # contact_id   | int (Foreign key)
    # email        | text
    email_table = """
                        CREATE TABLE IF NOT EXISTS contact_emails (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            contact_id INTEGER NOT NULL
                                REFERENCES contacts (id) ON DELETE CASCADE,
                            email TEXT NOT NULL
                        );
                  """

    idx_contact_emails_contact_id = """
                                        CREATE INDEX IF NOT EXISTS idx_contact_emails_contact_id
                                        ON contact_emails (contact_id);
                                    """

    conn = get_connection(db_path)

    try:
        #Create contact_table if not exist
        conn.executescript(contact_table)
        #Create email_table if not exist
        conn.executescript(email_table)
        #Create idx_contact_emails_contact_id if not exist
        conn.executescript(idx_contact_emails_contact_id)

        conn.commit()
    finally:
        conn.close()
