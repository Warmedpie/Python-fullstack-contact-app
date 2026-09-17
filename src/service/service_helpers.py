from src.service import contact_service, email_service

def get_contact_with_emails(db_path, contact_id):
    contact = contact_service.get_contact(db_path, contact_id)
    contact["emails"] = email_service.list_emails_for_contact(
        db_path, contact_id
    )
    return contact

def get_all_contacts_with_emails(db_path):
    contacts = contact_service.list_contacts(db_path)
    for contact in contacts:
        contact["emails"] = email_service.list_emails_for_contact(
            db_path, contact["id"]
        )
    return contacts
