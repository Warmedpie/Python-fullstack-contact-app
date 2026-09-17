"""
Unit tests for src.api.contact_routes - the HTTP layer for contacts.

The service layer is mocked (src.api.contact_routes.contact_service /
.service_helpers), not the database: these tests aren't re-checking
business rules (that's tests/test_contact_service.py's job) - they're
checking that each route calls the right service function with the
right arguments, and translates its result/exception into the right
HTTP status code and JSON body.

The Flask app itself is real (built via the actual create_app()), using
TestConfig's in-memory SQLite so app creation doesn't touch a real file
- but no route in this file executes a real database query, since the
service layer underneath is replaced with mocks before each request.
"""
import unittest
from unittest.mock import patch

from config import TestConfig
from app import create_app
from src.service.exceptions import NotFoundError, ValidationError


class ContactRoutesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app.testing = True
        self.client = self.app.test_client()
        self.db_path = self.app.config["DATABASE_PATH"]


class TestListContacts(ContactRoutesTestCase):
    @patch("src.api.contact_routes.service_helpers")
    def test_returns_200_with_service_result(self, mock_helpers):
        mock_helpers.get_all_contacts_with_emails.return_value = [
            {"id": 1, "first_name": "Ada", "last_name": "Lovelace", "emails": []}
        ]

        response = self.client.get("/api/contacts")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), [
            {"id": 1, "first_name": "Ada", "last_name": "Lovelace", "emails": []}
        ])
        mock_helpers.get_all_contacts_with_emails.assert_called_once_with(self.db_path)


class TestGetContact(ContactRoutesTestCase):
    @patch("src.api.contact_routes.service_helpers")
    def test_returns_200_when_found(self, mock_helpers):
        mock_helpers.get_contact_with_emails.return_value = {"id": 5, "first_name": "Grace"}

        response = self.client.get("/api/contacts/5")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"id": 5, "first_name": "Grace"})
        mock_helpers.get_contact_with_emails.assert_called_once_with(self.db_path, 5)

    @patch("src.api.contact_routes.service_helpers")
    def test_returns_404_when_not_found(self, mock_helpers):
        mock_helpers.get_contact_with_emails.side_effect = NotFoundError("Contact 999 not found")

        response = self.client.get("/api/contacts/999")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json(), {"error": "Contact 999 not found"})

    def test_non_integer_id_returns_404_via_url_converter(self):
        # <int:contact_id> means Flask itself rejects a non-numeric id
        # before the route body (and the mocked service) ever runs.
        response = self.client.get("/api/contacts/not-a-number")

        self.assertEqual(response.status_code, 404)


class TestCreateContact(ContactRoutesTestCase):
    @patch("src.api.contact_routes.contact_service")
    def test_returns_201_with_created_contact(self, mock_service):
        mock_service.create_contact.return_value = {
            "id": 1, "first_name": "Ada", "last_name": "Lovelace"
        }

        response = self.client.post(
            "/api/contacts", json={"first_name": "Ada", "last_name": "Lovelace"}
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["id"], 1)
        mock_service.create_contact.assert_called_once_with(self.db_path, "Ada", "Lovelace")

    @patch("src.api.contact_routes.contact_service")
    def test_returns_400_on_validation_error(self, mock_service):
        mock_service.create_contact.side_effect = ValidationError("last_name is required")

        response = self.client.post("/api/contacts", json={"first_name": "Ada"})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json(), {"error": "last_name is required"})

    @patch("src.api.contact_routes.contact_service")
    def test_missing_request_body_does_not_crash_the_route(self, mock_service):
        # No JSON body at all (not even {}) - request.get_json(silent=True)
        # returns None, and the route needs to fall back to {} rather than
        # raising an AttributeError trying to call .get() on None.
        mock_service.create_contact.side_effect = ValidationError("first_name is required")

        response = self.client.post("/api/contacts")

        self.assertEqual(response.status_code, 400)
        mock_service.create_contact.assert_called_once_with(self.db_path, None, None)


class TestUpdateContact(ContactRoutesTestCase):
    @patch("src.api.contact_routes.contact_service")
    def test_returns_200_with_updated_contact(self, mock_service):
        mock_service.edit_contact.return_value = {"id": 3, "first_name": "New"}

        response = self.client.put("/api/contacts/3", json={"first_name": "New"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"id": 3, "first_name": "New"})
        mock_service.edit_contact.assert_called_once_with(self.db_path, 3, "New", None)

    @patch("src.api.contact_routes.contact_service")
    def test_returns_404_when_not_found(self, mock_service):
        mock_service.edit_contact.side_effect = NotFoundError("Contact 3 not found")

        response = self.client.put("/api/contacts/3", json={"first_name": "New"})

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json(), {"error": "Contact 3 not found"})

    @patch("src.api.contact_routes.contact_service")
    def test_returns_400_on_validation_error(self, mock_service):
        mock_service.edit_contact.side_effect = ValidationError("last_name cannot be blank")

        response = self.client.put("/api/contacts/3", json={"last_name": ""})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json(), {"error": "last_name cannot be blank"})


class TestDeleteContact(ContactRoutesTestCase):
    @patch("src.api.contact_routes.contact_service")
    def test_returns_204_on_success(self, mock_service):
        mock_service.remove_contact.return_value = None

        response = self.client.delete("/api/contacts/7")

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.data, b"")
        mock_service.remove_contact.assert_called_once_with(self.db_path, 7)

    @patch("src.api.contact_routes.contact_service")
    def test_returns_404_when_not_found(self, mock_service):
        mock_service.remove_contact.side_effect = NotFoundError("Contact 7 not found")

        response = self.client.delete("/api/contacts/7")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json(), {"error": "Contact 7 not found"})


if __name__ == "__main__":
    unittest.main()
