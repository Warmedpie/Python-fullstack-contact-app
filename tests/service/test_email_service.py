"""
Unit tests for src.service.email_service - email format validation and
the rule that an email can't be added to (or listed for) a contact that
doesn't exist.

Both data-layer dependencies are mocked: contact_data (used only for the
existence check) and email_data (the actual email storage). No real
database is touched.
"""
import unittest
from unittest.mock import patch

from src.service import email_service
from src.service.exceptions import NotFoundError, ValidationError

DB_PATH = "fake-db-path"
CONTACT_ID = 1


class TestListEmailsForContact(unittest.TestCase):
    @patch("src.service.email_service.email_data")
    @patch("src.service.email_service.contact_data")
    def test_raises_not_found_when_contact_missing(self, mock_contact_data, mock_email_data):
        mock_contact_data.get_contact_by_id.return_value = None

        with self.assertRaises(NotFoundError):
            email_service.list_emails_for_contact(DB_PATH, CONTACT_ID)

        mock_email_data.get_contact_emails.assert_not_called()

    @patch("src.service.email_service.email_data")
    @patch("src.service.email_service.contact_data")
    def test_returns_emails_when_contact_exists(self, mock_contact_data, mock_email_data):
        mock_contact_data.get_contact_by_id.return_value = {"id": CONTACT_ID}
        mock_email_data.get_contact_emails.return_value = [
            {"id": 1, "email": "ada@example.com"}
        ]

        result = email_service.list_emails_for_contact(DB_PATH, CONTACT_ID)

        mock_email_data.get_contact_emails.assert_called_once_with(DB_PATH, CONTACT_ID)
        self.assertEqual(result, [{"id": 1, "email": "ada@example.com"}])


class TestAddEmail(unittest.TestCase):
    @patch("src.service.email_service.email_data")
    @patch("src.service.email_service.contact_data")
    def test_raises_not_found_before_validating_email(self, mock_contact_data, mock_email_data):
        # Contact-existence is checked first: even a garbage email string
        # should surface as "contact not found", not "invalid email".
        mock_contact_data.get_contact_by_id.return_value = None

        with self.assertRaises(NotFoundError):
            email_service.add_email(DB_PATH, CONTACT_ID, "not-an-email-either")

        mock_email_data.add_contact_email.assert_not_called()

    @patch("src.service.email_service.email_data")
    @patch("src.service.email_service.contact_data")
    def test_rejects_invalid_email_formats(self, mock_contact_data, mock_email_data):
        mock_contact_data.get_contact_by_id.return_value = {"id": CONTACT_ID}

        invalid_addresses = [
            "no-at-sign.com",
            "double@@at.com",
            "@missing-local.com",
            "missing-domain@",
            "no-dot-in-domain@example",
            "has space@example.com",
            "",
            "   ",
            None,
        ]

        for address in invalid_addresses:
            with self.subTest(address=address):
                with self.assertRaises(ValidationError):
                    email_service.add_email(DB_PATH, CONTACT_ID, address)

        mock_email_data.add_contact_email.assert_not_called()

    @patch("src.service.email_service.email_data")
    @patch("src.service.email_service.contact_data")
    def test_accepts_valid_email_formats(self, mock_contact_data, mock_email_data):
        mock_contact_data.get_contact_by_id.return_value = {"id": CONTACT_ID}
        mock_email_data.add_contact_email.return_value = 10

        valid_addresses = [
            "ada@example.com",
            "first.last+tag@sub.example.co.uk",
            "a@b.co",
        ]

        for address in valid_addresses:
            with self.subTest(address=address):
                result = email_service.add_email(DB_PATH, CONTACT_ID, address)
                self.assertEqual(result["email"], address)

    @patch("src.service.email_service.email_data")
    @patch("src.service.email_service.contact_data")
    def test_trims_whitespace_before_persisting_and_in_the_response(
        self, mock_contact_data, mock_email_data
    ):
        mock_contact_data.get_contact_by_id.return_value = {"id": CONTACT_ID}
        mock_email_data.add_contact_email.return_value = 99

        result = email_service.add_email(DB_PATH, CONTACT_ID, "  ada@example.com  ")

        mock_email_data.add_contact_email.assert_called_once_with(
            DB_PATH, CONTACT_ID, "ada@example.com"
        )
        self.assertEqual(result, {
            "id": 99,
            "contact_id": CONTACT_ID,
            "email": "ada@example.com",
        })


class TestRemoveEmail(unittest.TestCase):
    @patch("src.service.email_service.email_data")
    def test_raises_not_found_when_nothing_was_deleted(self, mock_email_data):
        mock_email_data.delete_contact_email.return_value = False

        with self.assertRaises(NotFoundError):
            email_service.remove_email(DB_PATH, 123)

    @patch("src.service.email_service.email_data")
    def test_succeeds_silently_when_a_row_was_deleted(self, mock_email_data):
        mock_email_data.delete_contact_email.return_value = True

        # Should not raise.
        email_service.remove_email(DB_PATH, 123)

        mock_email_data.delete_contact_email.assert_called_once_with(DB_PATH, 123)


if __name__ == "__main__":
    unittest.main()
