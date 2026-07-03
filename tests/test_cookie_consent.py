from __future__ import annotations

import json
import time

import pytest
from playwright.sync_api import Page, expect

from tests.pages.cookie_preferences import CookiePreferences


BASE_URL = "https://www.ing.pl/"

CONSENT_COOKIE_NAME = "cookiePolicyGDPR"
CONSENT_DETAILS_COOKIE_NAME = "cookiePolicyGDPR__details"

MARKETING_COOKIE_NAMES = {
    "cookieSEG",
    "cookieSEG__details",
}


def get_cookies_by_name(page: Page) -> dict[str, dict]:
    """
    Pobiera cookies zapisane dla domeny ING i zwraca je
    jako słownik: nazwa cookie -> dane cookie.
    """
    cookies = page.context.cookies([BASE_URL])

    return {
        cookie["name"]: cookie
        for cookie in cookies
    }

def fail_if_ing_blocked_environment(page: Page) -> None:
    blocked_frame = page.locator(
        'iframe[title*="Incapsula incident ID"]'
    )

    if blocked_frame.count() > 0:
        incident_message = (
            blocked_frame.first.get_attribute("title")
            or "Brak numeru incydentu"
        )

        pytest.fail(
            "Strona ING nie została załadowana. "
            "Środowisko testowe zostało zablokowane przez "
            "warstwę bezpieczeństwa Imperva/Incapsula. "
            f"Komunikat: {incident_message}"
        )

@pytest.mark.smoke
def test_analytics_cookie_consent_is_saved(page: Page) -> None:
    # Arrange — test rozpoczyna się z pustym magazynem cookies.
    page.context.clear_cookies()

    page.goto(
        BASE_URL,
        wait_until="domcontentloaded",
        timeout=60_000,
    )
    fail_if_ing_blocked_environment(page)

    cookie_preferences = CookiePreferences(page)

    expect(cookie_preferences.dialog).to_be_visible(
        timeout=15_000
    )

    cookies_before = get_cookies_by_name(page)

    assert CONSENT_COOKIE_NAME not in cookies_before
    assert CONSENT_DETAILS_COOKIE_NAME not in cookies_before

    cookie_preferences.accept_analytics_only()

    # Assert — weryfikacja cookies zapisanych w przeglądarce.
    cookies_after = get_cookies_by_name(page)

    assert CONSENT_COOKIE_NAME in cookies_after, (
        f"Nie zapisano cookie {CONSENT_COOKIE_NAME}."
    )

    assert CONSENT_DETAILS_COOKIE_NAME in cookies_after, (
        f"Nie zapisano cookie {CONSENT_DETAILS_COOKIE_NAME}."
    )

    consent_cookie = cookies_after[CONSENT_COOKIE_NAME]
    details_cookie = cookies_after[CONSENT_DETAILS_COOKIE_NAME]

    # Wartość zaobserwowana dla:
    # cookies niezbędne + cookies analityczne.
    assert consent_cookie["value"] == "3", (
        "Cookie zgody ma nieoczekiwaną wartość. "
        f"Otrzymano: {consent_cookie['value']!r}"
    )

    assert consent_cookie["domain"].endswith("ing.pl")
    assert consent_cookie["path"] == "/"
    assert consent_cookie["expires"] > time.time()

    assert details_cookie["domain"].endswith("ing.pl")
    assert details_cookie["path"] == "/"
    assert details_cookie["expires"] > time.time()

    # Weryfikacja struktury cookie zawierającego szczegóły zgody.
    details_value = json.loads(details_cookie["value"])

    assert "cookieCreateTimestamp" in details_value

    created_at_ms = details_value["cookieCreateTimestamp"]
    current_time_ms = int(time.time() * 1000)

    assert abs(current_time_ms - created_at_ms) < 60_000, (
        "Czas zapisania zgody różni się od czasu wykonania testu "
        "o więcej niż 60 sekund."
    )

    # Po wyrażeniu wyłącznie zgody analitycznej nie powinny
    # pojawić się cookies marketingowe.
    unexpected_marketing_cookies = (
        MARKETING_COOKIE_NAMES & cookies_after.keys()
    )

    assert not unexpected_marketing_cookies, (
        "Zapisano cookies marketingowe mimo braku zgody: "
        f"{sorted(unexpected_marketing_cookies)}"
    )

    # Zgoda powinna przetrwać przeładowanie strony.
    page.reload(
        wait_until="domcontentloaded",
        timeout=60_000,
    )

    expect(page.get_by_role("dialog")).to_be_hidden(
        timeout=10_000
    )

    cookies_after_reload = get_cookies_by_name(page)

    assert cookies_after_reload[CONSENT_COOKIE_NAME]["value"] == "3"

    assert (
        cookies_after_reload[CONSENT_DETAILS_COOKIE_NAME]["value"]
        == details_cookie["value"]
    )