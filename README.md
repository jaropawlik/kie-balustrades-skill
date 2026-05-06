# Kie Balustrades Skill

Skill dla Claude Code do edycji zdjec produktow z branzy slusarsko-stalowej (balustrady, porecze, klamki, ogrodzenia, bramy itd.) przez API Kie.ai.

**Filozofia:** generyczny edytor - bierzesz zdjecie produktu i piszesz krotki, naturalny opis zmiany ("zmniejsz liczbe rurek z 4 do 3", "zmien kolor klamki na czarny", "wstaw te porecz na te schody"). Skill przekazuje to do AI i zwraca edytowane zdjecie.

Modele:
- `nano-banana-pro` (default) - lepsza jakosc, drozszy
- `nano-banana-2` - tansza alternatywa do iteracji

Tryby:
- **edit** - 1 zdjecie + prompt
- **compose** - 2+ zdjec (1. = scena, kolejne = referencje stylu) + prompt
- **batch** - wiele promptow na tym samym zdjeciu(ach) - dostajesz seria wariantow

---

## Wymagania

- **Konto Kie.ai** z API key i zasilonym kontem (https://kie.ai)
- **S3 lub MinIO** - dowolny S3-compatible storage (Kie.ai pobiera zdjecia z publicznego URL)
- **Python 3.9+**

---

## Instalacja

### 1. Sklonuj repo do skills Claude Code

```bash
cd ~/.claude/skills
git clone <URL_REPO> kie-balustrades
cd kie-balustrades
```

### 2. Zainstaluj zaleznosci

```bash
pip3 install -r requirements.txt
```

### 3. Konto Kie.ai

1. Wejdz na https://kie.ai, zaloz konto
2. Doladuj konto - kazda generacja kosztuje punkty
3. W **API Keys** wygeneruj klucz

### 4. S3/MinIO

Kie.ai potrzebuje **publicznego URL** zdjecia. Skrypt uploaduje na Twoje S3/MinIO i przekazuje URL do API.

Wymagane:
- Endpoint S3 (np. `https://minio.twojadomena.com` albo `https://s3.eu-central-1.amazonaws.com`)
- Access key + Secret key
- Bucket z **public-read na GetObject**

> **MinIO:** ustaw bucket policy `public-read` (przez `mc anonymous set download`, panel webowy, albo programowo przez boto3).
> **AWS S3:** wlacz public access dla bucketa lub uzyj CloudFront przed nim.

Bez public-read dostaniesz `403 Forbidden` przy generacji.

### 5. Skonfiguruj `.env`

```bash
cp .env.example .env
```

Wypelnij:

```
KIE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
S3_ENDPOINT_URL=https://minio.twojadomena.com
S3_ACCESS_KEY=twoj_access_key
S3_SECRET_KEY=twoj_secret_key
S3_BUCKET=nazwa_bucketu
S3_REGION=us-east-1
```

Opcjonalnie `S3_PUBLIC_URL` - jesli URL publicznego dostepu jest inny niz endpoint (np. CDN przed MinIO).

Skrypt szuka `.env` najpierw w katalogu skilla, potem w `~/.claude/.env` (fallback dla globalnej konfiguracji).

### 6. Test

```bash
python3 scripts/kie_balustrade.py edit \
  --prompt "Change the railing color to satin black." \
  --image /sciezka/do/zdjecia.jpg \
  --output output/test.jpg
```

---

## Uzycie w Claude Code

Po instalacji skill dziala automatycznie. Wystarczy napisac do Claude:

```
Tu masz zdjecie balkonu /path/to/balkon.jpg, zmniejsz liczbe poprzecznych rurek z 4 do 3
```

```
Mam zdjecie domu i osobno zdjecie balustrady. Wstaw te balustrade na ten balkon.
```

```
Z tego zdjecia /path/to/produkt.jpg zrob 4 warianty kolorystyczne: antracyt, czarny, bialy, rdzawy
```

Claude zrozumie kontekst, sformuluje krotki prompt po angielsku, odpali skrypt.

**Dobre prompty (krotkie, konkretne):**
- "Reduce the number of horizontal cross-rails from 4 to 3."
- "Change the door handle color to satin nickel."
- "Replace the existing fence panels with vertical slat panels."

**Zle prompty (zbyt dlugie, opisuja cala scene):**
- "Generate a high-quality, professional product visualization of an anthracite steel balustrade with 6 evenly spaced posts..."

---

## Uzycie z linii komend

### Edit - 1 zdjecie + prompt

```bash
python3 scripts/kie_balustrade.py edit \
  --prompt "Change the railing color to matte black." \
  --image input.jpg \
  --output output/result.jpg \
  --resolution 2K
```

### Compose - 2+ zdjec referencyjnych

Pierwsze zdjecie = glowna scena, kolejne = referencje stylu (np. balustrada do skopiowania).

```bash
python3 scripts/kie_balustrade.py compose \
  --prompt "Install this railing style on the balcony in the first image." \
  --image scena.jpg \
  --image railing-reference.jpg \
  --output output/result.jpg
```

### Batch - wiele promptow na jednym zdjeciu

```bash
python3 scripts/kie_balustrade.py batch \
  --prompt "Change railing color to anthracite." \
  --prompt "Change railing color to white." \
  --prompt "Change railing color to corten rust." \
  --image input.jpg \
  --output-dir output/
```

albo z pliku:

```bash
python3 scripts/kie_balustrade.py batch \
  --prompts-file prompts.txt \
  --image input.jpg \
  --output-dir output/
```

`prompts.txt` - 1 prompt per linia, linie zaczynajace od `#` ignorowane.

### Wybor modelu

```bash
python3 scripts/kie_balustrade.py edit \
  --prompt "..." \
  --image input.jpg --output out.jpg \
  --model nano-banana-2     # tanszy, do iteracji
```

Default: `nano-banana-pro` (lepsza jakosc, drozszy).

---

## Wszystkie parametry

| Parametr | Tryby | Opis |
|----------|-------|------|
| `--prompt` | edit/compose/batch | Krotki opis zmiany. W batch uzyj wielokrotnie. |
| `--prompts-file` | batch | Plik tekstowy: 1 prompt per linia |
| `--image` | edit/compose/batch | Sciezka pliku. compose/batch: uzyj wielokrotnie. |
| `--output` | edit/compose | Sciezka pliku wynikowego |
| `--output-dir` | batch | Katalog na wyniki |
| `--model` | wszystkie | `nano-banana-pro` (default) lub `nano-banana-2` |
| `--ratio` | wszystkie | `1:1` / `4:3` / `3:2` / `16:9` / `9:16` / `2:3` / `3:4` / `auto` (default) |
| `--resolution` | wszystkie | `1K` / `2K` (default) / `4K` |
| `--format` | wszystkie | `jpg` (default) / `png` |
| `--seed` | wszystkie | int dla powtarzalnosci, brak = losowy |

---

## Koszt orientacyjny

Cennik Kie.ai zmienia sie - sprawdz aktualny na https://kie.ai.

Orientacyjnie:
- Nano Banana 2 (2K): ~0.08 USD per obrazek
- Nano Banana Pro (2K): ~0.20-0.30 USD per obrazek

Pro daje zauwazalnie lepsza jakosc detalu i lepiej trzyma sie instrukcji - dla finalnych zdjec na oferty/Allegro warto. Do iteracji i szybkich testow uzyj Nano Banana 2.

---

## Troubleshooting

**`Error: Brak konfiguracji S3 w .env`**
Sprawdz czy w `.env` sa wszystkie zmienne S3_*.

**`Error: 401 Unauthorized`**
Zly `KIE_API_KEY`. Skopiuj na nowo z https://kie.ai.

**`Error: 402 Payment Required`**
Brak srodkow. Doladuj na https://kie.ai.

**`Generation failed: 403 Forbidden for url: ...`**
Plik na S3 nie jest publicznie czytelny. Ustaw bucket policy `public-read` na GetObject. Otworz URL z logu w przegladarce - musi sie wyswietlic zdjecie.

**`Error: 422 Validation Error`**
Zle proporcje albo rozdzielczosc. Sprawdz `--ratio` i `--resolution`.

**`Error: 429 Rate Limit`**
Za duzo zapytan. Poczekaj 30s.

**AI nie respektuje liczb (np. zostawia 4 rurki zamiast 3)**
Znana slabosc obu modeli przy malych elementach na zdjeciu. Sprobuj:
- Pro zamiast Nano 2 (`--model nano-banana-pro`)
- Konkretny opis ktorej rzeczy sie pozbyc: "Remove the topmost horizontal rail" zamiast "reduce from 4 to 3"
- Compose z drugim zdjeciem ktore juz ma docelowa geometrie

**Zmienia tlo zamiast tylko produkt**
Skrypt automatycznie dodaje "Keep the rest of the photo unchanged." na koncu kazdego promptu. Jak nadal psuje tlo - sprobuj `--resolution 4K` (lepsze trzymanie detalu) albo daj wieksze, jasniejsze zdjecie.

---

## Bezpieczenstwo

- `.env` jest w `.gitignore` - nigdy nie wlatuje do git
- Skrypt nie loguje credentials
- Zdjecia uploadowane do **Twojego** S3/MinIO (Kie.ai pobiera tylko URL)
- Pliki na S3 maja unikalne nazwy z timestamp+UUID

---

## Licencja

MIT
