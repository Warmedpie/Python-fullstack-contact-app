from src.data.database import get_connection, _row_to_dict, _rows_to_list

# ---------------------------------------------------------------------
# Contacts table interface
# ---------------------------------------------------------------------

def create_contact(db_path, first_name, last_name=None):
    conn = get_connection(db_path)
    try:
        cursor = conn.execute(
            "INSERT INTO contacts (first_name, last_name) VALUES (?, ?)",
            (first_name, last_name),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def get_contact_by_id(db_path, contact_id):
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM contacts WHERE id = ?", (contact_id,)
        ).fetchone()
        return _row_to_dict(row)
    finally:
        conn.close()

def get_all_contacts(db_path):
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM contacts ORDER BY last_name, first_name"
        ).fetchall()
        return _rows_to_list(rows)
    finally:
        conn.close()

def update_contact(db_path, contact_id, first_name=None, last_name=None):
    conn = get_connection(db_path)
    try:
        conn.execute(
            """
            UPDATE contacts
            SET first_name = COALESCE(?, first_name),
                last_name = COALESCE(?, last_name)
            WHERE id = ?
            """,
            (first_name, last_name, contact_id),
        )
        conn.commit()
        return conn.total_changes > 0
    finally:
        conn.close()

def delete_contact(db_path, contact_id):
    """Deletes the contact along with its emails (cascade)."""
    conn = get_connection(db_path)
    try:
        conn.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
        conn.commit()
        return conn.total_changes > 0
    finally:
        conn.close()
