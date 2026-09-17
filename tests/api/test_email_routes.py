"""
Unit tests for src.api.email_routes - the HTTP layer for a contact's
emails. Same approach as test_contact_routes.py: the real Flask app,
but with src.api.email_routes.email_service mocked out, so these tests
check routing/status-codes/JSON shape rather than business rules.
"""
import unittest
from unittest.mock import patch

from config import TestConfig
from app import create_app
from src.service.exceptions import NotFoundError, ValidationError


class EmailRoutesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app.testing = True
        self.client = self.app.test_client()
        self.db_path = self.app.config["DATABASE_PATH"]


class TestListEmails(EmailRoutesTestCase):
    @patch("src.api.email_routes.email_service")
    def test_returns_200_with_service_result(self, mock_service):
        mock_service.list_emails_for_contact.return_value = [
            {"id": 1, "email": "ada@example.com"}
        ]

        response = self.client.get("/api/contacts/1/emails")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), [{"id": 1, "email": "ada@example.com"}])
        mock_service.list_emails_for_contact.assert_called_once_with(self.db_path, 1)

    @patch("src.api.email_routes.email_service")
    def test_returns_404_when_contact_missing(self, mock_service):
        mock_service.list_emails_for_contact.side_effect = NotFoundError("Contact 1 not found")

        response = self.client.get("/api/contacts/1/emails")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json(), {"error": "Contact 1 not found"})


class TestAddEmail(EmailRoutesTestCase):
    @patch("src.api.email_routes.email_service")
    def test_returns_201_with_created_email(self, mock_service):
        mock_service.add_email.return_value = {
            "id": 10, "contact_id": 1, "email": "ada@example.com"
        }

        response = self.client.post("/api/contacts/1/emails", json={"email": "ada@example.com"})

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["email"], "ada@example.com")
        mock_service.add_email.assert_called_once_with(self.db_path, 1, "ada@example.com")

    @patch("src.api.email_routes.email_service")
    def test_returns_404_when_contact_missing(self, mock_service):
        mock_service.add_email.side_effect = NotFoundError("Contact 1 not found")

        response = self.client.post("/api/contacts/1/emails", json={"email": "ada@example.com"})

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json(), {"error": "Contact 1 not found"})

    @patch("src.api.email_routes.email_service")
    def test_returns_400_on_invalid_email_format(self, mock_service):
        mock_service.add_email.side_effect = ValidationError("'nope' is not a valid email address")

        response = self.client.post("/api/contacts/1/emails", json={"email": "nope"})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json(), {"error": "'nope' is not a valid email address"})

    @patch("src.api.email_routes.email_service")
    def test_missing_request_body_does_not_crash_the_route(self, mock_service):
        mock_service.add_email.side_effect = ValidationError("None is not a valid email address")

        response = self.client.post("/api/contacts/1/emails")

        self.assertEqual(response.status_code, 400)
        mock_service.add_email.assert_called_once_with(self.db_path, 1, None)


class TestDeleteEmail(EmailRoutesTestCase):
    @patch("src.api.email_routes.email_service")
    def test_returns_204_on_success(self, mock_service):
        mock_service.remove_email.return_value = None

        response = self.client.delete("/api/contacts/1/emails/5")

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.data, b"")
        mock_service.remove_email.assert_called_once_with(self.db_path, 5)

    @patch("src.api.email_routes.email_service")
    def test_returns_404_when_not_found(self, mock_service):
        mock_service.remove_email.side_effect = NotFoundError("Email 5 not found")

        response = self.client.delete("/api/contacts/1/emails/5")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json(), {"error": "Email 5 not found"})


if __name__ == "__main__":
    unittest.main()
