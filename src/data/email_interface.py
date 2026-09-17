from src.data.database import get_connection, _rows_to_list

# ---------------------------------------------------------------------
# Email table interface
# ---------------------------------------------------------------------

def add_contact_email(db_path, contact_id, email):
    conn = get_connection(db_path)
    try:
        cursor = conn.execute(
            "INSERT INTO contact_emails (contact_id, email) VALUES (?, ?)",
            (contact_id, email),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def get_contact_emails(db_path, contact_id):
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM contact_emails WHERE contact_id = ? ORDER BY id",
            (contact_id,),
        ).fetchall()
        return _rows_to_list(rows)
    finally:
        conn.close()

def delete_contact_email(db_path, email_id):
    conn = get_connection(db_path)
    try:
        conn.execute(
            "DELETE FROM contact_emails WHERE id = ?", (email_id,)
        )
        conn.commit()
        return conn.total_changes > 0
    finally:
        conn.close()
