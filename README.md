# Kie Balustrades Skill

Skill dla Claude Code do generowania wysokiej jakosci wizualizacji balustrad balkonowych przez API Kie.ai (model Google Nano Banana 2).

**Pracuje na zdjeciach referencyjnych uzytkownika** - bierzesz zdjecie budynku/elewacji, skill wstawia/zamienia balustrade na nowa wg parametrow.

Parametryzuje:
- liczbe slupkow (np. 5, 6, 7)
- liczbe rurek poprzecznych (np. 3, 4, 5)
- kolor (antracyt, czarny, bialy, srebrny, rdzawy lub custom hex)

Tryby:
- **edit** - 1 zdjecie referencyjne (najczestsze)
- **compose** - 2+ zdjec (np. budynek + osobna referencja balustrady)
- **batch** - wiele wariantow z tego samego zdjecia jednym poleceniem (np. 9 kombinacji)

---

## Wymagania

- **Konto Kie.ai** z API key i zasilonym kontem (https://kie.ai)
- **S3 lub MinIO** - dowolny S3-compatible storage z Twoimi credentials (zdjecia musza miec publiczny URL dla Kie.ai API)
- **Python 3.9+**

---

## Instalacja

### 1. Sklonuj repo do skills Claude Code

```bash
cd ~/.claude/skills
git clone <URL_REPO> kie-balustrades
cd kie-balustrades
```

### 2. Zainstaluj zaleznosci Pythona

```bash
pip3 install -r requirements.txt
```

### 3. Zaloz konto Kie.ai i pobierz API key

1. Wejdz na https://kie.ai
2. Zaloz konto (mozna przez Google)
3. Doladuj konto - kazda generacja kosztuje punkty (orientacyjnie 0.05-0.20 USD per obrazek 2K)
4. Wejdz w **API Keys** i wygeneruj nowy klucz

### 4. Przygotuj S3/MinIO

Kie.ai API potrzebuje **publicznego URL** zdjecia referencyjnego. Skrypt uploaduje na Twoje S3/MinIO i przekazuje URL.

Wymagane:
- Endpoint S3 (np. `https://minio.twojadomena.com` albo `https://s3.eu-central-1.amazonaws.com`)
- Access key + Secret key
- Bucket z **publicznym dostepem do odczytu** (lub presigned URLs - skrypt uzywa direct URL)

> **MinIO:** ustaw bucket policy na `public read` dla prefixu `kie-balustrades/*`
> **AWS S3:** wlacz public access dla bucketa lub uzyj CloudFront przed nim

### 5. Skonfiguruj `.env`

```bash
cp .env.example .env
```

Otworz `.env` w edytorze i wypelnij:

```
KIE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
S3_ENDPOINT_URL=https://minio.twojadomena.com
S3_ACCESS_KEY=twoj_access_key
S3_SECRET_KEY=twoj_secret_key
S3_BUCKET=nazwa_bucketu
S3_REGION=us-east-1
```

Opcjonalnie `S3_PUBLIC_URL` - jesli URL publicznego dostepu jest inny niz endpoint (np. CDN przed MinIO).

### 6. Test

```bash
python3 scripts/kie_balustrade.py edit \
  --posts 6 --rails 4 \
  --image /sciezka/do/twojego/zdjecia.jpg \
  --output output/test.jpg
```

Jesli wszystko dziala - dostaniesz `output/test.jpg`.

---

## Uzycie w Claude Code

Po instalacji skill dziala automatycznie. Wystarczy napisac do Claude:

```
Tu masz zdjecie willi /path/to/willa.jpg, wstaw balustrade na 6 slupkow
z 4 rurkami poprzecznymi w antracycie
```

albo batch:

```
Z tego zdjecia /path/to/budynek.jpg potrzebuje wszystkie warianty:
5, 6, 7 slupkow i 3, 4, 5 rurek poprzecznych, antracyt
```

Claude zrozumie i odpali skrypt.

---

## Uzycie z linii komend (bez Claude)

### Edit - 1 zdjecie

```bash
python3 scripts/kie_balustrade.py edit \
  --posts 6 --rails 4 --color antracyt \
  --image input.jpg \
  --output output/balustrada-6x4.jpg \
  --ratio auto \
  --resolution 2K
```

### Compose - 2+ zdjec referencyjnych

```bash
python3 scripts/kie_balustrade.py compose \
  --posts 6 --rails 4 --color czarny \
  --image building.jpg \
  --image railing-style-ref.jpg \
  --output output/balustrada.jpg
```

### Batch - wszystkie kombinacje z jednego zdjecia

```bash
python3 scripts/kie_balustrade.py batch \
  --posts 5,6,7 --rails 3,4,5 --color antracyt \
  --image input.jpg \
  --output-dir output/ \
  --resolution 2K
```

To wygeneruje 9 plikow w `output/`:
```
balustrada_5x3_antracyt_20260506_141523.jpg
balustrada_5x4_antracyt_20260506_141523.jpg
balustrada_5x5_antracyt_20260506_141523.jpg
balustrada_6x3_antracyt_20260506_141523.jpg
balustrada_6x4_antracyt_20260506_141523.jpg
balustrada_6x5_antracyt_20260506_141523.jpg
balustrada_7x3_antracyt_20260506_141523.jpg
balustrada_7x4_antracyt_20260506_141523.jpg
balustrada_7x5_antracyt_20260506_141523.jpg
```

> **Optymalizacja:** Batch uploaduje zdjecia tylko raz (na poczatku), potem reuzytkuje URL dla wszystkich wariantow - oszczedza czas i transfer.

### Dodatkowe instrukcje (`--extra`)

```bash
python3 scripts/kie_balustrade.py edit \
  --posts 6 --rails 4 \
  --image input.jpg --output out.jpg \
  --extra "balustrada w stylu nowoczesnym, slupki w przekroju kwadratowym 40x40mm"
```

---

## Wszystkie parametry

| Parametr | Opcje | Domyslnie |
|----------|-------|-----------|
| `--posts` | int (edit/compose) lub lista `5,6,7` (batch) | wymagany |
| `--rails` | int lub lista `3,4,5` | wymagany |
| `--image` | sciezka (uzyj wielokrotnie dla compose) | wymagany |
| `--color` | `antracyt` / `czarny` / `bialy` / `srebrny` / `rdzawy` / `#XXXXXX` | `antracyt` |
| `--extra` | string z dodatkowymi instrukcjami | - |
| `--ratio` | `1:1` / `4:3` / `3:2` / `16:9` / `9:16` / `2:3` / `3:4` / `auto` | `auto` |
| `--resolution` | `1K` / `2K` / `4K` | `2K` |
| `--format` | `jpg` / `png` | `jpg` |
| `--output` (edit/compose) | sciezka pliku | wymagany |
| `--output-dir` (batch) | katalog | wymagany |

---

## Koszt orientacyjny

Cennik Kie.ai zmienia sie - sprawdz aktualny na https://kie.ai. Orientacyjnie dla Nano Banana 2:

- 1K: ~0.04 USD
- 2K: ~0.08 USD
- 4K: ~0.16 USD

Batch 9 wariantow w 2K = ~0.72 USD (~3 zl). Plus minimalny transfer S3.

---

## Troubleshooting

**`Error: Brak konfiguracji S3 w .env`**
- Sprawdz czy w `.env` sa wszystkie zmienne S3_*

**`Error: 401 Unauthorized`**
- Zly `KIE_API_KEY`. Skopiuj na nowo z https://kie.ai

**`Error: 402 Payment Required`**
- Brak srodkow. Doladuj na https://kie.ai

**`Error: 422 Validation Error`**
- Najczestszy powod: zle proporcje/rozdzielczosc albo URL zdjecia jest niedostepny publicznie. Otworz URL z logu (`URL: https://...`) w przegladarce - musi sie wyswietlic zdjecie.

**`Error: 429 Rate Limit`**
- Za duzo zapytan. Poczekaj 30s. Batch ma 5s przerwy miedzy wariantami.

**Generuje zla liczbe slupkow / rurek**
- To znany problem modeli text-to-image. Skill juz uzywa najmocniejszych technik (subject-first, slowa+cyfry, wzmacnianie wagami).
- Wygeneruj 2-3 warianty i wybierz najlepszy.
- Sprobuj z mniej skomplikowanym tlem albo `--extra "extreme detail on railing geometry"`.

**Generuje balustrade ale zmienia tlo**
- W trybie `edit` skrypt instruuje "keep building exactly as in original". Jesli mimo tego zmienia, sprobuj `--ratio auto` (dopasowanie do zdjecia) i wyzsza `--resolution 4K`.

---

## Jak to dziala (jakosc)

Skill uzywa **inzynierii promptow** zoptymalizowanej pod konstrukcje balustrad:

1. **Subject-first** - balustrada jako pierwszy element promptu
2. **Liczby slownie + cyfrowo** - `"six (6) vertical posts"` (lepsze rozpoznanie liczb)
3. **Wzmacniacze wag** - `(through-bolt connections:1.4)` na uchwytach przelotowych
4. **Pozytywne negatywy** - zamiast "no missing posts" piszemy "every post fully visible"
5. **Preserve scene** - w trybie `edit` instrukcja aby zachowac budynek/swiatlo z oryginalu

Pelne zasady: [prompting-guide.md](prompting-guide.md)

---

## Bezpieczenstwo

- `.env` jest w `.gitignore` - nigdy nie wlatuje do git
- Skrypt nie loguje credentials
- Zdjecia uploadowane do **Twojego** S3/MinIO (Kie.ai pobiera tylko URL)
- Pliki na S3 maja unikalne nazwy z timestamp+UUID

---

## Licencja

MIT
