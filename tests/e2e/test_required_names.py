"""
Both first and last name are required on create and on edit, and a
failed save surfaces a visible error banner instead of failing silently.
"""
from tests.e2e.base import E2ETestCase


class TestRequiredNames(E2ETestCase):
    def test_01_error_banner_hidden_on_initial_load(self):
        self.assertTrue(self.error_hidden())

    def test_02_blank_last_name_on_create_is_rejected(self):
        self.page.click("#add-contact-btn")
        self.page.fill("#first-name", "Ada")
        # last name left blank
        with self.page.expect_response(
            lambda r: r.url.endswith("/api/contacts") and r.request.method == "POST"
        ):
            self.page.click("#save-btn")
        self.page.wait_for_timeout(400)

        self.assertFalse(self.error_hidden())
        self.assertIn("last_name", self.error_text())
        self.assertEqual(self.contact_count(), 0)
        self.assertEqual(self.page.input_value("#first-name"), "Ada")

    def test_03_filling_in_the_last_name_and_saving_again_succeeds(self):
        self.page.fill("#last-name", "Lovelace")
        with self.page.expect_response(
            lambda r: r.url.endswith("/api/contacts") and r.request.method == "POST"
        ):
            self.page.click("#save-btn")
        self.page.wait_for_timeout(400)

        self.assertTrue(self.error_hidden())
        self.assertEqual(self.contact_count(), 1)

    def test_04_clearing_last_name_on_an_existing_contact_is_also_rejected(self):
        self.page.click(".contact-list-item")
        self.page.wait_for_timeout(300)
        self.page.fill("#last-name", "")
        with self.page.expect_response(
            lambda r: "/api/contacts/" in r.url and r.request.method == "PUT"
        ):
            self.page.click("#save-btn")
        self.page.wait_for_timeout(400)

        self.assertFalse(self.error_hidden())
        self.assertIn("last_name", self.error_text())

    def test_05_starting_a_new_contact_clears_the_stale_error_and_is_blank(self):
        self.page.click("#add-contact-btn")

        self.assertTrue(self.error_hidden())
        # Regression check: "+" after viewing an existing contact must not
        # silently pre-fill that contact's name (form.reset() alone
        # restores defaultValue, which renderContact() intentionally
        # rewrites so Cancel reverts to the saved value).
        self.assertEqual(self.page.input_value("#first-name"), "")
        self.assertEqual(self.page.input_value("#last-name"), "")

        self.page.click("#cancel-btn")

    def test_06_blank_first_name_on_create_is_rejected_with_its_own_message(self):
        self.page.click("#add-contact-btn")
        self.page.fill("#last-name", "Only-Last")
        with self.page.expect_response(
            lambda r: r.url.endswith("/api/contacts") and r.request.method == "POST"
        ):
            self.page.click("#save-btn")
        self.page.wait_for_timeout(400)

        self.assertFalse(self.error_hidden())
        self.assertIn("first_name", self.error_text())
