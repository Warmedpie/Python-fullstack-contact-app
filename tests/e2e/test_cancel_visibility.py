"""
Cancel should only be visible while there's something unsaved to drop: a
new (not-yet-saved) contact, or an unsaved email row - not while just
viewing or editing the name of an already-saved contact.
"""
from tests.e2e.base import E2ETestCase


class TestCancelVisibility(E2ETestCase):
    def test_01_hidden_on_initial_load(self):
        self.assertTrue(self.is_hidden("#contact-form"))
        self.assertTrue(self.is_hidden("#cancel-btn"))

    def test_02_visible_for_a_new_unsaved_contact(self):
        self.page.click("#add-contact-btn")
        self.assertFalse(self.is_hidden("#cancel-btn"))

        self.page.click("#cancel-btn")
        self.assertTrue(self.is_hidden("#contact-form"))
        self.assertTrue(self.is_hidden("#cancel-btn"))

    def test_03_hidden_immediately_after_saving_a_new_contact(self):
        self.make_contact("Grace", "Hopper")
        self.assertTrue(self.is_hidden("#cancel-btn"))

    def test_04_hidden_when_viewing_or_editing_an_existing_contact(self):
        self.page.click(".contact-list-item")
        self.page.wait_for_timeout(300)
        self.assertTrue(self.is_hidden("#cancel-btn"))

        # Editing the name alone (no unsaved email row) still shouldn't show it.
        self.page.fill("#first-name", "Grace Edited")
        self.assertTrue(self.is_hidden("#cancel-btn"))
        self.page.fill("#first-name", "Grace")  # revert the stray edit

    def test_05_visible_while_an_unsaved_email_row_exists(self):
        self.page.click("#add-email-btn")
        self.assertFalse(self.is_hidden("#cancel-btn"))

        # Removing that row directly (its own remove button) hides it again.
        self.page.click("#email-list .email-item .remove-email-btn")
        self.assertTrue(self.is_hidden("#cancel-btn"))

    def test_06_cancel_drops_the_unsaved_row_and_keeps_the_form_open(self):
        self.page.click("#add-email-btn")
        self.assertFalse(self.is_hidden("#cancel-btn"))

        self.page.click("#cancel-btn")

        self.assertFalse(self.is_hidden("#contact-form"))
        self.assertTrue(self.is_hidden("#cancel-btn"))
        self.assertEqual(
            self.page.eval_on_selector_all(
                "#email-list .email-item:not([data-email-id])", "els => els.length"
            ),
            0,
        )

    def test_07_hidden_again_after_actually_saving_a_new_email(self):
        self.page.click("#add-email-btn")
        self.page.fill("#email-list .email-input", "grace@example.com")
        with self.page.expect_response(
            lambda r: "/emails" in r.url and r.request.method == "POST"
        ):
            self.page.click("#save-btn")
        self.page.wait_for_timeout(500)

        self.assertTrue(self.is_hidden("#cancel-btn"))
        self.assertEqual(
            self.page.eval_on_selector_all(
                "#email-list .email-item[data-email-id]", "els => els.length"
            ),
            1,
        )
