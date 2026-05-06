---
name: kie-balustrades
description: Generuje wizualizacje produktow z branzy slusarsko-stalowej (balustrady, porecze, klamki, ogrodzenia, bramy - cala oferta najdek.pl) przez Kie.ai (Nano Banana 2). Bierze zdjecie referencyjne + krotki opis zmiany w naturalnym jezyku i zwraca edytowane zdjecie. Obsluguje pojedyncze zdjecie (edit), wiele zdjec referencyjnych (compose) i batch (wiele wariantow). Zdjecia uploadowane przez wlasne S3/MinIO uzytkownika.
allowed-tools: ["Bash", "Read", "Write", "Glob"]
---

# Kie Balustrades Skill

Skill do generowania wizualizacji produktow z branzy slusarsko-stalowej (balustrady, porecze, klamki, ogrodzenia, bramy itd.) na bazie **wlasnych zdjec referencyjnych** klienta - dedykowany pod Allegro/aukcje/oferty produktowe.

## Filozofia

Generyczny edytor zdjec produktowych. Klient pisze **krotki, naturalny opis zmiany** (po polsku lub angielsku) - skill przekazuje to do AI. **Zero sztywnych parametrow** typu `--posts/--rails`. Im krotszy i bardziej konkretny prompt, tym lepszy wynik z Nano Banana 2.

## Kiedy uzywac

Uzytkownik chce edytowac zdjecie produktu - zmienic detal, kolor, liczbe elementow, dodac/usunac cos, zlozyc kompozycje z kilku zdjec. Triggery: "balustrada", "porecz", "klamka", "ogrodzenie", "brama", "zmien na zdjeciu", "wstaw produkt do tego zdjecia", "wygeneruj warianty", "edytuj to zdjecie".

## Co skill robi

1. Bierze zdjecie(a) referencyjne uzytkownika
2. Bierze krotki opis zmiany (sformulowany przez Claude na podstawie tego co user pisze/pokazuje)
3. Uploaduje zdjecia do S3/MinIO uzytkownika (Kie.ai wymaga publicznego URL)
4. Wywoluje Nano Banana 2 z minimalnym promptem ("{user_prompt} Keep the rest of the photo unchanged.")
5. Zapisuje wynik lokalnie

Tryby:
- **edit** - 1 zdjecie + prompt → edycja
- **compose** - 2+ zdjec (1. = scena, kolejne = referencje stylu) + prompt → kompozycja
- **batch** - wiele promptow na tym samym zdjeciu(ach) → seria wariantow

## Jak rozmawiac z uzytkownikiem (workflow Claude)

1. **Sprawdz co user dal**:
   - Brak zdjec → popros o sciezke do zdjecia referencyjnego
   - 1 zdjecie → tryb `edit`
   - 2+ zdjec → tryb `compose`
   - Mowi "warianty", "kazdy kolor", "porownanie" → tryb `batch`

2. **Zapytaj co dokladnie chce zmienic**, jezeli to nie jest jasne ze zdjecia/wiadomosci. Przyklady dobrych pytan:
   - "Co konkretnie ma byc inaczej na tym zdjeciu?"
   - "Jaki kolor / ile elementow / jaki ksztalt?"
   - "To ma byc edycja istniejacego produktu, czy doklejamy nowy?"

3. **Sformuluj krotki, konkretny prompt po angielsku** - 1-2 zdania max. Zasady:
   - Mow co zmienic, **nie** opisuj calej sceny od zera
   - Konkretne liczby gdy potrzeba: "Change 4 horizontal rails to 3 horizontal rails"
   - Konkretne kolory: "Change the handle color to matte black"
   - Bez ozdobnikow typu "modern minimalist", "high quality" itd.
   - Jezeli sa ograniczenia co zachowac: "Keep the rest of the photo unchanged" zostanie dodane automatycznie przez skrypt

   **Przyklady dobrych promptow:**
   - "Reduce the number of horizontal cross-rails on the balcony railing from 4 to 3."
   - "Change the door handle color to satin nickel."
   - "Replace the existing fence panels with vertical slat panels."
   - "Make the railing posts thicker (square 60x60mm profile instead of 40x40mm)."

   **Zle prompty (zbyt dlugie, opisuja cala scene):**
   - "PRESERVE FROM REFERENCE IMAGE: keep the entire building... CHANGE: replace the railing with a modern minimalist..."
   - "Generate a high-quality, professional product visualization of an anthracite steel balustrade with 6 evenly spaced posts..."

4. **Wywolaj skrypt**:

   **Edit (1 zdjecie):**
   ```bash
   python3 {SKILL_DIR}/scripts/kie_balustrade.py edit \
     --prompt "Reduce the number of horizontal rails from 4 to 3." \
     --image /path/to/input.jpg \
     --output /path/to/output/result.jpg
   ```

   **Compose (2+ zdjec):**
   ```bash
   python3 {SKILL_DIR}/scripts/kie_balustrade.py compose \
     --prompt "Install this railing style on the balcony in the first image." \
     --image scene.jpg --image railing-reference.jpg \
     --output /path/to/output/result.jpg
   ```

   **Batch (kilka promptow na tym samym zdjeciu):**
   ```bash
   python3 {SKILL_DIR}/scripts/kie_balustrade.py batch \
     --prompt "Change railing color to anthracite." \
     --prompt "Change railing color to white." \
     --prompt "Change railing color to corten rust." \
     --image input.jpg \
     --output-dir /path/to/output/
   ```

   **Batch z plikiem promptow (1 prompt per linia):**
   ```bash
   python3 {SKILL_DIR}/scripts/kie_balustrade.py batch \
     --prompts-file /path/to/prompts.txt \
     --image input.jpg \
     --output-dir /path/to/output/
   ```

5. **Pokaz wyniki** - sciezki do plikow + ile sie udalo / ile sie sypnelo. Jesli wynik jest slaby, zaproponuj retry z innym promptem (czesto wystarczy inne sformulowanie albo dodanie konkretnej liczby).

## Parametry CLI

| Parametr | Tryby | Opis |
|----------|-------|------|
| `--prompt` | edit/compose/batch | Krotki opis zmiany (batch: uzyj wielokrotnie) |
| `--prompts-file` | batch | Plik txt z promptami (1 linia = 1 prompt) |
| `--image` | edit/compose/batch | Sciezka do zdjecia (compose/batch: uzyj wielokrotnie) |
| `--output` | edit/compose | Sciezka pliku wynikowego |
| `--output-dir` | batch | Katalog na wyniki |
| `--ratio` | wszystkie | 1:1, 4:3, 16:9, 9:16, 3:2, 2:3, auto (domyslnie auto) |
| `--resolution` | wszystkie | 1K, 2K, 4K (domyslnie 2K) |
| `--format` | wszystkie | jpg, png (domyslnie jpg) |
| `--seed` | wszystkie | int dla powtarzalnosci, brak = losowy |

## Tipy do promptow (dla Claude)

- **Liczby pisz cyfrowo I podawaj kontekst**: "from 4 to 3" jest lepsze niz "set to 3"
- **Kolory konkretnie**: "satin black", "matte anthracite RAL 7016", "polished chrome" - nie "ciemny"
- **Material**: "stainless steel", "powder-coated aluminum", "tempered glass" - jezeli istotne
- **Pozycja**: "left railing only", "the bottom horizontal rail" - jezeli zmiana dotyczy konkretnego fragmentu
- **Negacje dzialaja srednio**: zamiast "no extra rails", pisz "exactly 3 rails total"
- **Jezeli AI gubi liczby** (czeste przy malych elementach na zdjeciu): w prompcie podaj kontekst "the railing currently has 4 rails - reduce to 3"

## Konfiguracja `.env`

Skrypt szuka `.env` najpierw w katalogu skilla, potem w `~/.claude/.env`. Wymagane zmienne:

```
KIE_API_KEY=...
S3_ENDPOINT_URL=...
S3_ACCESS_KEY=...
S3_SECRET_KEY=...
S3_BUCKET=...
S3_REGION=us-east-1
S3_PUBLIC_URL=...    # opcjonalne, jesli inny niz endpoint
```

Bucket musi mieć policy `public-read` na GetObject (Kie.ai pobiera plik z URLa) - w przeciwnym wypadku dostaniesz 403.

## Obsluga bledow

| Kod | Znaczenie | Akcja |
|-----|-----------|-------|
| 401 | Zly KIE_API_KEY | Sprawdz `.env` |
| 402 | Brak srodkow na Kie.ai | Doladuj na kie.ai |
| 403 (przy generacji) | Plik na S3 nieosiagalny publicznie | Ustaw bucket policy public-read |
| 422 | Blad walidacji parametrow | Sprawdz proporcje/rozdzielczosc |
| 429 | Rate limit | Poczekaj 30s |
| Brak konfiguracji S3 | Brak credentials w `.env` | Uzupelnij `.env` wg `.env.example` |

## Referencje

- Instalacja i konfiguracja: [README.md](README.md)
