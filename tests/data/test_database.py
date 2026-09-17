"""
Unit tests for src.data.database - the connection helper, the row/rows
conversion helpers, and init_db's schema setup.

No real sqlite3 connection or file is used anywhere in this file:
get_connection() is tested by mocking the sqlite3 module itself, and
init_db() is tested by mocking get_connection() so it never has to
resolve to a real Connection.
"""
import sqlite3
import unittest
from unittest.mock import patch, MagicMock, call

from src.data import database

DB_PATH = "fake-db-path"


class TestRowConversionHelpers(unittest.TestCase):
    def test_row_to_dict_converts_a_row(self):
        # A plain dict stands in for sqlite3.Row here: both support the
        # mapping protocol dict() relies on, so this is a faithful test
        # of what _row_to_dict actually does with the row it's handed.
        row = {"id": 1, "first_name": "Ada"}

        self.assertEqual(database._row_to_dict(row), {"id": 1, "first_name": "Ada"})

    def test_row_to_dict_returns_none_for_none(self):
        self.assertIsNone(database._row_to_dict(None))

    def test_rows_to_list_converts_every_row(self):
        rows = [{"id": 1}, {"id": 2}]

        self.assertEqual(database._rows_to_list(rows), [{"id": 1}, {"id": 2}])

    def test_rows_to_list_handles_empty_input(self):
        self.assertEqual(database._rows_to_list([]), [])


class TestGetConnection(unittest.TestCase):
    @patch("src.data.database.sqlite3")
    def test_connects_to_the_given_path(self, mock_sqlite3):
        database.get_connection(DB_PATH)

        mock_sqlite3.connect.assert_called_once_with(DB_PATH)

    @patch("src.data.database.sqlite3")
    def test_sets_row_factory_to_sqlite3_row(self, mock_sqlite3):
        mock_conn = mock_sqlite3.connect.return_value

        database.get_connection(DB_PATH)

        self.assertIs(mock_conn.row_factory, mock_sqlite3.Row)

    @patch("src.data.database.sqlite3")
    def test_enables_foreign_key_enforcement(self, mock_sqlite3):
        mock_conn = mock_sqlite3.connect.return_value

        database.get_connection(DB_PATH)

        mock_conn.execute.assert_called_once_with("PRAGMA foreign_keys = ON")

    @patch("src.data.database.sqlite3")
    def test_returns_the_connection(self, mock_sqlite3):
        result = database.get_connection(DB_PATH)

        self.assertIs(result, mock_sqlite3.connect.return_value)


class TestInitDb(unittest.TestCase):
    @patch("src.data.database.get_connection")
    def test_creates_the_contacts_table(self, mock_get_connection):
        mock_conn = mock_get_connection.return_value

        database.init_db(DB_PATH)

        scripts = [c.args[0] for c in mock_conn.executescript.call_args_list]
        self.assertTrue(any("CREATE TABLE IF NOT EXISTS contacts" in s for s in scripts))

    @patch("src.data.database.get_connection")
    def test_creates_the_contact_emails_table_with_cascade_delete(self, mock_get_connection):
        mock_conn = mock_get_connection.return_value

        database.init_db(DB_PATH)

        scripts = [c.args[0] for c in mock_conn.executescript.call_args_list]
        self.assertTrue(any(
            "CREATE TABLE IF NOT EXISTS contact_emails" in s and "ON DELETE CASCADE" in s
            for s in scripts
        ))

    @patch("src.data.database.get_connection")
    def test_creates_the_contact_id_index(self, mock_get_connection):
        mock_conn = mock_get_connection.return_value

        database.init_db(DB_PATH)

        scripts = [c.args[0] for c in mock_conn.executescript.call_args_list]
        self.assertTrue(any(
            "CREATE INDEX IF NOT EXISTS idx_contact_emails_contact_id" in s for s in scripts
        ))

    @patch("src.data.database.get_connection")
    def test_commits_and_closes_the_connection(self, mock_get_connection):
        mock_conn = mock_get_connection.return_value

        database.init_db(DB_PATH)

        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("src.data.database.get_connection")
    def test_closes_the_connection_even_if_schema_setup_fails(self, mock_get_connection):
        # A locked/corrupt DB file failing partway through setup must not
        # leak the open connection - the finally block has to run.
        mock_conn = mock_get_connection.return_value
        mock_conn.executescript.side_effect = sqlite3.OperationalError("disk I/O error")

        with self.assertRaises(sqlite3.OperationalError):
            database.init_db(DB_PATH)

        mock_conn.close.assert_called_once()
        mock_conn.commit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
