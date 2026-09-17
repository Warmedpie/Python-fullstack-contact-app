"""
Delete goes through a confirmation modal instead of deleting immediately:
cancelling it (via its own Cancel button, the backdrop, or Escape) leaves
the contact untouched, and only confirming actually deletes it.
"""
from tests.e2e.base import E2ETestCase


class TestDeleteConfirm(E2ETestCase):
    def test_01_overlay_hidden_on_initial_load(self):
        self.assertTrue(self.is_hidden("#confirm-overlay"))

    def test_02_cancel_button_on_the_modal_leaves_the_contact_intact(self):
        self.make_contact("Rosalind", "Franklin")

        self.page.click("#delete-contact-btn")
        self.assertFalse(self.is_hidden("#confirm-overlay"))
        self.assertIn("Rosalind", self.page.inner_text("#confirm-message"))

        self.page.click("#confirm-cancel-btn")
        self.assertTrue(self.is_hidden("#confirm-overlay"))
        self.assertEqual(self.contact_count(), 1)
        self.assertFalse(self.is_hidden("#contact-form"))

    def test_03_backdrop_click_also_cancels(self):
        self.page.click("#delete-contact-btn")
        self.assertFalse(self.is_hidden("#confirm-overlay"))

        # click near the edge of the overlay, outside the dialog box itself
        self.page.click("#confirm-overlay", position={"x": 5, "y": 5})

        self.assertTrue(self.is_hidden("#confirm-overlay"))
        self.assertEqual(self.contact_count(), 1)

    def test_04_escape_key_also_cancels(self):
        self.page.click("#delete-contact-btn")
        self.assertFalse(self.is_hidden("#confirm-overlay"))

        self.page.keyboard.press("Escape")

        self.assertTrue(self.is_hidden("#confirm-overlay"))
        self.assertEqual(self.contact_count(), 1)

    def test_05_confirming_actually_deletes_the_contact(self):
        self.page.click("#delete-contact-btn")
        self.assertFalse(self.is_hidden("#confirm-overlay"))

        with self.page.expect_response(
            lambda r: "/api/contacts/" in r.url and r.request.method == "DELETE"
        ):
            self.page.click("#confirm-ok-btn")
        self.page.wait_for_timeout(400)

        self.assertTrue(self.is_hidden("#confirm-overlay"))
        self.assertEqual(self.contact_count(), 0)
        self.assertTrue(self.is_hidden("#contact-form"))

    def test_06_confirm_flow_also_works_for_a_contact_just_created_this_session(self):
        self.make_contact("Chien-Shiung", "Wu")

        self.page.click("#delete-contact-btn")
        self.page.click("#confirm-ok-btn")
        self.page.wait_for_timeout(400)

        self.assertEqual(self.contact_count(), 0)
