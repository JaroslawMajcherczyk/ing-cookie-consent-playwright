from __future__ import annotations

import json
import re
import time
from typing import Any

import pytest
from playwright.sync_api import (
    Locator,
    Page,
    TimeoutError as PlaywrightTimeoutError,
    expect,
)

from tests.pages.cookie_preferences import CookiePreferences


BASE_URL = "https://www.ing.pl/"

CONSENT_COOKIE_NAME = "cookiePolicyGDPR"
CONSENT_DETAILS_COOKIE_NAME = "cookiePolicyGDPR__details"

MARKETING_COOKIE_NAMES = {
    "cookieSEG",
    "cookieSEG__details",
}

INCAPSULA_MESSAGE_PATTERN = re.compile(
    r"Request unsuccessful\.?\s*"
    r"Incapsula incident ID:\s*"
    r'[^"\n]+',
    re.IGNORECASE,
)


def get_cookies_by_name(
    page: Page,
) -> dict[str, dict[str, Any]]:
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


def read_incapsula_message(page: Page) -> str | None:
    """
    Odczytuje drzewo dostępności strony i zwraca komunikat
    Imperva/Incapsula, jeżeli został wyświetlony.

    Komunikat blokady może być dostępny jako nazwa elementu iframe,
    mimo że nie występuje bezpośrednio w atrybucie HTML title.
    """
    try:
        aria_snapshot = page.aria_snapshot(timeout=2_000)
    except PlaywrightTimeoutError:
        return None

    match = INCAPSULA_MESSAGE_PATTERN.search(aria_snapshot)

    if match is None:
        return None

    return match.group(0).strip()


def fail_when_ing_is_blocked(message: str) -> None:
    """
    Kończy test czytelnym komunikatem, gdy środowisko
    zostało zablokowane przez Imperva/Incapsula.
    """
    pytest.fail(
        "Strona ING nie została załadowana. "
        "Środowisko testowe zostało zablokowane przez "
        "warstwę bezpieczeństwa Imperva/Incapsula. "
        f"Komunikat: {message}",
        pytrace=False,
    )


def wait_for_initial_page_state(
    page: Page,
    timeout_ms: int = 15_000,
) -> Locator:
    """
    Oczekuje na jeden z dwóch rezultatów:

    1. pojawienie się panelu ustawień cookies;
    2. pojawienie się komunikatu blokady Incapsula.

    Zwraca locator panelu cookies, gdy strona została
    załadowana prawidłowo.
    """
    cookie_dialog = page.get_by_role("dialog")
    deadline = time.monotonic() + timeout_ms / 1000

    while time.monotonic() < deadline:
        if cookie_dialog.is_visible():
            return cookie_dialog

        incapsula_message = read_incapsula_message(page)

        if incapsula_message is not None:
            fail_when_ing_is_blocked(incapsula_message)

        page.wait_for_timeout(250)

    # Ostatnie sprawdzenie po zakończeniu oczekiwania.
    incapsula_message = read_incapsula_message(page)

    if incapsula_message is not None:
        fail_when_ing_is_blocked(incapsula_message)

    pytest.fail(
        "Nie wyświetlono panelu cookies w ciągu "
        f"{timeout_ms / 1000:.0f} sekund. "
        "Nie wykryto również komunikatu blokady Incapsula.",
        pytrace=False,
    )


def check_for_block_after_reload(
    page: Page,
    timeout_ms: int = 3_000,
) -> None:
    """
    Po przeładowaniu strony sprawdza przez określony czas,
    czy ING nie zwrócił strony blokady Incapsula.
    """
    deadline = time.monotonic() + timeout_ms / 1000

    while time.monotonic() < deadline:
        incapsula_message = read_incapsula_message(page)

        if incapsula_message is not None:
            fail_when_ing_is_blocked(incapsula_message)

        page.wait_for_timeout(250)


@pytest.mark.smoke
def test_analytics_cookie_consent_is_saved(
    page: Page,
) -> None:
    """
    Sprawdza zapisanie zgody na cookies analityczne
    oraz brak zgody na cookies marketingowe.
    """

    # Arrange — usunięcie cookies pozostałych
    # po ewentualnych wcześniejszych uruchomieniach.
    page.context.clear_cookies()

    page.goto(
        BASE_URL,
        wait_until="domcontentloaded",
        timeout=60_000,
    )

    # Oczekiwanie na panel cookies albo wykrycie blokady.
    wait_for_initial_page_state(page)

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

    # Act — włączenie cookies analitycznych
    # i zapisanie wybranych ustawień.
    cookie_preferences.accept_analytics_only()

    # Assert — odczyt cookies zapisanych
    # w kontekście przeglądarki.
    cookies_after = get_cookies_by_name(page)

    assert CONSENT_COOKIE_NAME in cookies_after, (
        f"Nie zapisano cookie {CONSENT_COOKIE_NAME}."
    )

    assert CONSENT_DETAILS_COOKIE_NAME in cookies_after, (
        f"Nie zapisano cookie "
        f"{CONSENT_DETAILS_COOKIE_NAME}."
    )

    consent_cookie = cookies_after[CONSENT_COOKIE_NAME]
    details_cookie = cookies_after[
        CONSENT_DETAILS_COOKIE_NAME
    ]

    # Wartość zaobserwowana dla konfiguracji:
    # cookies niezbędne + cookies analityczne.
    assert consent_cookie["value"] == "3", (
        "Cookie zgody ma nieoczekiwaną wartość. "
        "Oczekiwano: '3'. "
        f"Otrzymano: {consent_cookie['value']!r}."
    )

    # Weryfikacja właściwości cookie zgody.
    assert consent_cookie["domain"].endswith("ing.pl"), (
        "Cookie zgody ma nieprawidłową domenę: "
        f"{consent_cookie['domain']!r}."
    )

    assert consent_cookie["path"] == "/", (
        "Cookie zgody ma nieprawidłową ścieżkę: "
        f"{consent_cookie['path']!r}."
    )

    assert consent_cookie["expires"] > time.time(), (
        "Cookie zgody nie ma prawidłowego "
        "terminu ważności."
    )

    # Weryfikacja właściwości cookie szczegółowego.
    assert details_cookie["domain"].endswith("ing.pl"), (
        "Cookie szczegółowe ma nieprawidłową domenę: "
        f"{details_cookie['domain']!r}."
    )

    assert details_cookie["path"] == "/", (
        "Cookie szczegółowe ma nieprawidłową ścieżkę: "
        f"{details_cookie['path']!r}."
    )

    assert details_cookie["expires"] > time.time(), (
        "Cookie szczegółowe nie ma prawidłowego "
        "terminu ważności."
    )

    # Weryfikacja JSON zapisanego
    # w cookie szczegółowym.
    try:
        details_value = json.loads(
            details_cookie["value"]
        )
    except json.JSONDecodeError as error:
        pytest.fail(
            "Cookie cookiePolicyGDPR__details "
            "nie zawiera prawidłowego JSON. "
            f"Szczegóły: {error}",
            pytrace=False,
        )

    assert "cookieCreateTimestamp" in details_value, (
        "W cookie szczegółowym brakuje pola "
        "'cookieCreateTimestamp'."
    )

    created_at_ms = details_value[
        "cookieCreateTimestamp"
    ]
    current_time_ms = int(time.time() * 1000)

    assert type(created_at_ms) is int, (
        "Pole 'cookieCreateTimestamp' "
        "nie jest liczbą całkowitą."
    )

    assert abs(current_time_ms - created_at_ms) < 60_000, (
        "Czas zapisania zgody różni się od czasu "
        "wykonania testu o więcej niż 60 sekund."
    )

    # Po wyrażeniu wyłącznie zgody analitycznej
    # nie powinny zostać zapisane cookies marketingowe.
    unexpected_marketing_cookies = (
        MARKETING_COOKIE_NAMES
        & cookies_after.keys()
    )

    assert not unexpected_marketing_cookies, (
        "Zapisano cookies marketingowe mimo braku zgody: "
        f"{sorted(unexpected_marketing_cookies)}."
    )

    # Zgoda powinna pozostać zapisana
    # po przeładowaniu strony.
    page.reload(
        wait_until="domcontentloaded",
        timeout=60_000,
    )

    check_for_block_after_reload(page)

    expect(page.get_by_role("dialog")).to_be_hidden(
        timeout=10_000
    )

    cookies_after_reload = get_cookies_by_name(page)

    assert CONSENT_COOKIE_NAME in cookies_after_reload, (
        "Po przeładowaniu strony brakuje cookie "
        f"{CONSENT_COOKIE_NAME}."
    )

    assert (
        CONSENT_DETAILS_COOKIE_NAME
        in cookies_after_reload
    ), (
        "Po przeładowaniu strony brakuje cookie "
        f"{CONSENT_DETAILS_COOKIE_NAME}."
    )

    assert (
        cookies_after_reload[
            CONSENT_COOKIE_NAME
        ]["value"]
        == consent_cookie["value"]
    ), (
        "Po przeładowaniu strony zmieniła się wartość "
        f"cookie {CONSENT_COOKIE_NAME}."
    )

    assert (
        cookies_after_reload[
            CONSENT_DETAILS_COOKIE_NAME
        ]["value"]
        == details_cookie["value"]
    ), (
        "Po przeładowaniu strony zmieniła się wartość "
        f"cookie {CONSENT_DETAILS_COOKIE_NAME}."
    )