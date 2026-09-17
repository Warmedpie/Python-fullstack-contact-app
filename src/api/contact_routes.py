from flask import Blueprint, current_app, jsonify, request

from src.service import contact_service, service_helpers
from src.service.exceptions import NotFoundError, ValidationError

contact_bp = Blueprint("contacts", __name__)

def _db_path():
    return current_app.config["DATABASE_PATH"]

@contact_bp.get("/contacts")
def list_contacts():
    return jsonify(service_helpers.get_all_contacts_with_emails(_db_path()))

@contact_bp.get("/contacts/<int:contact_id>")
def get_contact(contact_id):
    try:
        contact = service_helpers.get_contact_with_emails(_db_path(), contact_id)
        return jsonify(contact)
    except NotFoundError as e:
        return jsonify({"error": str(e)}), 404

@contact_bp.post("/contacts")
def create_contact():
    data = request.get_json(silent=True) or {}
    try:
        contact = contact_service.create_contact(
            _db_path(), data.get("first_name"), data.get("last_name")
        )
        return jsonify(contact), 201
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400

@contact_bp.put("/contacts/<int:contact_id>")
def update_contact(contact_id):
    data = request.get_json(silent=True) or {}
    try:
        contact = contact_service.edit_contact(
            _db_path(),
            contact_id,
            data.get("first_name"),
            data.get("last_name"),
        )
        return jsonify(contact)
    except NotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400

@contact_bp.delete("/contacts/<int:contact_id>")
def delete_contact(contact_id):
    try:
        contact_service.remove_contact(_db_path(), contact_id)
        return "", 204
    except NotFoundError as e:
        return jsonify({"error": str(e)}), 404
