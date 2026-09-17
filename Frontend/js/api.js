/*  Backend API client. */
const API_BASE = "/api";

async function request(method, path, body) {
    const response = await fetch(`${API_BASE}${path}`, {
        method,
        headers: body ? { "Content-Type": "application/json" } : undefined,
        body: body ? JSON.stringify(body) : undefined,
    });

    if (!response.ok) {
        let message = `${method} ${path} failed (${response.status})`;
        try {
            const errorBody = await response.json();
            if (errorBody && errorBody.error) {
                message = errorBody.error;
            }
        } catch (_) {
            // no JSON body on the error response - keep the generic message
        }
        throw new Error(message);
    }

    // DELETE endpoints return 204 No Content - nothing to parse.
    if (response.status === 204) {
        return null;
    }
    return response.json();
}

/* POST request for adding emails */
async function saveNewEmails(contactId) {
    const unsavedRows = document.querySelectorAll(
        "#email-list .email-item:not([data-email-id])"
    );

    for (const row of unsavedRows) {
        const input = row.querySelector("input.email-input");
        const value = input ? input.value.trim() : "";
        if (!value) continue;

        try {
            await request("POST", `/contacts/${contactId}/emails`, { email: value });
        } catch (err) {
            console.error("Failed to save email", value, err);
            window.App.showFormError(err.message);
        }
    }
}

const Api = {
    // GET /api/contacts
    async getContacts() {
        try {
            const contacts = await request("GET", "/contacts");
            window.App.renderContactList(contacts);
        } catch (err) {
            console.error("Failed to load contacts", err);
        }
    },

    // GET /api/contacts/<contactId>
    async getContact(contactId) {
        try {
            const contact = await request("GET", `/contacts/${contactId}`);
            window.App.renderContact(contact);
        } catch (err) {
            console.error("Failed to load contact", contactId, err);
        }
    },

    // POST /api/contacts   body: { first_name, last_name }
    async createContact(contact) {
        try {
            const created = await request("POST", "/contacts", contact);
            await saveNewEmails(created.id);
            await Api.getContacts();
            await Api.getContact(created.id);
            window.App.selectContactInList(created.id);
        } catch (err) {
            console.error("Failed to create contact", err);
            window.App.showFormError(err.message);
        }
    },

    // PUT /api/contacts/<contactId>   body: { first_name, last_name }
    async updateContact(contactId, contact) {
        try {
            await request("PUT", `/contacts/${contactId}`, contact);
            await saveNewEmails(contactId);
            await Api.getContacts();
            await Api.getContact(contactId);
            window.App.selectContactInList(contactId);
        } catch (err) {
            console.error("Failed to update contact", contactId, err);
            window.App.showFormError(err.message);
        }
    },

    // DELETE /api/contacts/<contactId>
    async deleteContact(contactId) {
        try {
            await request("DELETE", `/contacts/${contactId}`);
            window.App.hideContactForm();
            await Api.getContacts();
        } catch (err) {
            console.error("Failed to delete contact", contactId, err);
            window.App.showFormError(err.message);
        }
    },

    // POST /api/contacts/<contactId>/emails   body: { email }
    async addEmail(contactId, email) {
        try {
            await request("POST", `/contacts/${contactId}/emails`, { email });
        } catch (err) {
            console.error("Failed to add email", email, err);
            window.App.showFormError(err.message);
        }
    },

    // DELETE /api/contacts/<contactId>/emails/<emailId>
    async removeEmail(contactId, emailId) {
        try {
            await request("DELETE", `/contacts/${contactId}/emails/${emailId}`);
        } catch (err) {
            console.error("Failed to remove email", emailId, err);
            window.App.showFormError(err.message);
        }
    },
};
