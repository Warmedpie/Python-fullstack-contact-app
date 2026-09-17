import re

from src.data import contact_interface as contact_data
from src.data import email_interface as email_data
from src.service.exceptions import NotFoundError, ValidationError

#Email REGEX for validation
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _ensure_contact_exists(db_path, contact_id):
    if contact_data.get_contact_by_id(db_path, contact_id) is None:
        raise NotFoundError(f"Contact {contact_id} not found")

def _validate_email(email):
    if not email or not _EMAIL_RE.match(email.strip()):
        raise ValidationError(f"{email!r} is not a valid email address")

def list_emails_for_contact(db_path, contact_id):
    _ensure_contact_exists(db_path, contact_id)
    return email_data.get_contact_emails(db_path, contact_id)

def add_email(db_path, contact_id, email):
    _ensure_contact_exists(db_path, contact_id)
    _validate_email(email)

    new_id = email_data.add_contact_email(db_path, contact_id, email.strip())
    return {
        "id": new_id,
        "contact_id": contact_id,
        "email": email.strip(),
    }

def remove_email(db_path, email_id):
    deleted = email_data.delete_contact_email(db_path, email_id)
    if not deleted:
        raise NotFoundError(f"Email {email_id} not found")
