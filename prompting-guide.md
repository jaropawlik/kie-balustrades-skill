# Prompting Guide - Balustrady (Nano Banana 2)

Zasady budowania promptow dla generacji balustrad balkonowych przez Google Nano Banana 2 (Gemini 3 Flash Image), na podstawie:

- Oficjalnych docs Google: https://ai.google.dev/gemini-api/docs/image-generation
- Google Cloud Blog "Ultimate prompting guide for Nano Banana": https://cloud.google.com/blog/products/ai-machine-learning/ultimate-prompting-guide-for-nano-banana
- Skill agentspace-so/nano-banana-edit (best practices dla edycji): https://skills.sh/agentspace-so/runcomfy-agent-skills/nano-banana-edit
- Kie.ai API docs: https://docs.kie.ai/market/google/nanobanana2

---

## Kluczowa roznica vs Stable Diffusion

Nano Banana 2 to **NIE jest Stable Diffusion**. To model oparty na architekturze Gemini (LLM + diffusion). To zmienia zasady promptowania:

| Technika SD | Nano Banana 2 |
|-------------|---------------|
| Wagi `(element:1.4)` | **NIE DZIALA** - ignorowane |
| Negative prompt jako parametr | **BRAK** w API |
| Tag list ("photo, woman, red dress, sharp focus") | **GORSZE** niz naturalne zdania |
| `seed` dla powtarzalnosci | **DZIALA** (parametr Kie.ai) |

**Co dziala zamiast tego:**
- Naturalne zdania w paragrafach (jak do czlowieka)
- Markdown sekcje dla zlozonych instrukcji (PRESERVE / CHANGE / SPECS / DO NOT)
- CAPS LOCK + "MUST" dla krytycznych wymogow
- Powtorzenie liczby slownie + cyfrowo
- "Do not X" w tekscie promptu (nie jako osobny parametr)

---

## Zasada #1: PRESERVE-FIRST (najwazniejsza dla edit)

Z oficjalnego skilla nano-banana-edit (skills.sh):

> "Lead with what to preserve, then state changes."

ZLE (kolejnosc moja stara):
```
Replace the railing with X. ... Keep the building exactly as in original.
```

DOBRZE (zgodnie z docs):
```
PRESERVE: Keep the entire building exactly as in reference - facade,
windows, lighting, perspective.

CHANGE: Replace only the balcony railing with X.
```

**Dlaczego dziala:** Model najpierw "zalocowuje" co ma zostac niezmienione, potem dopiero rozumie co zmienic. Odwrotna kolejnosc powoduje "drift" - model zmienia rzeczy ktorych nie powinien.

---

## Zasada #2: Markdown sekcje dla zlozonych promptow

Z oficjalnego skilla nano-banana-edit:

> "Avoid compound multi-step instructions in single prompts."

Zamiast jednego dlugiego zdania - rozbij na sekcje:

```
PRESERVE FROM REFERENCE IMAGE:
[co zachowac]

CHANGE - REPLACE ONLY THE BALCONY RAILING:
[co zmienic, ogolnie]

NEW RAILING SPECIFICATIONS:
- post count
- rail count
- color/material
- style

COUNT VERIFICATION:
[powtorzenie liczb dla pewnosci]

DO NOT:
- [czego nie robic]
```

Kazdy element pelni inna funkcje, model je traktuje jako osobne wymogi.

---

## Zasada #3: Liczby - CAPS + MUST + slownie + cyfrowo

Oficjalne docs Google przyznaja:

> "The model won't always follow the exact number of objects requested."

Stack technik (od najwazniejszej):

1. **CAPS LOCK** dla emphasis: `MUST have EXACTLY 6`
2. **Slownie + cyfrowo:** `6 (six) vertical posts`
3. **Negacja przeciwna liczbie:** `not 5, not 7`
4. **Opis ukladu:** `evenly spaced from left to right`
5. **Sekcja COUNT VERIFICATION** - powtorz na koncu

Nasz prompt robi wszystkie 5:

```
The railing MUST have EXACTLY 6 (six) vertical posts, evenly spaced
from left to right.

COUNT VERIFICATION: The final image MUST contain 6 vertical posts
(not 5, not 7) and 4 horizontal rails (not 3, not 5).
```

---

## Zasada #4: Negative prompts - tylko jako tekst, w sekcji DO NOT

W API nie ma `negative_prompt`. Ale dopisanie "Do not X" w tekscie dziala (potwierdzone przez Max Woolf - https://minimaxir.com/2025/11/nano-banana-prompts/).

Format:

```
DO NOT:
- Do not alter the building walls or windows.
- Do not change lighting or shadows.
- Do not add text, watermarks, logos or signatures.
```

**Wazne:** Google rekomenduje glownie pozytywne opisy. "Do not" uzywaj tylko dla rzeczy ktore model **mialby tendencje dodawac mimo proby zachowania** (watermarks, dodatkowe elementy dekoracyjne).

---

## Zasada #5: Naturalne zdania > tag list

Z oficjalnego docs Google:

> "A narrative, descriptive paragraph will almost always produce a better, more coherent image than a list of disconnected words."

ZLE (tag list jak w SD):
```
balcony, 6 posts, 4 rails, anthracite steel, modern, sharp focus,
high quality, 8k, masterpiece
```

DOBRZE (naturalne zdania):
```
The balcony has a modern steel railing with exactly 6 vertical posts
and 4 horizontal cross-rails, finished in matte anthracite. The posts
are evenly spaced and connected to the rails with clean welded joints.
```

---

## Pelny template promptu (zaszyte w skripcie)

### Tryb `edit` (1 zdjecie referencyjne)

```
PRESERVE FROM REFERENCE IMAGE:
Keep the entire building EXACTLY as shown in the reference - facade,
walls, windows, window frames, balcony slab, roof, surrounding
environment, lighting conditions, time of day, perspective and
camera angle. Do not modify any architectural elements other than
the railing.

CHANGE - REPLACE ONLY THE BALCONY RAILING:
Remove the existing balcony railing and replace it with a new modern
steel railing.

NEW RAILING SPECIFICATIONS:
- The railing MUST have EXACTLY [N] ([N_word]) vertical posts, evenly
  spaced from left to right.
- The railing MUST have EXACTLY [M] ([M_word]) horizontal cross-rails,
  parallel to each other, equal spacing between them.
- Color and material: [COLOR_DESC].
- Style: modern minimalist, slim rectangular profile, complete and
  unbroken structure, every post connected to every horizontal rail.
- Mounting: posts visibly mounted to the balcony floor or balcony
  front edge with clean metal connections.

COUNT VERIFICATION: The final image MUST contain [N] vertical posts
(not [N-1], not [N+1]) and [M] horizontal rails (not [M-1], not [M+1]).

DO NOT:
- Do not alter the building walls, windows, facade or any
  architectural details.
- Do not change lighting, shadows, time of day or weather.
- Do not add any decorative elements not specified above.
- Do not add text, watermarks, logos or signatures.
```

### Tryb `compose` (2+ zdjec)

Identyczna struktura, ale rozszerzona o:
- "REFERENCE IMAGES" - wyjasnienie ktore zdjecie jest glowne, ktore sa stylem
- "Match the lighting/perspective of the first (main) image"

---

## Mapa kolorow

| Nazwa | Opis dla AI |
|-------|-------------|
| `antracyt` | anthracite powder-coated steel, matte finish (RAL 7016) |
| `czarny` | jet black painted steel, satin finish |
| `bialy` | pure white powder-coated steel, matte finish (RAL 9016) |
| `srebrny` | brushed stainless steel, satin metallic finish |
| `rdzawy` | corten steel with weathered rust patina, warm orange-brown |
| `#XXXXXX` | custom color #XXXXXX painted steel, matte finish |

---

## Parametr `--seed` - powtarzalnosc

Kie.ai API wspiera `seed` (potwierdzone w docs.kie.ai). Skrypt obsluguje przez `--seed 42`.

**Kiedy uzywac:**
- Iteracja - chcesz zachowac kompozycje, zmienic tylko detal (np. kolor)
- A/B porownania - ten sam seed, dwa rozne prompty
- Replikacja udanego wyniku

**Kiedy NIE uzywac:**
- Generowanie wielu wariantow (chcesz roznorodnosci) - zostaw `--seed` puste, kazdy bedzie inny

**Przyklad iteracji:**
```bash
# Pierwszy strzal - sprobuj losowy seed
python3 scripts/kie_balustrade.py edit --posts 6 --rails 4 \
  --image input.jpg --output v1.jpg

# Wynik OK ale chce zmienic kolor - reuzywam tego samego seed-a
# (z logu task_id z Kie.ai mozesz odczytac uzyty seed)
python3 scripts/kie_balustrade.py edit --posts 6 --rails 4 \
  --color czarny --seed 12345 \
  --image input.jpg --output v2_czarny.jpg
```

---

## Parametr `--extra` - dodatkowe instrukcje

Dodawane do promptu jako sekcja `ADDITIONAL NOTES`. Format:

```
ADDITIONAL NOTES:
[twoj tekst]
```

Przyklady:
- `--extra "Posts are square 40x40mm cross-section"` - geometria
- `--extra "Cross-rails are round tubes diameter 25mm"` - profil
- `--extra "Railing height approximately 110cm"` - wysokosc

Patrz [balustrade-recipes.md](balustrade-recipes.md) dla biblioteki gotowych instrukcji.

---

## Co NIE dziala (i dlaczego)

| Technika | Dlaczego nie | Co zamiast |
|----------|--------------|------------|
| `(through-bolt:1.4)` | Skladnia SD, Nano Banana ignoruje | CAPS + "with prominent visible bolt heads" |
| `negative_prompt` parametr | Brak w API Kie.ai | Sekcja `DO NOT:` w tekscie |
| Tag list `quality, 8k, masterpiece` | Google rekomenduje narracje | Naturalne zdanie |
| `[posts:1.5]` (alternative weights) | SD only | Powtorzenie + CAPS |
| Long compound sentences | Powoduja drift | Markdown sekcje |

---

## Checklist promptu (skrypt to robi automatycznie)

- [x] Sekcja PRESERVE FIRST (co zachowac)
- [x] Sekcja CHANGE (co zmienic)
- [x] SPECIFICATIONS jako bulleted list
- [x] Liczby: CAPS + "MUST" + slownie + cyfrowo
- [x] COUNT VERIFICATION (powtorka liczb)
- [x] Sekcja DO NOT (negacje pozytywne)
- [x] Bez wag `(x:1.4)` ze Stable Diffusion
- [x] Naturalne zdania w sekcjach (nie tag-list)
