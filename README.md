# Sposób uruchomienia testu — ING Cookie Consent

Automatyczny test E2E panelu zgód cookies na stronie [ing.pl](https://www.ing.pl/), przygotowany w języku Python z wykorzystaniem Playwright oraz pytest.

**Repozytorium:**  
https://github.com/JaroslawMajcherczyk/ing-cookie-consent-playwright

---

## Cel zadania

Test automatyzuje następujący scenariusz:

1. Otwiera stronę `https://www.ing.pl/`.
2. W panelu cookies wybiera opcję **Dostosuj**.
3. Włącza zgodę na cookies analityczne.
4. Pozostawia cookies marketingowe wyłączone.
5. Klika **Zaakceptuj zaznaczone**.
6. Sprawdza cookies zapisane w kontekście przeglądarki.
7. Przeładowuje stronę i potwierdza trwałość zapisanej decyzji.

## Zakres weryfikacji

Test sprawdza, że:

- przed wykonaniem scenariusza nie istnieją cookies przechowujące decyzję użytkownika;
- po zaakceptowaniu ustawień zapisane zostają:
  - `cookiePolicyGDPR`,
  - `cookiePolicyGDPR__details`;
- `cookiePolicyGDPR` ma wartość `3`, zaobserwowaną dla konfiguracji „cookies niezbędne + analityczne”;
- `cookiePolicyGDPR__details` zawiera poprawny JSON z polem `cookieCreateTimestamp`;
- czas zapisania decyzji odpowiada czasowi wykonania testu;
- cookies mają prawidłową domenę, ścieżkę i termin ważności;
- nie zostały zapisane cookies marketingowe:
  - `cookieSEG`,
  - `cookieSEG__details`;
- po przeładowaniu strony decyzja nadal jest dostępna;
- panel cookies nie pojawia się ponownie po zapisaniu ustawień.

---

## Technologie

- Python
- Playwright
- pytest
- pytest-playwright
- pytest-xdist
- GitHub Actions

## Sprawdzone środowiska

| Środowisko | Python | Przeglądarki |
|---|---:|---|
| Manjaro / Arch Linux — lokalnie | 3.14.5 | Chromium, Firefox |
| GitHub Actions — konfiguracja CI | 3.13 | Chromium, Firefox, WebKit |
| Windows 11+ | 3.13 zalecany | Chromium, Firefox, WebKit |

Playwright korzysta z własnych, wersjonowanych binariów przeglądarek. Nie wymaga używania lokalnie zainstalowanego Chrome, Firefoksa ani Safari.

---

## Struktura projektu

```text
ing-cookie-consent-playwright/
├── .github/
│   └── workflows/
│       └── playwright.yml
├── tests/
│   ├── pages/
│   │   ├── __init__.py
│   │   └── cookie_preferences.py
│   ├── __init__.py
│   └── test_cookie_consent.py
├── .gitignore
├── conftest.py
├── pytest.ini
├── requirements.txt
└── README.md
```

Katalog `test-results/` nie jest częścią kodu źródłowego. Jest tworzony podczas uruchamiania testów z włączonym zapisem wyników i powinien znajdować się w `.gitignore`.

### Najważniejsze pliki i katalogi

| Element | Odpowiedzialność |
|---|---|
| `tests/test_cookie_consent.py` | scenariusz testowy i sprawdzenie zapisanych cookies |
| `tests/pages/cookie_preferences.py` | obsługa panelu zgód cookies zgodnie z Page Object Model |
| `conftest.py` | wspólna konfiguracja kontekstu przeglądarki |
| `pytest.ini` | konfiguracja pytest i markerów |
| `requirements.txt` | przypięte zależności projektu |
| `.github/workflows/playwright.yml` | pipeline cross-browser w GitHub Actions |
| `test-results/` | generowane lokalnie lub w CI raporty i materiały diagnostyczne |

---

# Instalacja i uruchomienie

## 1. Pobranie projektu

```bash
git clone https://github.com/JaroslawMajcherczyk/ing-cookie-consent-playwright.git
cd ing-cookie-consent-playwright
```

# 2. Linux

## 2.1. Utworzenie środowiska wirtualnego

```bash
python3 -m venv .venv
```

Aktualizacja `pip`:

```bash
.venv/bin/python -m pip install --upgrade pip
```

Instalacja zależności projektu:

```bash
.venv/bin/python -m pip install -r requirements.txt
```

## 2.2. Instalacja przeglądarek

### Ubuntu / Debian

Na oficjalnie wspieranych dystrybucjach Playwright może zainstalować przeglądarki wraz z wymaganymi bibliotekami systemowymi:

```bash
.venv/bin/python -m playwright install --with-deps chromium firefox webkit
```

Polecenie może wymagać podania hasła administratora.

### Arch Linux / Manjaro

Instalacja binariów przeglądarek:

```bash
.venv/bin/python -m playwright install chromium firefox webkit
```

Arch Linux i Manjaro nie należą do oficjalnie wspieranych przez Playwright dystrybucji Linux. Chromium i Firefox mogą działać prawidłowo, natomiast WebKit może nie uruchomić się z powodu różnic w bibliotekach systemowych. W takim przypadku WebKit należy zweryfikować w GitHub Actions.

## 2.3. Podstawowe uruchamianie testów na Linuxie

### Chromium

```bash
.venv/bin/python -m pytest tests/test_cookie_consent.py \
  --browser chromium \
  -v
```

### Chromium z widocznym oknem

```bash
.venv/bin/python -m pytest tests/test_cookie_consent.py \
  --browser chromium \
  --headed \
  -v
```

### Chromium i Firefox

Polecenie zalecane lokalnie na Manjaro:

```bash
.venv/bin/python -m pytest tests/test_cookie_consent.py \
  --browser chromium \
  --browser firefox \
  -v
```

### Wszystkie trzy silniki

```bash
.venv/bin/python -m pytest tests/test_cookie_consent.py \
  --browser chromium \
  --browser firefox \
  --browser webkit \
  -v
```

### Wszystkie trzy silniki równolegle

```bash
.venv/bin/python -m pytest tests/test_cookie_consent.py \
  --browser chromium \
  --browser firefox \
  --browser webkit \
  -n 3 \
  -v
```

Opcja `-n 3` pochodzi z `pytest-xdist` i uruchamia trzy procesy robocze.

## 2.4. Uruchomienie z zapisem wyników na Linuxie

Samo polecenie `pytest ... -v` nie musi utworzyć katalogów z raportami. Aby jawnie zapisać raport JUnit oraz materiały diagnostyczne, należy użyć parametrów `--output`, `--junitxml`, `--tracing` i `--screenshot`.

### Jedna przeglądarka

```bash
mkdir -p test-results/chromium

.venv/bin/python -m pytest tests/test_cookie_consent.py \
  --browser chromium \
  --tracing=retain-on-failure \
  --screenshot=only-on-failure \
  --full-page-screenshot \
  --output=test-results/chromium \
  --junitxml=test-results/chromium/junit.xml \
  -v
```

Po poprawnym wykonaniu powinien powstać co najmniej:

```text
test-results/
└── chromium/
    └── junit.xml
```

### Osobne katalogi dla Chromium i Firefox

```bash
rm -rf test-results

for browser in chromium firefox; do
  mkdir -p "test-results/$browser"

  .venv/bin/python -m pytest tests/test_cookie_consent.py \
    --browser "$browser" \
    --tracing=retain-on-failure \
    --screenshot=only-on-failure \
    --full-page-screenshot \
    --output="test-results/$browser" \
    --junitxml="test-results/$browser/junit.xml" \
    -v
done
```

Po wykonaniu:

```text
test-results/
├── chromium/
│   └── junit.xml
└── firefox/
    └── junit.xml
```


---

# 3. Windows

Poniższe polecenia są przeznaczone dla PowerShell.

## 3.1. Sprawdzenie Pythona

```powershell
py -3.13 --version
```

Gdy polecenie `py` nie jest dostępne:

```powershell
python --version
```

Zalecana wersja to Python 3.13, zgodna ze środowiskiem GitHub Actions.

## 3.2. Utworzenie środowiska wirtualnego

```powershell
py -3.13 -m venv .venv
```

Alternatywnie:

```powershell
python -m venv .venv
```

Nie trzeba aktywować środowiska. Dalsze polecenia korzystają bezpośrednio z interpretera w `.venv`.

## 3.3. Instalacja zależności

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 3.4. Instalacja przeglądarek

```powershell
.\.venv\Scripts\python.exe -m playwright install chromium firefox webkit
```

## 3.5. Podstawowe uruchamianie testów na Windows

### Chromium

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_cookie_consent.py `
  --browser chromium `
  -v
```

### Chromium z widocznym oknem

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_cookie_consent.py `
  --browser chromium `
  --headed `
  -v
```

### Wszystkie trzy silniki

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_cookie_consent.py `
  --browser chromium `
  --browser firefox `
  --browser webkit `
  -v
```

### Wszystkie trzy silniki równolegle

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_cookie_consent.py `
  --browser chromium `
  --browser firefox `
  --browser webkit `
  -n 3 `
  -v
```

PowerShell używa znaku `` ` `` do kontynuowania polecenia w następnym wierszu.

## 3.6. Uruchomienie z zapisem wyników na Windows

### Jedna przeglądarka

```powershell
New-Item -ItemType Directory -Force test-results\chromium

.\.venv\Scripts\python.exe -m pytest tests/test_cookie_consent.py `
  --browser chromium `
  --tracing=retain-on-failure `
  --screenshot=only-on-failure `
  --full-page-screenshot `
  --output=test-results/chromium `
  --junitxml=test-results/chromium/junit.xml `
  -v
```

Po poprawnym wykonaniu powinien powstać co najmniej:

```text
test-results/
└── chromium/
    └── junit.xml
```

### Osobne katalogi dla Chromium, Firefox i WebKit

```powershell
Remove-Item test-results -Recurse -Force -ErrorAction SilentlyContinue

$Browsers = @("chromium", "firefox", "webkit")

foreach ($Browser in $Browsers) {
    New-Item -ItemType Directory -Force "test-results\$Browser"

    .\.venv\Scripts\python.exe -m pytest tests/test_cookie_consent.py `
      --browser $Browser `
      --tracing=retain-on-failure `
      --screenshot=only-on-failure `
      --full-page-screenshot `
      --output="test-results/$Browser" `
      --junitxml="test-results/$Browser/junit.xml" `
      -v
}
```

Po wykonaniu:

```text
test-results/
├── chromium/
│   └── junit.xml
├── firefox/
│   └── junit.xml
└── webkit/
    └── junit.xml
```

---

## Oczekiwany rezultat

Uruchomienie w jednej przeglądarce:

```text
tests/test_cookie_consent.py::test_analytics_cookie_consent_is_saved[chromium] PASSED

1 passed
```

Uruchomienie w Chromium i Firefox:

```text
test_analytics_cookie_consent_is_saved[chromium] PASSED
test_analytics_cookie_consent_is_saved[firefox] PASSED

2 passed
```

Uruchomienie we wszystkich silnikach:

```text
test_analytics_cookie_consent_is_saved[chromium] PASSED
test_analytics_cookie_consent_is_saved[firefox] PASSED
test_analytics_cookie_consent_is_saved[webkit] PASSED

3 passed
```

---

## Implementacja

### Page Object Model

Operacje wykonywane na panelu cookies zostały wydzielone do klasy `CookiePreferences`.

```python
from playwright.sync_api import Page, expect


class CookiePreferences:
    def __init__(self, page: Page) -> None:
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

        self.customize_button.click()
        self.analytics_toggle.click()
        self.accept_selected_button.click()

        expect(self.dialog).to_be_hidden(timeout=10_000)
```

Kod odpowiedzialny za obsługę interfejsu jest dzięki temu oddzielony od logiki sprawdzającej wynik testu. Zmiana struktury panelu cookies wymaga aktualizacji locatorów tylko w jednym pliku.

### Odczyt cookies z kontekstu przeglądarki

```python
def get_cookies_by_name(page: Page) -> dict[str, dict]:
    cookies = page.context.cookies(["https://www.ing.pl/"])

    return {
        cookie["name"]: cookie
        for cookie in cookies
    }
```

### Kluczowe weryfikacje

```python
cookies_after = get_cookies_by_name(page)

assert "cookiePolicyGDPR" in cookies_after
assert "cookiePolicyGDPR__details" in cookies_after

assert cookies_after["cookiePolicyGDPR"]["value"] == "3"

unexpected_marketing_cookies = {
    "cookieSEG",
    "cookieSEG__details",
} & cookies_after.keys()

assert not unexpected_marketing_cookies
```

Test dodatkowo sprawdza JSON zapisany w `cookiePolicyGDPR__details`, czas utworzenia decyzji, domenę, ścieżkę, termin ważności i zachowanie po przeładowaniu strony.

---

## Powtarzalność testu

W projekcie zastosowano następujące mechanizmy ograniczające niestabilność testu:

- każdy test korzysta z izolowanego `BrowserContext`;
- magazyn cookies jest jawnie czyszczony przed scenariuszem;
- konfiguracja ustala locale, strefę czasową i viewport;
- `expect` automatycznie oczekuje na właściwy stan elementu;
- test nie używa stałych opóźnień typu `time.sleep()`;
- zależności są przypięte w `requirements.txt`;
- przeglądarki są instalowane przez Playwright i dopasowane do wersji biblioteki;
- CI korzysta z określonej wersji Pythona i runnera Ubuntu;
- raport JUnit jest generowany przy każdym uruchomieniu z parametrem `--junitxml`;
- po niepowodzeniu, przy użyciu właściwych parametrów, zachowywane są trace i screenshot;
- test nie zależy od stanu pozostawionego przez wcześniejsze uruchomienia.

---
## GitHub Actions — testy cross-browser

Pipeline znajduje się w pliku:

```text
.github/workflows/playwright.yml
```

Workflow uruchamia się:

- po wykonaniu `push` do gałęzi `main` lub `master`;
- po utworzeniu `pull_request` do gałęzi `main` lub `master`;
- ręcznie przez opcję **Run workflow** w zakładce GitHub Actions.

Najważniejszy fragment konfiguracji:

```yaml
strategy:
  fail-fast: false
  matrix:
    browser:
      - chromium
      - firefox
      - webkit
```

Macierz tworzy trzy niezależne joby:

```text
Browser - chromium
Browser - firefox
Browser - webkit
```

Joby mogą być wykonywane równolegle. Ustawienie:

```yaml
fail-fast: false
```

powoduje, że niepowodzenie jednego wariantu nie anuluje pozostałych testów.

Każdy job:

1. pobiera kod repozytorium;
2. ustawia Python 3.13;
3. instaluje zależności z `requirements.txt`;
4. instaluje odpowiednią przeglądarkę oraz wymagane biblioteki systemowe;
5. uruchamia test;
6. generuje raport JUnit;
7. publikuje katalog wynikowy jako artefakt GitHub Actions.

### Ograniczenie środowiska GitHub-hosted

Podczas wykonanych prób standardowe runnery GitHub-hosted zostały
zablokowane przez warstwę bezpieczeństwa Imperva/Incapsula używaną
przez serwis ING.

Zamiast właściwej strony zwracany był komunikat:

```text
Request unsuccessful. Incapsula incident ID: ...
```

W takiej sytuacji test kończy się niepowodzeniem przed rozpoczęciem
interakcji z panelem cookies, ponieważ testowana aplikacja nie została
załadowana.

Nie jest to błąd locatorów, kodu testu ani instalacji przeglądarki.
Jest to ograniczenie dostępu do zewnętrznego serwisu z adresów IP
używanych przez współdzielone runnery GitHub Actions.

Test rozpoznaje tę sytuację i zwraca jednoznaczny komunikat:

```text
Strona ING nie została załadowana.
Środowisko testowe zostało zablokowane przez
warstwę bezpieczeństwa Imperva/Incapsula.
```

Mimo blokady aplikacji pipeline potwierdza poprawne działanie:

- macierzy trzech przeglądarek;
- instalacji Chromium, Firefox i WebKit;
- niezależnego wykonywania jobów;
- generowania raportów JUnit;
- zachowywania trace i screenshotów po błędzie;
- publikowania artefaktów diagnostycznych.

Pełny scenariusz został zweryfikowany lokalnie w oficjalnym
kontenerze Playwright.

---

## Lokalne testy cross-browser w Dockerze

Pełny test Chromium, Firefox i WebKit można uruchomić lokalnie
w oficjalnym kontenerze Playwright opartym na Ubuntu.

Rozwiązanie pozwala uruchomić WebKit także na systemach, które nie są
oficjalnie wspierane przez Playwright, takich jak Arch Linux lub Manjaro.

Wersja obrazu Docker musi być zgodna z wersją biblioteki Playwright
zapisaną w `requirements.txt`.

W projekcie używana jest wersja:

```text
playwright==1.61.0
```

Dlatego należy użyć obrazu:

```text
mcr.microsoft.com/playwright/python:v1.61.0-noble
```

Uruchomienie trzech przeglądarek równolegle:

```bash
docker run --rm --pull=always --ipc=host \
  -v "$PWD":/work \
  -w /work \
  mcr.microsoft.com/playwright/python:v1.61.0-noble \
  bash -lc '
    python -m pip install -r requirements.txt &&
    python -m pytest tests/test_cookie_consent.py \
      --browser chromium \
      --browser firefox \
      --browser webkit \
      -n 3 \
      -v
  '
```

Znaczenie parametrów:

- `--rm` — usuwa kontener po zakończeniu;
- `--pull=always` — sprawdza i pobiera wskazaną wersję obrazu;
- `--ipc=host` — udostępnia przeglądarkom pamięć współdzieloną hosta;
- `-v "$PWD":/work` — udostępnia katalog projektu wewnątrz kontenera;
- `-w /work` — ustawia katalog roboczy;
- `-n 3` — uruchamia trzy procesy testowe przez `pytest-xdist`.

Zweryfikowany wynik:

```text
test_analytics_cookie_consent_is_saved[chromium] PASSED
test_analytics_cookie_consent_is_saved[firefox] PASSED
test_analytics_cookie_consent_is_saved[webkit] PASSED

3 passed in 9.89s
```

Wynik potwierdza poprawne działanie scenariusza w trzech silnikach
przeglądarek.

Przy zmianie wersji Playwright w `requirements.txt` należy również
zmienić wersję obrazu Docker.

Przykład:

```text
playwright==1.62.0
```

wymaga obrazu:

```text
mcr.microsoft.com/playwright/python:v1.62.0-noble
```

---

## Artefakty i diagnostyka

Pipeline zapisuje wyniki osobno dla każdej przeglądarki:

```text
test-results/chromium/
test-results/firefox/
test-results/webkit/
```

Każdy job działa na osobnym runnerze, dlatego katalogi te nie znajdują
się jednocześnie na jednej maszynie GitHub Actions.

### Generowane materiały

| Materiał | Kiedy powstaje |
|---|---|
| `junit.xml` | przy każdym uruchomieniu testu w pipeline |
| `trace.zip` | po niepowodzeniu testu |
| screenshot | po niepowodzeniu testu |

Raport JUnit zawiera między innymi:

- nazwę testu;
- liczbę wykonanych testów;
- liczbę błędów i niepowodzeń;
- czas wykonania;
- komunikat przyczyny niepowodzenia.

Trace i screenshot są zachowywane dzięki parametrom:

```text
--tracing=retain-on-failure
--screenshot=only-on-failure
```

Każdy job publikuje osobny artefakt:

```text
playwright-results-chromium
playwright-results-firefox
playwright-results-webkit
```

Aby pobrać artefakt:

1. otwórz repozytorium na GitHubie;
2. przejdź do zakładki **Actions**;
3. otwórz wykonanie workflow **Playwright E2E**;
4. przejdź do sekcji **Artifacts**;
5. pobierz wynik odpowiedniej przeglądarki.

Artefakty są przypisane do konkretnego wykonania workflow. Nie są
automatycznie dodawane do plików repozytorium.
---

## Realizacja wymagań niefunkcjonalnych

| Wymaganie | Sposób realizacji |
|---|---|
| Powtarzalny rezultat testu | izolowany kontekst, czyszczenie cookies, ustalone parametry środowiska, automatyczne oczekiwanie i przypięte zależności |
| Python i Playwright | test zaimplementowany w Pythonie z użyciem `pytest-playwright` |
| Publikacja na GitHub | kod, historia zmian i wyniki CI są dostępne w repozytorium |
| Dokumentacja uruchomienia | README zawiera instrukcje dla Linuxa i Windows |
| Test w kilku przeglądarkach | Chromium, Firefox i WebKit |
| Jednoczesne wykonanie | lokalnie `pytest-xdist`, w CI macierz GitHub Actions |
| Diagnostyka błędów | JUnit przy każdym skonfigurowanym uruchomieniu oraz trace i screenshot po niepowodzeniu |
| Dokumentacja wyników | zrzuty ekranu przechowywane w wersjonowanym katalogu `docs/images/` |

---

