"""
The per-email remove ("-") and copy buttons are hover/focus-revealed
(opacity + pointer-events, not display, so there's no layout shift), for
both a freshly-typed unsaved row and one loaded from the server.
"""
from tests.e2e.base import E2ETestCase

ROW = "#email-list .email-item"
REMOVE_BTN = "#email-list .email-item .remove-email-btn"
COPY_BTN = "#email-list .copy-email-btn"


class TestRemoveButtonHoverReveal(E2ETestCase):
    def test_01_hidden_without_hover_on_an_unsaved_row(self):
        self.page.click("#add-contact-btn")
        self.page.fill("#first-name", "Marie")
        self.page.fill("#last-name", "Curie")
        self.page.click("#add-email-btn")
        self.page.fill("#email-list .email-input", "marie@example.com")

        # The email input keeps focus after fill(); blur it so :focus-within
        # isn't the reason the button would appear visible.
        self.page.click("#contact-list-header h1")
        self.page.wait_for_timeout(250)

        self.assertEqual(self.opacity_of(REMOVE_BTN), "0")
        self.assertEqual(self.pointer_events_of(REMOVE_BTN), "none")

    def test_02_visible_on_hover_then_hides_again_on_mouse_leave(self):
        self.page.hover(ROW)
        self.page.wait_for_timeout(250)
        self.assertEqual(self.opacity_of(REMOVE_BTN), "1")
        self.assertEqual(self.pointer_events_of(REMOVE_BTN), "auto")

        self.page.hover("#contact-list-header h1")
        self.page.wait_for_timeout(250)
        self.assertEqual(self.opacity_of(REMOVE_BTN), "0")

    def test_03_same_behavior_on_a_saved_row_loaded_from_the_server(self):
        with self.page.expect_response(
            lambda r: r.url.endswith("/api/contacts") and r.request.method == "POST"
        ):
            self.page.click("#save-btn")
        self.page.wait_for_timeout(500)
        self.assertEqual(
            self.page.eval_on_selector_all(
                "#email-list .email-item[data-email-id]", "els => els.length"
            ),
            1,
        )

        self.page.click("#contact-list-header h1")  # clear focus
        self.page.wait_for_timeout(250)
        self.assertEqual(self.opacity_of(REMOVE_BTN), "0")

        self.page.hover(ROW)
        self.page.wait_for_timeout(250)
        self.assertEqual(self.opacity_of(REMOVE_BTN), "1")

    def test_04_clicking_while_hovered_actually_removes_the_row(self):
        with self.page.expect_response(
            lambda r: "/emails/" in r.url and r.request.method == "DELETE"
        ):
            self.page.click(REMOVE_BTN)
        self.page.wait_for_timeout(500)

        self.assertEqual(
            self.page.eval_on_selector_all("#email-list .email-item", "els => els.length"), 0
        )


class TestCopyButtonHoverRevealAndClipboard(E2ETestCase):
    def test_01_no_copy_button_on_a_still_unsaved_row(self):
        self.page.click("#add-contact-btn")
        self.page.fill("#first-name", "Katherine")
        self.page.fill("#last-name", "Johnson")
        self.page.click("#add-email-btn")

        self.assertEqual(
            self.page.eval_on_selector_all(COPY_BTN, "els => els.length"), 0
        )

    def test_02_copy_button_appears_once_the_email_is_saved(self):
        self.page.fill("#email-list .email-input", "katherine@example.com")
        with self.page.expect_response(
            lambda r: r.url.endswith("/api/contacts") and r.request.method == "POST"
        ):
            self.page.click("#save-btn")
        self.page.wait_for_timeout(500)

        self.assertEqual(self.page.eval_on_selector_all(COPY_BTN, "els => els.length"), 1)

    def test_03_hover_reveals_it_like_the_remove_button(self):
        self.page.click("#contact-list-header h1")  # clear focus
        self.page.wait_for_timeout(250)
        self.assertEqual(self.opacity_of(COPY_BTN), "0")

        self.page.hover(ROW)
        self.page.wait_for_timeout(250)
        self.assertEqual(self.opacity_of(COPY_BTN), "1")

    def test_04_clicking_copies_the_address_and_flashes_copied(self):
        self.page.click(COPY_BTN)
        self.page.wait_for_timeout(200)

        clipboard_text = self.page.evaluate("navigator.clipboard.readText()")
        self.assertEqual(clipboard_text, "katherine@example.com")
        self.assertEqual(self.page.inner_text(COPY_BTN), "Copied!")

    def test_05_copied_state_persists_briefly_then_reverts(self):
        # Moving the mouse away shouldn't cut the flash short - it isn't hover-driven.
        self.page.hover("#contact-list-header h1")
        self.page.wait_for_timeout(200)
        self.assertEqual(self.page.inner_text(COPY_BTN), "Copied!")

        self.page.wait_for_timeout(1300)
        self.assertEqual(self.page.inner_text(COPY_BTN), "Copy")

    def test_06_goes_invisible_again_once_neither_hovered_nor_focused(self):
        # Chromium focuses a <button> on click, and :focus-within
        # intentionally keeps it visible for keyboard users - shift focus
        # elsewhere (not just the mouse) to test the true resting state.
        self.page.click("#first-name")
        self.page.wait_for_timeout(250)

        self.assertEqual(self.opacity_of(COPY_BTN), "0")
