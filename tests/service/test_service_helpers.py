"""
Unit tests for src.service.service_helpers - the thin composition layer
that attaches a contact's emails onto its record. contact_service and
email_service are themselves mocked here (not the database), since this
module's only job is wiring the two together correctly.
"""
import unittest
from unittest.mock import patch

from src.service import service_helpers

DB_PATH = "fake-db-path"


class TestGetContactWithEmails(unittest.TestCase):
    @patch("src.service.service_helpers.email_service")
    @patch("src.service.service_helpers.contact_service")
    def test_attaches_emails_list_onto_the_contact(self, mock_contact_service, mock_email_service):
        mock_contact_service.get_contact.return_value = {"id": 1, "first_name": "Ada"}
        mock_email_service.list_emails_for_contact.return_value = [
            {"id": 1, "email": "ada@example.com"}
        ]

        result = service_helpers.get_contact_with_emails(DB_PATH, 1)

        mock_contact_service.get_contact.assert_called_once_with(DB_PATH, 1)
        mock_email_service.list_emails_for_contact.assert_called_once_with(DB_PATH, 1)
        self.assertEqual(result, {
            "id": 1,
            "first_name": "Ada",
            "emails": [{"id": 1, "email": "ada@example.com"}],
        })

    @patch("src.service.service_helpers.email_service")
    @patch("src.service.service_helpers.contact_service")
    def test_propagates_not_found_from_contact_service(self, mock_contact_service, mock_email_service):
        from src.service.exceptions import NotFoundError

        mock_contact_service.get_contact.side_effect = NotFoundError("Contact 999 not found")

        with self.assertRaises(NotFoundError):
            service_helpers.get_contact_with_emails(DB_PATH, 999)

        # Never got far enough to ask for emails of a contact that doesn't exist.
        mock_email_service.list_emails_for_contact.assert_not_called()


class TestGetAllContactsWithEmails(unittest.TestCase):
    @patch("src.service.service_helpers.email_service")
    @patch("src.service.service_helpers.contact_service")
    def test_attaches_emails_to_every_contact(self, mock_contact_service, mock_email_service):
        mock_contact_service.list_contacts.return_value = [
            {"id": 1, "first_name": "Ada"},
            {"id": 2, "first_name": "Grace"},
        ]
        # Different emails per contact_id, to confirm each lookup uses the
        # right id rather than reusing the first result.
        mock_email_service.list_emails_for_contact.side_effect = lambda db, cid: [
            {"id": cid * 10, "email": f"contact{cid}@example.com"}
        ]

        result = service_helpers.get_all_contacts_with_emails(DB_PATH)

        self.assertEqual(result, [
            {"id": 1, "first_name": "Ada", "emails": [{"id": 10, "email": "contact1@example.com"}]},
            {"id": 2, "first_name": "Grace", "emails": [{"id": 20, "email": "contact2@example.com"}]},
        ])

    @patch("src.service.service_helpers.email_service")
    @patch("src.service.service_helpers.contact_service")
    def test_empty_contact_list_returns_empty_list(self, mock_contact_service, mock_email_service):
        mock_contact_service.list_contacts.return_value = []

        result = service_helpers.get_all_contacts_with_emails(DB_PATH)

        self.assertEqual(result, [])
        mock_email_service.list_emails_for_contact.assert_not_called()


if __name__ == "__main__":
    unittest.main()
