# Prompting Guide - Balustrady (edit/compose)

Zasady budowania promptow dla generacji balustrad balkonowych z **referencyjnych zdjec uzytkownika** przez Nano Banana 2.

## Problem ktory rozwiazujemy

Modele text-to-image gubia szczegoly konstrukcyjne przy balustradach:
- Nieprawidlowa liczba slupkow (zamiast 6 generuje 5 lub 7)
- Brakujace uchwyty przelotowe (rurki "wisza" w powietrzu)
- Zmiana sceny/budynku zamiast zachowania oryginalu
- Mieszanie metalu z drewnem gdy nie chcemy

Te zasady minimalizuja te bledy. Skrypt sam buduje prompt - ten plik tlumaczy **dlaczego** prompt wyglada tak a nie inaczej.

---

## Struktura promptu (KOLEJNOSC MA ZNACZENIE)

W trybie `edit`:

```
1. ZADANIE: "Replace the existing balcony railing in the provided image with..."
2. SUBJECT: balustrada z dokladna liczba elementow (slownie + cyfrowo)
3. CONNECTIONS: uchwyty przelotowe z waga (1.4)
4. MATERIAL: kolor, faktura, wykonczenie
5. PRESERVE: "Keep the building, facade, windows, lighting EXACTLY as in original"
6. QUALITY: (sharp focus:1.3), positive negatives
```

---

## Zasada #1: Liczby zapisuj DWA RAZY

| Zle | Dobrze |
|-----|--------|
| `balcony with 6 posts` | `exactly six (6) vertical posts` |
| `4 rails` | `four (4) horizontal cross-rails` |

**Dlaczego:** Modele lepiej rozumieja liczby zapisane slownie. Cyfra w nawiasie wzmacnia.

---

## Zasada #2: PRESERVE SCENE (krytyczne dla edit)

W trybie edit najwazniejsza instrukcja:

```
"Keep the building, facade, windows, lighting and surrounding scene
EXACTLY as in the original image - only replace the railing."
```

Bez tego model "ulepsza" budynek, zmienia kolor elewacji, pora dnia ucieka.

---

## Zasada #3: Wzmocnij krytyczne elementy wagami

Skladnia Nano Banana 2: `(element:1.3)` - wzmocnienie, `(element:0.7)` - oslabienie.

**Wzmacniaj zawsze:**
- `(through-bolt connections:1.4)` - uchwyty przelotowe
- `(sharp focus:1.3)` - ostrosc na balustradzie
- `(architectural detail:1.2)` - szczegolowosc

---

## Zasada #4: Negatywy semantyczne (pozytywne)

Modele slabo reaguja na "no X". Opisuj POZYTYWNIE.

| Zle (negacja) | Dobrze (pozytyw) |
|---------------|------------------|
| `no missing posts` | `every post fully visible and connected` |
| `no broken rails` | `continuous unbroken horizontal rails` |
| `not blurry` | `sharp focus on railing details` |

---

## Format promptu (jak buduje go skrypt)

### Tryb `edit` (1 zdjecie)

```
Replace the existing balcony railing in the provided image with a new
modern balcony railing that has exactly [POSTS_WORD] ([POSTS]) vertical
posts and [RAILS_WORD] ([RAILS]) horizontal cross-rails.

Material: [COLOR_DESCRIPTION].

(through-bolt connections:1.4) clearly visible at every post-to-rail
intersection. Symmetrical post spacing, slim rectangular profile,
complete unbroken structure.

Keep the building, facade, windows, lighting and surrounding scene
EXACTLY as in the original image - only replace the railing.

(sharp focus:1.3) on railing structure, every one of the [POSTS_WORD]
posts fully visible and connected, all [RAILS_WORD] continuous unbroken
horizontal rails, perfect alignment with balcony floor.
```

### Tryb `compose` (2+ zdjec)

```
Using the first image as the main scene (building/balcony) and additional
images as style/material reference, create a photorealistic visualization
where the balcony has a new railing with exactly [POSTS_WORD] ([POSTS])
vertical posts and [RAILS_WORD] ([RAILS]) horizontal cross-rails, in
[COLOR_DESCRIPTION].

(through-bolt connections:1.4) clearly visible at every intersection.
Match the lighting, perspective and architectural style of the main scene.

(sharp focus:1.3) on railing, every one of the [POSTS_WORD] posts fully
visible, all [RAILS_WORD] continuous unbroken horizontal rails.
```

---

## Mapa kolorow (zaszyte w skrypcie)

| Nazwa | Opis dla AI |
|-------|-------------|
| `antracyt` | anthracite powder-coated steel, matte finish (RAL 7016) |
| `czarny` | jet black painted steel, satin finish |
| `bialy` | pure white powder-coated steel, matte finish (RAL 9016) |
| `srebrny` | brushed stainless steel, satin metallic finish |
| `rdzawy` | corten steel with weathered rust patina, warm orange-brown |
| `#XXXXXX` | custom color #XXXXXX painted steel, matte finish |

---

## Parametr `--extra` (dodatkowe instrukcje)

Gdy chcesz wymusic cos specyficznego, uzyj `--extra`:

**Przyklady:**
- `--extra "slupki w przekroju kwadratowym 40x40mm"` - geometria
- `--extra "metal posts with subtle vertical brushed texture"` - faktura
- `--extra "balustrade height ~110cm above balcony floor"` - wysokosc
- `--extra "wider spacing between outer posts and wall"` - rozstaw

Skrypt dolaczy to na koncu promptu jako "Additional notes: ...".

---

## Co NIE dziala dobrze (i dlaczego)

✗ **"Make sure there are exactly X posts"** - meta-instrukcje sa ignorowane
✗ **"Render in 4K, professional quality"** - od tego sa parametry `--resolution`, nie prompt
✗ **Opisywanie sceny w prompcie** - juz jest na zdjeciu referencyjnym, nie powtarzaj
✗ **Wiele kolorow w jednym `--color`** - rob wiele wywolan, jeden kolor na raz
✗ **Negatywy z "no/not/without"** - uzywaj zawsze pozytywnych form

---

## Checklist (skrypt to robi automatycznie, dla wiedzy)

Zbudowany prompt powinien miec:

- [x] Instrukcja "replace railing" / "create with new railing" (akcja)
- [x] Liczba slupkow slownie + cyfrowo
- [x] Liczba rurek slownie + cyfrowo
- [x] `(through-bolt connections:1.4)`
- [x] Kolor i material balustrady
- [x] "Keep building/scene EXACTLY as original" (tylko edit)
- [x] `(sharp focus:1.3)` na koncu
- [x] Pozytywne potwierdzenie kompletnosci ("every X visible, all Y unbroken")

Jesli budujesz prompt recznie - zachowaj te punkty.
