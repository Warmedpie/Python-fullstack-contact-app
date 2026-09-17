"""
The contact-detail panel should be hidden until something is selected or
being created, and should hide again after a delete - across creating,
selecting, cancelling, and deleting a contact.
"""
from tests.e2e.base import E2ETestCase


class TestContactLifecycle(E2ETestCase):
    def test_01_form_hidden_and_list_empty_on_initial_load(self):
        self.assertTrue(self.is_hidden("#contact-form"))
        self.assertEqual(self.contact_count(), 0)

    def test_02_add_button_shows_an_empty_form(self):
        self.page.click("#add-contact-btn")

        self.assertFalse(self.is_hidden("#contact-form"))
        self.assertEqual(self.page.input_value("#first-name"), "")
        self.assertEqual(
            self.page.eval_on_selector("#contact-form", "el => el.dataset.contactId"), ""
        )

    def test_03_saving_a_new_contact_selects_it_in_the_list(self):
        self.page.fill("#first-name", "Ada")
        self.page.fill("#last-name", "Lovelace")
        self.page.click("#add-email-btn")
        self.page.fill("#email-list .email-input", "ada@example.com")
        with self.page.expect_response(
            lambda r: r.url.endswith("/api/contacts") and r.request.method == "POST"
        ):
            self.page.click("#save-btn")
        self.page.wait_for_timeout(500)

        self.assertFalse(self.is_hidden("#contact-form"))
        self.assertNotEqual(
            self.page.eval_on_selector("#contact-form", "el => el.dataset.contactId"), ""
        )
        self.assertEqual(self.contact_count(), 1)
        self.assertTrue(
            self.page.eval_on_selector(
                ".contact-list-item", "el => el.classList.contains('is-selected')"
            )
        )

    def test_04_cancel_on_a_new_unsaved_contact_hides_the_form(self):
        self.page.click("#add-contact-btn")
        self.assertFalse(self.is_hidden("#contact-form"))

        self.page.click("#cancel-btn")

        self.assertTrue(self.is_hidden("#contact-form"))
        self.assertEqual(self.contact_count(), 1)  # Ada, from the previous test, untouched

    def test_05_selecting_an_existing_contact_populates_the_form(self):
        self.page.click(".contact-list-item")
        self.page.wait_for_timeout(300)

        self.assertFalse(self.is_hidden("#contact-form"))
        self.assertEqual(self.page.input_value("#first-name"), "Ada")

    def test_06_cancel_on_an_existing_contact_drops_only_the_unsaved_edit(self):
        # Cancel only appears while there's something unsaved to drop -
        # adding an email row here is what makes it clickable at all.
        self.page.click("#add-email-btn")
        self.assertFalse(self.is_hidden("#cancel-btn"))

        self.page.fill("#first-name", "Changed")
        self.page.click("#cancel-btn")

        self.assertFalse(self.is_hidden("#contact-form"))
        self.assertEqual(self.page.input_value("#first-name"), "Ada")
        self.assertTrue(self.is_hidden("#cancel-btn"))

    def test_07_confirming_delete_removes_the_contact_and_hides_the_form(self):
        self.page.click("#delete-contact-btn")
        with self.page.expect_response(
            lambda r: "/api/contacts/" in r.url and r.request.method == "DELETE"
        ):
            self.page.click("#confirm-ok-btn")
        self.page.wait_for_timeout(500)

        self.assertTrue(self.is_hidden("#contact-form"))
        self.assertEqual(self.contact_count(), 0)
