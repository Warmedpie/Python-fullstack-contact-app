"""
Unit tests for src.data.contact_interface - the raw SQL layer for the
contacts table.

get_connection is mocked where contact_interface imports it, so no real
sqlite3 connection or file is ever touched. Row objects are stood in for
with plain dicts (as in test_database.py): both support the mapping
protocol that _row_to_dict/_rows_to_list rely on via dict(), so this is a
faithful test of the conversion without needing a real sqlite3.Row.
"""
import sqlite3
import unittest
from unittest.mock import patch

from src.data import contact_interface

DB_PATH = "fake-db-path"


class ContactInterfaceTestCase(unittest.TestCase):
    def setUp(self):
        patcher = patch("src.data.contact_interface.get_connection")
        self.mock_get_connection = patcher.start()
        self.addCleanup(patcher.stop)
        self.mock_conn = self.mock_get_connection.return_value


class TestCreateContact(ContactInterfaceTestCase):
    def test_inserts_and_returns_the_new_id(self):
        self.mock_conn.execute.return_value.lastrowid = 7

        result = contact_interface.create_contact(DB_PATH, "Ada", "Lovelace")

        self.assertEqual(result, 7)
        args = self.mock_conn.execute.call_args.args
        self.assertIn("INSERT INTO contacts", args[0])
        self.assertEqual(args[1], ("Ada", "Lovelace"))

    def test_commits_and_closes_the_connection(self):
        contact_interface.create_contact(DB_PATH, "Ada", "Lovelace")

        self.mock_conn.commit.assert_called_once()
        self.mock_conn.close.assert_called_once()

    def test_closes_the_connection_even_if_the_insert_fails(self):
        self.mock_conn.execute.side_effect = sqlite3.OperationalError("locked")

        with self.assertRaises(sqlite3.OperationalError):
            contact_interface.create_contact(DB_PATH, "Ada", "Lovelace")

        self.mock_conn.close.assert_called_once()
        self.mock_conn.commit.assert_not_called()


class TestGetContactById(ContactInterfaceTestCase):
    def test_returns_a_dict_when_found(self):
        self.mock_conn.execute.return_value.fetchone.return_value = {
            "id": 1, "first_name": "Ada", "last_name": "Lovelace"
        }

        result = contact_interface.get_contact_by_id(DB_PATH, 1)

        self.assertEqual(result, {"id": 1, "first_name": "Ada", "last_name": "Lovelace"})
        args = self.mock_conn.execute.call_args.args
        self.assertIn("SELECT * FROM contacts WHERE id = ?", args[0])
        self.assertEqual(args[1], (1,))

    def test_returns_none_when_not_found(self):
        self.mock_conn.execute.return_value.fetchone.return_value = None

        result = contact_interface.get_contact_by_id(DB_PATH, 999)

        self.assertIsNone(result)

    def test_closes_the_connection_regardless_of_outcome(self):
        self.mock_conn.execute.return_value.fetchone.return_value = None

        contact_interface.get_contact_by_id(DB_PATH, 999)

        self.mock_conn.close.assert_called_once()


class TestGetAllContacts(ContactInterfaceTestCase):
    def test_returns_a_list_of_dicts(self):
        self.mock_conn.execute.return_value.fetchall.return_value = [
            {"id": 1, "first_name": "Ada"},
            {"id": 2, "first_name": "Grace"},
        ]

        result = contact_interface.get_all_contacts(DB_PATH)

        self.assertEqual(result, [{"id": 1, "first_name": "Ada"}, {"id": 2, "first_name": "Grace"}])

    def test_orders_by_last_name_then_first_name(self):
        self.mock_conn.execute.return_value.fetchall.return_value = []

        contact_interface.get_all_contacts(DB_PATH)

        args = self.mock_conn.execute.call_args.args
        self.assertIn("ORDER BY last_name, first_name", args[0])

    def test_closes_the_connection(self):
        self.mock_conn.execute.return_value.fetchall.return_value = []

        contact_interface.get_all_contacts(DB_PATH)

        self.mock_conn.close.assert_called_once()


class TestUpdateContact(ContactInterfaceTestCase):
    def test_passes_the_new_values_and_id_through_in_order(self):
        self.mock_conn.total_changes = 1

        contact_interface.update_contact(DB_PATH, 3, first_name="New", last_name="Name")

        args = self.mock_conn.execute.call_args.args
        self.assertEqual(args[1], ("New", "Name", 3))

    def test_returns_true_when_a_row_was_changed(self):
        self.mock_conn.total_changes = 1

        result = contact_interface.update_contact(DB_PATH, 3, first_name="New")

        self.assertTrue(result)

    def test_returns_false_when_no_row_was_changed(self):
        self.mock_conn.total_changes = 0

        result = contact_interface.update_contact(DB_PATH, 999, first_name="New")

        self.assertFalse(result)

    def test_commits_and_closes_the_connection(self):
        self.mock_conn.total_changes = 1

        contact_interface.update_contact(DB_PATH, 3, first_name="New")

        self.mock_conn.commit.assert_called_once()
        self.mock_conn.close.assert_called_once()


class TestDeleteContact(ContactInterfaceTestCase):
    def test_returns_true_when_a_row_was_deleted(self):
        self.mock_conn.total_changes = 1

        result = contact_interface.delete_contact(DB_PATH, 3)

        self.assertTrue(result)
        args = self.mock_conn.execute.call_args.args
        self.assertEqual(args[1], (3,))

    def test_returns_false_when_nothing_was_deleted(self):
        self.mock_conn.total_changes = 0

        result = contact_interface.delete_contact(DB_PATH, 999)

        self.assertFalse(result)

    def test_closes_the_connection_even_if_the_delete_fails(self):
        self.mock_conn.execute.side_effect = sqlite3.OperationalError("locked")

        with self.assertRaises(sqlite3.OperationalError):
            contact_interface.delete_contact(DB_PATH, 3)

        self.mock_conn.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
