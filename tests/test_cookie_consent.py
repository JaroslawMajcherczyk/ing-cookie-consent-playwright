from __future__ import annotations

import json
import time
from typing import Any

import pytest
from playwright.sync_api import Locator, Page, TimeoutError, expect

from tests.pages.cookie_preferences import CookiePreferences


BASE_URL = "https://www.ing.pl/"

CONSENT_COOKIE_NAME = "cookiePolicyGDPR"
CONSENT_DETAILS_COOKIE_NAME = "cookiePolicyGDPR__details"

MARKETING_COOKIE_NAMES = {
    "cookieSEG",
    "cookieSEG__details",
}


def get_cookies_by_name(page: Page) -> dict[str, dict[str, Any]]:
    """
    Pobiera cookies zapisane dla domeny ING.

    Zwraca słownik w formacie:
    nazwa cookie -> dane cookie.
    """
    cookies = page.context.cookies([BASE_URL])

    return {
        cookie["name"]: cookie
        for cookie in cookies
    }


def get_incapsula_frame(page: Page) -> Locator:
    """
    Zwraca locator komunikatu blokady Imperva/Incapsula.
    """
    return page.locator(
        'iframe[title*="Request unsuccessful"], '
        'iframe[title*="Incapsula incident ID"]'
    ).first


def fail_with_incapsula_message(blocked_frame: Locator) -> None:
    """
    Kończy test czytelnym komunikatem, gdy ING zablokował
    środowisko testowe.
    """
    incident_message = (
        blocked_frame.get_attribute("title")
        or "Request unsuccessful — brak numeru incydentu"
    )

    pytest.fail(
        "Strona ING nie została załadowana. "
        "Środowisko testowe zostało zablokowane przez "
        "warstwę bezpieczeństwa Imperva/Incapsula. "
        f"Komunikat: {incident_message}",
        pytrace=False,
    )


def wait_for_cookie_dialog_or_fail(page: Page) -> Locator:
    """
    Oczekuje na jeden z dwóch rezultatów:

    1. wyświetlenie panelu ustawień cookies,
    2. wyświetlenie blokady Imperva/Incapsula.
    """
    cookie_dialog = page.get_by_role("dialog")
    blocked_frame = get_incapsula_frame(page)

    page_result = cookie_dialog.or_(blocked_frame).first

    expect(page_result).to_be_visible(timeout=15_000)

    if blocked_frame.is_visible():
        fail_with_incapsula_message(blocked_frame)

    return cookie_dialog


def fail_if_ing_blocked_after_navigation(
    page: Page,
    timeout_ms: int = 3_000,
) -> None:
    """
    Sprawdza po przeładowaniu strony, czy środowisko nie zostało
    zablokowane przez Imperva/Incapsula.
    """
    blocked_frame = get_incapsula_frame(page)

    try:
        blocked_frame.wait_for(
            state="visible",
            timeout=timeout_ms,
        )
    except TimeoutError:
        return

    fail_with_incapsula_message(blocked_frame)


@pytest.mark.smoke
def test_analytics_cookie_consent_is_saved(page: Page) -> None:
    """
    Sprawdza zapisanie zgody na cookies analityczne oraz
    brak zgody na cookies marketingowe.
    """

    # Arrange — test rozpoczyna się bez cookies
    # pozostawionych przez wcześniejsze uruchomienia.
    page.context.clear_cookies()

    page.goto(
        BASE_URL,
        wait_until="domcontentloaded",
        timeout=60_000,
    )

    wait_for_cookie_dialog_or_fail(page)

    cookie_preferences = CookiePreferences(page)

    cookies_before = get_cookies_by_name(page)

    assert CONSENT_COOKIE_NAME not in cookies_before, (
        f"Cookie {CONSENT_COOKIE_NAME} istniało "
        "przed zapisaniem decyzji użytkownika."
    )

    assert CONSENT_DETAILS_COOKIE_NAME not in cookies_before, (
        f"Cookie {CONSENT_DETAILS_COOKIE_NAME} istniało "
        "przed zapisaniem decyzji użytkownika."
    )

    # Act — włączenie wyłącznie cookies analitycznych.
    cookie_preferences.accept_analytics_only()

    # Assert — odczyt cookies zapisanych w kontekście przeglądarki.
    cookies_after = get_cookies_by_name(page)

    assert CONSENT_COOKIE_NAME in cookies_after, (
        f"Nie zapisano cookie {CONSENT_COOKIE_NAME}."
    )

    assert CONSENT_DETAILS_COOKIE_NAME in cookies_after, (
        f"Nie zapisano cookie {CONSENT_DETAILS_COOKIE_NAME}."
    )

    consent_cookie = cookies_after[CONSENT_COOKIE_NAME]
    details_cookie = cookies_after[CONSENT_DETAILS_COOKIE_NAME]

    # Wartość zaobserwowana dla konfiguracji:
    # cookies niezbędne + cookies analityczne.
    assert consent_cookie["value"] == "3", (
        "Cookie zgody ma nieoczekiwaną wartość. "
        f"Oczekiwano: '3'. "
        f"Otrzymano: {consent_cookie['value']!r}."
    )

    # Weryfikacja podstawowych właściwości cookie zgody.
    assert consent_cookie["domain"].endswith("ing.pl"), (
        "Cookie zgody ma nieprawidłową domenę: "
        f"{consent_cookie['domain']!r}."
    )

    assert consent_cookie["path"] == "/", (
        "Cookie zgody ma nieprawidłową ścieżkę: "
        f"{consent_cookie['path']!r}."
    )

    assert consent_cookie["expires"] > time.time(), (
        "Cookie zgody nie ma prawidłowego terminu ważności."
    )

    # Weryfikacja podstawowych właściwości cookie szczegółowego.
    assert details_cookie["domain"].endswith("ing.pl"), (
        "Cookie szczegółowe ma nieprawidłową domenę: "
        f"{details_cookie['domain']!r}."
    )

    assert details_cookie["path"] == "/", (
        "Cookie szczegółowe ma nieprawidłową ścieżkę: "
        f"{details_cookie['path']!r}."
    )

    assert details_cookie["expires"] > time.time(), (
        "Cookie szczegółowe nie ma prawidłowego terminu ważności."
    )

    # Weryfikacja JSON zapisanego w cookie szczegółowym.
    try:
        details_value = json.loads(details_cookie["value"])
    except json.JSONDecodeError as error:
        pytest.fail(
            "Cookie cookiePolicyGDPR__details "
            f"nie zawiera prawidłowego JSON: {error}",
            pytrace=False,
        )

    assert "cookieCreateTimestamp" in details_value, (
        "W cookie szczegółowym brakuje pola "
        "'cookieCreateTimestamp'."
    )

    created_at_ms = details_value["cookieCreateTimestamp"]
    current_time_ms = int(time.time() * 1000)

    assert isinstance(created_at_ms, int), (
        "Pole 'cookieCreateTimestamp' nie jest liczbą całkowitą."
    )

    assert abs(current_time_ms - created_at_ms) < 60_000, (
        "Czas zapisania zgody różni się od czasu wykonania testu "
        "o więcej niż 60 sekund."
    )

    # Po wyrażeniu wyłącznie zgody analitycznej nie powinny
    # zostać zapisane cookies marketingowe.
    unexpected_marketing_cookies = (
        MARKETING_COOKIE_NAMES & cookies_after.keys()
    )

    assert not unexpected_marketing_cookies, (
        "Zapisano cookies marketingowe mimo braku zgody: "
        f"{sorted(unexpected_marketing_cookies)}."
    )

    # Zgoda powinna pozostać zapisana po przeładowaniu strony.
    page.reload(
        wait_until="domcontentloaded",
        timeout=60_000,
    )

    fail_if_ing_blocked_after_navigation(page)

    expect(page.get_by_role("dialog")).to_be_hidden(
        timeout=10_000
    )

    cookies_after_reload = get_cookies_by_name(page)

    assert CONSENT_COOKIE_NAME in cookies_after_reload, (
        f"Po przeładowaniu strony brakuje cookie "
        f"{CONSENT_COOKIE_NAME}."
    )

    assert CONSENT_DETAILS_COOKIE_NAME in cookies_after_reload, (
        f"Po przeładowaniu strony brakuje cookie "
        f"{CONSENT_DETAILS_COOKIE_NAME}."
    )

    assert (
        cookies_after_reload[CONSENT_COOKIE_NAME]["value"]
        == consent_cookie["value"]
    ), (
        "Po przeładowaniu strony zmieniła się wartość "
        f"cookie {CONSENT_COOKIE_NAME}."
    )

    assert (
        cookies_after_reload[CONSENT_DETAILS_COOKIE_NAME]["value"]
        == details_cookie["value"]
    ), (
        "Po przeładowaniu strony zmieniła się wartość "
        f"cookie {CONSENT_DETAILS_COOKIE_NAME}."
    )