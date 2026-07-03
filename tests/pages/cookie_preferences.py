from playwright.sync_api import Page, expect


class CookiePreferences:
    def __init__(self, page: Page) -> None:
        self.page = page
        self.dialog = page.get_by_role("dialog")

        self.customize_button = self.dialog.get_by_role(
            "button",
            name="Dostosuj",
        )

        self.analytics_toggle = self.dialog.locator(
            "div:nth-child(2) "
            "> .cookie-policy-switch "
            "> .cookie-policy-toggle-button"
        )

        self.accept_selected_button = self.dialog.get_by_role(
            "button",
            name="Zaakceptuj zaznaczone",
        )

    def accept_analytics_only(self) -> None:
        expect(self.dialog).to_be_visible(timeout=15_000)

        expect(self.customize_button).to_be_visible()
        self.customize_button.click()

        expect(self.analytics_toggle).to_be_visible()
        self.analytics_toggle.click()

        expect(self.accept_selected_button).to_be_visible()
        expect(self.accept_selected_button).to_be_enabled()
        self.accept_selected_button.click()

        expect(self.dialog).to_be_hidden(timeout=10_000)