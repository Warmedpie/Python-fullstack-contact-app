/* Client side behavior */
document.addEventListener("DOMContentLoaded", () => {
    const contactList = document.getElementById("contact-list");
    const addContactBtn = document.getElementById("add-contact-btn");
    const contactSearchInput = document.getElementById("contact-search");
    const sortToggleBtn = document.getElementById("sort-toggle-btn");

    // The full, unfiltered list from the last GET /api/contacts, kept
    // around so search/sort can re-render instantly without re-fetching.
    let allContacts = [];
    let sortField = "last_name";

    const contactForm = document.getElementById("contact-form");
    const firstNameInput = document.getElementById("first-name");
    const lastNameInput = document.getElementById("last-name");

    const emailList = document.getElementById("email-list");
    const addEmailBtn = document.getElementById("add-email-btn");

    const cancelBtn = document.getElementById("cancel-btn");
    const deleteContactBtn = document.getElementById("delete-contact-btn");
    const formError = document.getElementById("form-error");

    const confirmOverlay = document.getElementById("confirm-overlay");
    const confirmMessage = document.getElementById("confirm-message");
    const confirmCancelBtn = document.getElementById("confirm-cancel-btn");
    const confirmOkBtn = document.getElementById("confirm-ok-btn");

    // -------------------------------------------------------------
    // Contact list selection
    // -------------------------------------------------------------

    contactList.addEventListener("click", (event) => {
        const item = event.target.closest(".contact-list-item");
        if (!item) return;
        selectContact(item);
    });

    function selectContact(item) {
        const current = contactList.querySelector(".is-selected");
        if (current) current.classList.remove("is-selected");
        item.classList.add("is-selected");

        contactForm.dataset.contactId = item.dataset.contactId;

        // Filling in the form's actual fields happens once getContact()
        // is implemented and calls renderContact() below with the result.
        Api.getContact(item.dataset.contactId);
    }

    // -------------------------------------------------------------
    // New contact
    // -------------------------------------------------------------

    addContactBtn.addEventListener("click", () => {
        const current = contactList.querySelector(".is-selected");
        if (current) current.classList.remove("is-selected");

        clearContactForm();
        firstNameInput.focus();
    });

    function showContactForm() {
        contactForm.classList.remove("hidden");
    }

    // Clear any default values on new contact
    function resetNameFields() {
        firstNameInput.value = "";
        firstNameInput.defaultValue = "";
        lastNameInput.value = "";
        lastNameInput.defaultValue = "";
    }

    function hideContactForm() {
        contactForm.classList.add("hidden");
        contactForm.reset();
        resetNameFields();
        contactForm.dataset.contactId = "";
        emailList.innerHTML = "";
        updateCancelVisibility();
        clearFormError();
    }

    function clearContactForm() {
        contactForm.reset();
        resetNameFields();
        contactForm.dataset.contactId = "";
        emailList.innerHTML = "";
        showContactForm();
        updateCancelVisibility();
        clearFormError();
    }

    // Error for missing fields

    function showFormError(message) {
        formError.textContent = message;
        formError.classList.remove("hidden");
    }

    function clearFormError() {
        formError.textContent = "";
        formError.classList.add("hidden");
    }

    // Cancel button visibility - show on cancelable action (adding email, making new contact)

    function updateCancelVisibility() {
        const formHidden = contactForm.classList.contains("hidden");
        const isNewContact = !contactForm.dataset.contactId;
        const hasUnsavedEmail =
            emailList.querySelector(".email-item:not([data-email-id])") !== null;

        if (!formHidden && (isNewContact || hasUnsavedEmail)) {
            cancelBtn.classList.remove("hidden");
        } else {
            cancelBtn.classList.add("hidden");
        }
    }

    // -------------------------------------------------------------
    // Emails: add a blank, editable row / remove any row
    // -------------------------------------------------------------

    addEmailBtn.addEventListener("click", () => {
        emailList.appendChild(createEmailRow());
        updateCancelVisibility();
    });

    function createEmailRow(emailAddress = "", emailId = "") {
        const li = document.createElement("li");
        li.className = "email-item";
        if (emailId) {
            li.dataset.emailId = emailId;
        }

        if (emailAddress) {
            const span = document.createElement("span");
            span.className = "email-address";
            span.textContent = emailAddress;
            li.appendChild(span);

            // Only a saved/rendered address has fixed text worth a copy
            // shortcut - a still-being-typed row is just a normal <input>,
            // which the user can already select and copy from directly.
            const copyBtn = document.createElement("button");
            copyBtn.type = "button";
            copyBtn.className = "email-action-btn copy-email-btn";
            copyBtn.setAttribute("aria-label", "Copy email");
            copyBtn.textContent = "Copy";
            li.appendChild(copyBtn);
        } else {
            const input = document.createElement("input");
            input.type = "email";
            input.className = "email-input";
            input.placeholder = "name@example.com";
            li.appendChild(input);
        }

        const removeBtn = document.createElement("button");
        removeBtn.type = "button";
        removeBtn.className = "email-action-btn remove-email-btn";
        removeBtn.setAttribute("aria-label", "Remove email");
        removeBtn.textContent = "−";
        li.appendChild(removeBtn);

        return li;
    }

    // Copy saved emails to clipboard

    function copyToClipboard(text) {
        if (navigator.clipboard && navigator.clipboard.writeText) {
            return navigator.clipboard.writeText(text);
        }

        // Fallback for browsers/contexts without the async Clipboard API.
        const textarea = document.createElement("textarea");
        textarea.value = text;
        textarea.style.position = "fixed";
        textarea.style.opacity = "0";
        document.body.appendChild(textarea);
        textarea.select();
        try {
            document.execCommand("copy");
        } finally {
            document.body.removeChild(textarea);
        }
        return Promise.resolve();
    }

    function flashCopied(button) {
        const originalText = button.textContent;
        button.textContent = "Copied!";
        button.classList.add("copied");
        setTimeout(() => {
            button.textContent = originalText;
            button.classList.remove("copied");
        }, 1200);
    }

    emailList.addEventListener("click", (event) => {
        const copyBtn = event.target.closest(".copy-email-btn");
        if (copyBtn) {
            const address = copyBtn.closest(".email-item").querySelector(".email-address").textContent;
            copyToClipboard(address)
                .then(() => flashCopied(copyBtn))
                .catch((err) => console.error("Failed to copy email", address, err));
            return;
        }

        const removeBtn = event.target.closest(".remove-email-btn");
        if (!removeBtn) return;

        const row = removeBtn.closest(".email-item");
        const emailId = row.dataset.emailId;
        const contactId = contactForm.dataset.contactId;

        row.remove();
        updateCancelVisibility();

        // A saved email also needs deleting server-side - that call is a
        // no-op until Api.removeEmail() is implemented.
        if (emailId) {
            Api.removeEmail(contactId, emailId);
        }
    });

    // -------------------------------------------------------------
    // Cancel: drop unsaved changes
    // -------------------------------------------------------------

    cancelBtn.addEventListener("click", () => {
        // Cancelling a not-yet-saved new contact goes back to "nothing
        // selected" rather than leaving an empty form on screen.
        if (!contactForm.dataset.contactId) {
            hideContactForm();
            return;
        }

        contactForm.reset();
        emailList
            .querySelectorAll(".email-item:not([data-email-id])")
            .forEach((row) => row.remove());
        updateCancelVisibility();
        clearFormError();
    });

    // -------------------------------------------------------------
    // Confirmation modal - used to guard destructive actions (delete)
    // instead of a native confirm().
    // -------------------------------------------------------------

    let confirmAction = null;

    function showConfirm(message, onConfirm) {
        confirmMessage.textContent = message;
        confirmAction = onConfirm;
        confirmOverlay.classList.remove("hidden");
    }

    function hideConfirm() {
        confirmOverlay.classList.add("hidden");
        confirmAction = null;
    }

    confirmCancelBtn.addEventListener("click", hideConfirm);

    confirmOkBtn.addEventListener("click", () => {
        const action = confirmAction;
        hideConfirm();
        if (action) action();
    });

    // Clicking the dimmed backdrop (not the dialog box itself) also cancels.
    confirmOverlay.addEventListener("click", (event) => {
        if (event.target === confirmOverlay) hideConfirm();
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && !confirmOverlay.classList.contains("hidden")) {
            hideConfirm();
        }
    });

    // -------------------------------------------------------------
    // Save / Delete - stubbed until api.js is wired up
    // -------------------------------------------------------------

    contactForm.addEventListener("submit", (event) => {
        event.preventDefault();
        clearFormError();

        const contactId = contactForm.dataset.contactId;
        const payload = {
            first_name: firstNameInput.value,
            last_name: lastNameInput.value,
        };

        if (contactId) {
            Api.updateContact(contactId, payload);
        } else {
            Api.createContact(payload);
        }
    });

    deleteContactBtn.addEventListener("click", () => {
        const contactId = contactForm.dataset.contactId;
        if (!contactId) return;

        const name = `${firstNameInput.value} ${lastNameInput.value}`.trim() || "this contact";
        showConfirm(`Delete ${name}? This can't be undone.`, () => {
            Api.deleteContact(contactId);
        });
    });

    // -------------------------------------------------------------
    // Rendering hooks - call these once api.js actually fetches data.
    // Exposed on window.App so api.js can reach them without a bundler.
    // -------------------------------------------------------------

    function renderContactList(contacts) {
        allContacts = contacts;
        renderVisibleContactList();
    }

    // Re-applies the current search text and sort field to the
    // last-fetched contact list, without hitting the server again.
    function renderVisibleContactList() {
        const query = contactSearchInput.value.trim().toLowerCase();
        const visible = allContacts.filter((contact) => {
            const fullName = `${contact.first_name || ""} ${contact.last_name || ""}`.toLowerCase();
            return fullName.includes(query);
        });

        sortContacts(visible);

        contactList.innerHTML = "";

        if (visible.length === 0) {
            const li = document.createElement("li");
            li.className = "contact-list-empty";
            li.textContent = query ? "No matching contacts" : "No contacts yet";
            contactList.appendChild(li);
        } else {
            visible.forEach((contact) => {
                const li = document.createElement("li");
                li.className = "contact-list-item";
                li.dataset.contactId = contact.id;
                li.textContent = `${contact.first_name} ${contact.last_name || ""}`.trim();
                contactList.appendChild(li);
            });
        }

        // The list was just rebuilt from scratch, so re-apply the
        // selection highlight (a no-op if that contact isn't visible
        // right now, e.g. filtered out by the search box).
        const currentId = contactForm.dataset.contactId;
        if (currentId) selectContactInList(currentId);
    }

    // Sorts in place by the active field (last name or first name),
    // falling back to the other name as a tiebreaker.
    function sortContacts(contacts) {
        const secondaryField = sortField === "first_name" ? "last_name" : "first_name";
        contacts.sort((a, b) => {
            const primary = (a[sortField] || "").localeCompare(b[sortField] || "", undefined, { sensitivity: "base" });
            if (primary !== 0) return primary;
            return (a[secondaryField] || "").localeCompare(b[secondaryField] || "", undefined, { sensitivity: "base" });
        });
        return contacts;
    }

    contactSearchInput.addEventListener("input", renderVisibleContactList);

    sortToggleBtn.addEventListener("click", () => {
        sortField = sortField === "last_name" ? "first_name" : "last_name";
        sortToggleBtn.textContent = sortField === "last_name" ? "Sort: Last name" : "Sort: First name";
        renderVisibleContactList();
    });

    function renderContact(contact) {
        showContactForm();
        clearFormError();
        contactForm.dataset.contactId = contact.id;
        firstNameInput.value = contact.first_name || "";
        lastNameInput.value = contact.last_name || "";

        // form.reset() (used by the Cancel button) restores inputs to their
        // defaultValue, not whatever was last assigned via .value - without
        // this, Cancel on an existing contact would revert the fields to
        // blank instead of back to the saved values.
        firstNameInput.defaultValue = firstNameInput.value;
        lastNameInput.defaultValue = lastNameInput.value;

        emailList.innerHTML = "";
        (contact.emails || []).forEach((email) => {
            emailList.appendChild(createEmailRow(email.email, email.id));
        });

        updateCancelVisibility();
    }

    function selectContactInList(contactId) {
        const current = contactList.querySelector(".is-selected");
        if (current) current.classList.remove("is-selected");

        const item = contactList.querySelector(`[data-contact-id="${contactId}"]`);
        if (item) item.classList.add("is-selected");
    }

    window.App = {
        renderContactList,
        renderContact,
        clearContactForm,
        hideContactForm,
        selectContactInList,
        showFormError,
    };

    // -------------------------------------------------------------
    // Initial load
    // -------------------------------------------------------------
    Api.getContacts();
});
