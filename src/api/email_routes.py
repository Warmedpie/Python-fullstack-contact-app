from flask import Blueprint, current_app, jsonify, request

from src.service import email_service
from src.service.exceptions import NotFoundError, ValidationError

email_bp = Blueprint("emails", __name__)

def _db_path():
    return current_app.config["DATABASE_PATH"]

@email_bp.get("/contacts/<int:contact_id>/emails")
def list_emails(contact_id):
    try:
        emails = email_service.list_emails_for_contact(_db_path(), contact_id)
        return jsonify(emails)
    except NotFoundError as e:
        return jsonify({"error": str(e)}), 404

@email_bp.post("/contacts/<int:contact_id>/emails")
def add_email(contact_id):
    data = request.get_json(silent=True) or {}
    try:
        email = email_service.add_email(
            _db_path(), contact_id, data.get("email")
        )
        return jsonify(email), 201
    except NotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400

@email_bp.delete("/contacts/<int:contact_id>/emails/<int:email_id>")
def delete_email(contact_id, email_id):
    try:
        email_service.remove_email(_db_path(), email_id)
        return "", 204
    except NotFoundError as e:
        return jsonify({"error": str(e)}), 404
