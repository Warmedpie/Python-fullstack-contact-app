from src.data import contact_interface as contact_data
from src.service.exceptions import NotFoundError, ValidationError


def list_contacts(db_path):
    return contact_data.get_all_contacts(db_path)

def get_contact(db_path, contact_id):
    contact = contact_data.get_contact_by_id(db_path, contact_id)
    if contact is None:
        raise NotFoundError(f"Contact {contact_id} not found")
    return contact

def create_contact(db_path, first_name, last_name=None):
    if not first_name or not first_name.strip():
        raise ValidationError("first_name is required")
    if not last_name or not last_name.strip():
        raise ValidationError("last_name is required")

    new_id = contact_data.create_contact(
        db_path, first_name.strip(), last_name.strip()
    )
    return get_contact(db_path, new_id)

def edit_contact(db_path, contact_id, first_name=None, last_name=None):
    get_contact(db_path, contact_id)

    # Both fields are required on a contact, but this still allows a
    # partial update (e.g. renaming just the first name) - the rule is
    # only "if you're setting it, it can't be blank", not "you must
    # always send both".
    if first_name is not None and not first_name.strip():
        raise ValidationError("first_name cannot be blank")
    if last_name is not None and not last_name.strip():
        raise ValidationError("last_name cannot be blank")

    contact_data.update_contact(
        db_path, contact_id, _clean(first_name), _clean(last_name)
    )
    return get_contact(db_path, contact_id)

def remove_contact(db_path, contact_id):
    get_contact(db_path, contact_id)
    contact_data.delete_contact(db_path, contact_id)

def _clean(value):
    """Trim a string, but leave None alone (used with COALESCE updates)."""
    return value.strip() if isinstance(value, str) else value
