"""
Unit tests for src.data.email_interface - the raw SQL layer for a
contact's emails.

Same approach as test_contact_interface.py: get_connection is mocked
where email_interface imports it, so no real sqlite3 connection or file
is ever touched, and rows are stood in for with plain dicts.
"""
import sqlite3
import unittest
from unittest.mock import patch

from src.data import email_interface

DB_PATH = "fake-db-path"


class EmailInterfaceTestCase(unittest.TestCase):
    def setUp(self):
        patcher = patch("src.data.email_interface.get_connection")
        self.mock_get_connection = patcher.start()
        self.addCleanup(patcher.stop)
        self.mock_conn = self.mock_get_connection.return_value


class TestAddContactEmail(EmailInterfaceTestCase):
    def test_inserts_and_returns_the_new_id(self):
        self.mock_conn.execute.return_value.lastrowid = 12

        result = email_interface.add_contact_email(DB_PATH, 1, "ada@example.com")

        self.assertEqual(result, 12)
        args = self.mock_conn.execute.call_args.args
        self.assertIn("INSERT INTO contact_emails", args[0])
        self.assertEqual(args[1], (1, "ada@example.com"))

    def test_commits_and_closes_the_connection(self):
        email_interface.add_contact_email(DB_PATH, 1, "ada@example.com")

        self.mock_conn.commit.assert_called_once()
        self.mock_conn.close.assert_called_once()

    def test_closes_the_connection_even_if_the_insert_fails(self):
        self.mock_conn.execute.side_effect = sqlite3.OperationalError("locked")

        with self.assertRaises(sqlite3.OperationalError):
            email_interface.add_contact_email(DB_PATH, 1, "ada@example.com")

        self.mock_conn.close.assert_called_once()
        self.mock_conn.commit.assert_not_called()


class TestGetContactEmails(EmailInterfaceTestCase):
    def test_returns_only_this_contacts_emails(self):
        self.mock_conn.execute.return_value.fetchall.return_value = [
            {"id": 1, "contact_id": 5, "email": "ada@example.com"}
        ]

        result = email_interface.get_contact_emails(DB_PATH, 5)

        self.assertEqual(result, [{"id": 1, "contact_id": 5, "email": "ada@example.com"}])
        args = self.mock_conn.execute.call_args.args
        self.assertIn("WHERE contact_id = ?", args[0])
        self.assertEqual(args[1], (5,))

    def test_orders_by_id(self):
        self.mock_conn.execute.return_value.fetchall.return_value = []

        email_interface.get_contact_emails(DB_PATH, 5)

        args = self.mock_conn.execute.call_args.args
        self.assertIn("ORDER BY id", args[0])

    def test_closes_the_connection(self):
        self.mock_conn.execute.return_value.fetchall.return_value = []

        email_interface.get_contact_emails(DB_PATH, 5)

        self.mock_conn.close.assert_called_once()


class TestDeleteContactEmail(EmailInterfaceTestCase):
    def test_returns_true_when_a_row_was_deleted(self):
        self.mock_conn.total_changes = 1

        result = email_interface.delete_contact_email(DB_PATH, 9)

        self.assertTrue(result)
        args = self.mock_conn.execute.call_args.args
        self.assertEqual(args[1], (9,))

    def test_returns_false_when_nothing_was_deleted(self):
        self.mock_conn.total_changes = 0

        result = email_interface.delete_contact_email(DB_PATH, 999)

        self.assertFalse(result)

    def test_commits_and_closes_the_connection(self):
        self.mock_conn.total_changes = 1

        email_interface.delete_contact_email(DB_PATH, 9)

        self.mock_conn.commit.assert_called_once()
        self.mock_conn.close.assert_called_once()

    def test_closes_the_connection_even_if_the_delete_fails(self):
        self.mock_conn.execute.side_effect = sqlite3.OperationalError("locked")

        with self.assertRaises(sqlite3.OperationalError):
            email_interface.delete_contact_email(DB_PATH, 9)

        self.mock_conn.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
