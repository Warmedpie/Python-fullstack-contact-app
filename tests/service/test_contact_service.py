"""
Unit tests for src.service.contact_service - the business-rule layer for
contacts (required fields, partial-update semantics, not-found guarding).

The data layer (src.data.contact_interface) is mocked throughout via
@patch("src.service.contact_service.contact_data", ...): these tests
never touch a real database, and assert not just the return values but
*whether the data layer was called at all* - a validation failure should
short-circuit before any DB call is made.
"""
import unittest
from unittest.mock import patch

from src.service import contact_service
from src.service.exceptions import NotFoundError, ValidationError

DB_PATH = "fake-db-path"


class TestListContacts(unittest.TestCase):
    @patch("src.service.contact_service.contact_data")
    def test_returns_data_layer_result_unchanged(self, mock_data):
        mock_data.get_all_contacts.return_value = [
            {"id": 1, "first_name": "Ada", "last_name": "Lovelace"}
        ]

        result = contact_service.list_contacts(DB_PATH)

        mock_data.get_all_contacts.assert_called_once_with(DB_PATH)
        self.assertEqual(result, [{"id": 1, "first_name": "Ada", "last_name": "Lovelace"}])


class TestGetContact(unittest.TestCase):
    @patch("src.service.contact_service.contact_data")
    def test_returns_contact_when_found(self, mock_data):
        mock_data.get_contact_by_id.return_value = {"id": 5, "first_name": "Grace"}

        result = contact_service.get_contact(DB_PATH, 5)

        mock_data.get_contact_by_id.assert_called_once_with(DB_PATH, 5)
        self.assertEqual(result, {"id": 5, "first_name": "Grace"})

    @patch("src.service.contact_service.contact_data")
    def test_raises_not_found_when_missing(self, mock_data):
        mock_data.get_contact_by_id.return_value = None

        with self.assertRaises(NotFoundError) as ctx:
            contact_service.get_contact(DB_PATH, 999)

        self.assertIn("999", str(ctx.exception))


class TestCreateContact(unittest.TestCase):
    @patch("src.service.contact_service.contact_data")
    def test_requires_first_name(self, mock_data):
        with self.assertRaises(ValidationError) as ctx:
            contact_service.create_contact(DB_PATH, "", "Lovelace")

        self.assertIn("first_name", str(ctx.exception))
        mock_data.create_contact.assert_not_called()

    @patch("src.service.contact_service.contact_data")
    def test_requires_first_name_not_whitespace_only(self, mock_data):
        with self.assertRaises(ValidationError):
            contact_service.create_contact(DB_PATH, "   ", "Lovelace")

        mock_data.create_contact.assert_not_called()

    @patch("src.service.contact_service.contact_data")
    def test_requires_last_name(self, mock_data):
        with self.assertRaises(ValidationError) as ctx:
            contact_service.create_contact(DB_PATH, "Ada", None)

        self.assertIn("last_name", str(ctx.exception))
        mock_data.create_contact.assert_not_called()

    @patch("src.service.contact_service.contact_data")
    def test_requires_last_name_not_blank(self, mock_data):
        with self.assertRaises(ValidationError):
            contact_service.create_contact(DB_PATH, "Ada", "   ")

        mock_data.create_contact.assert_not_called()

    @patch("src.service.contact_service.contact_data")
    def test_trims_whitespace_before_persisting(self, mock_data):
        mock_data.create_contact.return_value = 42
        mock_data.get_contact_by_id.return_value = {
            "id": 42, "first_name": "Ada", "last_name": "Lovelace"
        }

        result = contact_service.create_contact(DB_PATH, "  Ada  ", "  Lovelace  ")

        mock_data.create_contact.assert_called_once_with(DB_PATH, "Ada", "Lovelace")
        self.assertEqual(result["id"], 42)

    @patch("src.service.contact_service.contact_data")
    def test_returns_the_newly_created_contact(self, mock_data):
        mock_data.create_contact.return_value = 7
        mock_data.get_contact_by_id.return_value = {
            "id": 7, "first_name": "Katherine", "last_name": "Johnson"
        }

        result = contact_service.create_contact(DB_PATH, "Katherine", "Johnson")

        mock_data.get_contact_by_id.assert_called_once_with(DB_PATH, 7)
        self.assertEqual(result, {"id": 7, "first_name": "Katherine", "last_name": "Johnson"})


class TestEditContact(unittest.TestCase):
    @patch("src.service.contact_service.contact_data")
    def test_raises_not_found_when_contact_missing(self, mock_data):
        mock_data.get_contact_by_id.return_value = None

        with self.assertRaises(NotFoundError):
            contact_service.edit_contact(DB_PATH, 999, first_name="New")

        mock_data.update_contact.assert_not_called()

    @patch("src.service.contact_service.contact_data")
    def test_allows_partial_update_of_first_name_only(self, mock_data):
        # get_contact is called twice (existence check, then to return the
        # updated row) - same canned response is fine for this test.
        mock_data.get_contact_by_id.return_value = {
            "id": 1, "first_name": "Grace", "last_name": "Hopper"
        }

        contact_service.edit_contact(DB_PATH, 1, first_name="Amazing Grace", last_name=None)

        mock_data.update_contact.assert_called_once_with(DB_PATH, 1, "Amazing Grace", None)

    @patch("src.service.contact_service.contact_data")
    def test_rejects_blank_first_name_if_explicitly_provided(self, mock_data):
        mock_data.get_contact_by_id.return_value = {"id": 1, "first_name": "Grace"}

        with self.assertRaises(ValidationError) as ctx:
            contact_service.edit_contact(DB_PATH, 1, first_name="   ")

        self.assertIn("first_name", str(ctx.exception))
        mock_data.update_contact.assert_not_called()

    @patch("src.service.contact_service.contact_data")
    def test_rejects_blank_last_name_if_explicitly_provided(self, mock_data):
        mock_data.get_contact_by_id.return_value = {"id": 1, "last_name": "Hopper"}

        with self.assertRaises(ValidationError) as ctx:
            contact_service.edit_contact(DB_PATH, 1, last_name="")

        self.assertIn("last_name", str(ctx.exception))
        mock_data.update_contact.assert_not_called()

    @patch("src.service.contact_service.contact_data")
    def test_trims_whitespace_on_update(self, mock_data):
        mock_data.get_contact_by_id.return_value = {"id": 1}

        contact_service.edit_contact(DB_PATH, 1, first_name="  Grace  ", last_name="  Hopper  ")

        mock_data.update_contact.assert_called_once_with(DB_PATH, 1, "Grace", "Hopper")

    @patch("src.service.contact_service.contact_data")
    def test_omitting_both_fields_is_not_a_validation_error(self, mock_data):
        # Neither field provided (both None) is a legitimate no-op update,
        # distinct from explicitly passing a blank string.
        mock_data.get_contact_by_id.return_value = {"id": 1}

        contact_service.edit_contact(DB_PATH, 1)

        mock_data.update_contact.assert_called_once_with(DB_PATH, 1, None, None)


class TestRemoveContact(unittest.TestCase):
    @patch("src.service.contact_service.contact_data")
    def test_raises_not_found_when_contact_missing(self, mock_data):
        mock_data.get_contact_by_id.return_value = None

        with self.assertRaises(NotFoundError):
            contact_service.remove_contact(DB_PATH, 999)

        mock_data.delete_contact.assert_not_called()

    @patch("src.service.contact_service.contact_data")
    def test_deletes_when_contact_exists(self, mock_data):
        mock_data.get_contact_by_id.return_value = {"id": 3}

        contact_service.remove_contact(DB_PATH, 3)

        mock_data.delete_contact.assert_called_once_with(DB_PATH, 3)


if __name__ == "__main__":
    unittest.main()
