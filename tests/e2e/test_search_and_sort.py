"""
The client-side search box and sort-toggle button on the contact list:
default sort by last name, toggling to first name and back, live
case-insensitive filtering with a helpful empty state, and the selection
highlight surviving a search/sort re-render.
"""
from tests.e2e.base import E2ETestCase


class TestSearchAndSort(E2ETestCase):
    def test_01_empty_state_and_default_sort_label(self):
        self.assertEqual(self.page.inner_text("#contact-list"), "No contacts yet")
        self.assertEqual(self.page.inner_text("#sort-toggle-btn"), "Sort: Last name")

    def test_02_default_sort_is_by_last_name(self):
        # Deliberately created out of alphabetical order.
        self.make_contact("Charlie", "Zeta")
        self.make_contact("Alice", "Yankee")
        self.make_contact("Bob", "Xray")

        self.assertEqual(
            self.contact_list_texts(), ["Bob Xray", "Alice Yankee", "Charlie Zeta"]
        )

    def test_03_toggle_switches_to_first_name_and_back(self):
        self.page.click("#sort-toggle-btn")
        self.assertEqual(self.page.inner_text("#sort-toggle-btn"), "Sort: First name")
        self.assertEqual(
            self.contact_list_texts(), ["Alice Yankee", "Bob Xray", "Charlie Zeta"]
        )

        self.page.click("#sort-toggle-btn")
        self.assertEqual(self.page.inner_text("#sort-toggle-btn"), "Sort: Last name")
        self.assertEqual(
            self.contact_list_texts(), ["Bob Xray", "Alice Yankee", "Charlie Zeta"]
        )

    def test_04_search_filters_live_and_case_insensitively(self):
        self.page.fill("#contact-search", "ali")
        self.page.wait_for_timeout(150)
        self.assertEqual(self.contact_list_texts(), ["Alice Yankee"])

        self.page.fill("#contact-search", "ALICE")
        self.page.wait_for_timeout(150)
        self.assertEqual(self.contact_list_texts(), ["Alice Yankee"])

        self.page.fill("#contact-search", "zeta")  # matches on last name too
        self.page.wait_for_timeout(150)
        self.assertEqual(self.contact_list_texts(), ["Charlie Zeta"])

    def test_05_no_match_shows_helpful_empty_state(self):
        self.page.fill("#contact-search", "nobody-like-this")
        self.page.wait_for_timeout(150)
        self.assertEqual(self.page.inner_text("#contact-list"), "No matching contacts")

    def test_06_clearing_search_restores_the_full_list(self):
        self.page.fill("#contact-search", "")
        self.page.wait_for_timeout(150)
        self.assertEqual(
            self.contact_list_texts(), ["Bob Xray", "Alice Yankee", "Charlie Zeta"]
        )

    def test_07_selection_highlight_survives_search_and_sort_rerenders(self):
        self.page.click("text=Alice Yankee")
        self.page.wait_for_timeout(300)
        self.assertEqual(self.page.input_value("#first-name"), "Alice")

        self.page.click("#sort-toggle-btn")
        self.assertEqual(
            self.page.eval_on_selector(".contact-list-item.is-selected", "el => el.textContent"),
            "Alice Yankee",
        )

        self.page.fill("#contact-search", "a")
        self.page.wait_for_timeout(150)
        self.assertEqual(
            self.page.eval_on_selector(
                ".contact-list-item.is-selected", "el => el && el.textContent"
            ),
            "Alice Yankee",
        )

    def test_08_form_stays_open_when_selected_contact_is_filtered_out(self):
        self.page.fill("#contact-search", "zeta")
        self.page.wait_for_timeout(150)

        self.assertFalse(self.is_hidden("#contact-form"))
        self.assertEqual(self.page.input_value("#first-name"), "Alice")
