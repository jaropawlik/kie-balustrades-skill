---
name: kie-balustrades
description: Generuje wizualizacje balustrad balkonowych przez Kie.ai (Nano Banana 2) na bazie zdjec referencyjnych. Parametryzuje liczbe slupkow, liczbe rurek poprzecznych i kolor. Obsluguje pojedyncze zdjecie (edit), wiele zdjec referencyjnych (compose) i batch (wszystkie warianty na raz). Zdjecia uploadowane przez wlasne S3/MinIO uzytkownika.
allowed-tools: ["Bash", "Read", "Write", "Glob"]
---

# Kie Balustrades Skill

Skill do generowania wizualizacji balustrad balkonowych z **wlasnych zdjec referencyjnych** (budynek/elewacja) - dedykowany pod Allegro/aukcje/oferty produktowe.

## Kiedy uzywac

Uzytkownik prosi o wygenerowanie wizualizacji balustrady na bazie wlasnego zdjecia. Triggery: "balustrada", "balkon", "wstaw balustrade do tego zdjecia", "wygeneruj warianty balustrad", "slupki + rurki poprzeczne".

## Co skill robi

Bierze **zdjecie referencyjne uzytkownika** (budynek/elewacja z balkonem) i wstawia/zamienia balustrade na nowa wg parametrow:
- **N slupkow** (typowo 3-10)
- **M rurek poprzecznych** (typowo 2-6)
- **Kolor** (antracyt, czarny, bialy, srebrny, rdzawy lub custom hex)

Tryby:
- **edit** - 1 zdjecie referencyjne (np. budynek z istniejaca balustrada do podmiany)
- **compose** - 2+ zdjec (np. budynek + osobna referencja balustrady)
- **batch** - wiele wariantow z tego samego zdjecia (jednym poleceniem)

Skill jest zoptymalizowany pod **wysoka jakosc** i **powtarzalnosc detalu konstrukcyjnego** (uchwyty przelotowe, prawidlowe slupki, brak gubienia elementow).

## Wazne: zdjecia referencyjne

Skrypt uploaduje zdjecia do **S3/MinIO uzytkownika** (skonfigurowane w `.env`) bo Kie.ai API wymaga publicznego URL. Bez S3/MinIO skill nie zadziala.

## Workflow dla Claude

1. **Sprawdz czy uzytkownik podal zdjecia**:
   - Brak zdjec → poinformuj ze skill wymaga zdjecia referencyjnego, popros o sciezke
   - 1 zdjecie → tryb `edit`
   - 2+ zdjec → tryb `compose`

2. **Zbierz parametry**:
   - Liczba slupkow (jedna wartosc dla edit/compose, lista `5,6,7` dla batch)
   - Liczba rurek poprzecznych (jedna wartosc lub lista)
   - Kolor (domyslnie: antracyt)
   - Czy batch? (kiedy uzytkownik mowi "wszystkie warianty", "kazda kombinacja")
   - Format/proporcje (domyslnie: `auto` - dopasowane do zdjecia)
   - Rozdzielczosc (domyslnie: 2K)

3. **Skrypt sam zbuduje prompt** wg zasad z [prompting-guide.md](prompting-guide.md):
   - SUBJECT FIRST - balustrada jako pierwszy element
   - Liczby slownie + cyfrowo ("six (6) vertical posts")
   - Wzmocnienia `(through-bolt connections:1.4)`
   - Pozytywne negatywy ("every post fully visible")
   - Instrukcja aby zachowac scene oryginalnego zdjecia

4. **Wywolaj skrypt**:

   **Edit (1 zdjecie):**
   ```bash
   python3 {SKILL_DIR}/scripts/kie_balustrade.py edit \
     --posts 6 --rails 4 --color antracyt \
     --image input.jpg \
     --output output/balustrada-6x4.jpg \
     --resolution 2K
   ```

   **Compose (2+ zdjec):**
   ```bash
   python3 {SKILL_DIR}/scripts/kie_balustrade.py compose \
     --posts 6 --rails 4 --color antracyt \
     --image building.jpg --image railing-ref.jpg \
     --output output/balustrada-6x4.jpg
   ```

   **Batch (jedno zdjecie, wiele wariantow):**
   ```bash
   python3 {SKILL_DIR}/scripts/kie_balustrade.py batch \
     --posts 5,6,7 --rails 3,4,5 --color antracyt \
     --image input.jpg \
     --output-dir output/ \
     --resolution 2K
   ```

   **Batch z compose (kilka zdjec ref + wiele wariantow):**
   ```bash
   python3 {SKILL_DIR}/scripts/kie_balustrade.py batch \
     --posts 5,6,7 --rails 3,4,5 \
     --image building.jpg --image railing-ref.jpg \
     --output-dir output/
   ```

5. **Pokaz wyniki** - liczba sukcesow/niepowodzen + scieżki do plikow

## Parametry CLI

| Parametr | Opcje | Domyslnie |
|----------|-------|-----------|
| `--posts` | int (single) lub lista `5,6,7` (batch) | wymagany |
| `--rails` | int (single) lub lista `3,4,5` (batch) | wymagany |
| `--color` | antracyt, czarny, bialy, srebrny, rdzawy, #XXXXXX | antracyt |
| `--image` | sciezka pliku (uzyj wielokrotnie dla compose) | wymagany |
| `--extra` | dodatkowe instrukcje dla AI | - |
| `--ratio` | 1:1, 4:3, 16:9, 9:16, 3:2, 2:3, auto | auto |
| `--resolution` | 1K, 2K, 4K | 2K |
| `--format` | jpg, png | jpg |

## Jak rozumiec uzytkownika

**Przyklad 1:** "Tu masz zdjecie willi, wstaw balustrade na 6 slupkow z 4 rurkami"
→ `edit` z 1 zdjeciem, `--posts 6 --rails 4`

**Przyklad 2:** "Mam zdjecie domu i osobno zdjecie balustrady jaka chce, polacz to"
→ `compose` z 2 zdjeciami

**Przyklad 3:** "Z tego zdjecia daj mi wszystkie kombinacje 5/6/7 slupkow i 3/4/5 rurek"
→ `batch` z 1 zdjeciem (9 wariantow)

**Przyklad 4:** "Z tego budynku zrob 9 wariantow w czarnym i 9 w antracycie"
→ 2x `batch` (po jednym na kolor) - poinformuj ze batch nie obsluguje wielu kolorow naraz

## Konfiguracja `.env`

Skrypt szuka `.env` w katalogu skilla. Wymagane zmienne:

```
KIE_API_KEY=...
S3_ENDPOINT_URL=...
S3_ACCESS_KEY=...
S3_SECRET_KEY=...
S3_BUCKET=...
S3_REGION=us-east-1
S3_PUBLIC_URL=...    # opcjonalne, jesli inny niz endpoint
```

Jesli `.env` nie istnieje albo brakuje zmiennych - poinformuj uzytkownika i wskaz [README.md](README.md).

## Obsluga bledow

| Kod | Znaczenie | Akcja |
|-----|-----------|-------|
| 401 | Zly KIE_API_KEY | Sprawdz `.env` |
| 402 | Brak srodkow na Kie.ai | Doladuj na kie.ai |
| 422 | Blad walidacji parametrow | Sprawdz proporcje/rozdzielczosc |
| 429 | Rate limit | Poczekaj 30s |
| Brak konfiguracji S3 | Brak credentials w `.env` | Uzupelnij `.env` wg `.env.example` |

## Referencje

- Zasady promptow: [prompting-guide.md](prompting-guide.md)
- Style sceny (notatki): [balustrade-recipes.md](balustrade-recipes.md)
- Instalacja i konfiguracja: [README.md](README.md)
