# Balustrade Recipes - notatki do `--extra`

W trybie `edit`/`compose` scena bierze sie **ze zdjecia referencyjnego uzytkownika**, wiec klasyczne "recipe sceny" nie sa potrzebne.

Ten plik to **biblioteka gotowych instrukcji** do parametru `--extra` - jesli klient chce wymusic specyficzny styl/szczegol balustrady, ktorego nie da sie wyciagnac z samego zdjecia.

---

## Geometria slupkow

| Cel | `--extra` |
|-----|-----------|
| Slupki kwadratowe 40x40mm | `square posts 40x40mm cross-section, sharp 90 degree corners` |
| Slupki prostokatne 60x40mm | `rectangular posts 60x40mm, narrow side facing viewer` |
| Slupki okragle | `cylindrical round posts diameter 30mm` |
| Slim profile | `ultra slim minimalist posts, thin profile` |

---

## Geometria rurek

| Cel | `--extra` |
|-----|-----------|
| Rurki okragle | `round tubular cross-rails diameter 25mm` |
| Rurki kwadratowe | `square cross-rails 25x25mm` |
| Cienkie linki stalowe | `thin steel cable cross-rails instead of tubes, taut horizontal lines` |

---

## Detale konstrukcyjne

| Cel | `--extra` |
|-----|-----------|
| Uchwyty boczne | `side-mounted brackets attaching railing to balcony edge` |
| Uchwyty od dolu | `top-mounted posts standing on balcony floor with base plates` |
| Uchwyty przelotowe widoczne | `prominent visible through-bolt heads at every connection point` |
| Pochwyt drewniany | `wooden top handrail in oak finish on top of metal railing` |

---

## Faktura i wykonczenie

| Cel | `--extra` |
|-----|-----------|
| Matowy proszkowy | `fine matte powder-coated texture, no shine` |
| Polysk metaliczny | `polished metallic surface with reflections` |
| Szczotkowany metal | `brushed metal texture with vertical grain lines` |
| Naturalna patyna | `natural weathered patina, slight surface variation` |

---

## Wysokosc i proporcje

| Cel | `--extra` |
|-----|-----------|
| Standard 110cm | `railing height approximately 110cm above balcony floor` |
| Niska 90cm | `low railing approximately 90cm above floor, modern minimalist look` |
| Wysoka 120cm | `tall safety railing 120cm above floor` |
| Rowny rozstaw | `equal spacing between all posts, perfectly symmetric` |
| Wieksze odstepy boczne | `slightly wider gap between outer posts and wall mounting` |

---

## Style architektoniczne (gdy zdjecie nie wymusza)

| Cel | `--extra` |
|-----|-----------|
| Nowoczesny minimalizm | `ultra minimalist modern style, geometric precision` |
| Industrialny | `industrial loft style, raw metal aesthetic` |
| Klasyczny | `classic traditional style, balanced proportions` |
| Skandynawski | `Scandinavian style, clean lines, light look` |

---

## Multi-extra (laczenie kilku)

Mozesz laczyc kilka instrukcji w jednym `--extra`:

```bash
--extra "square posts 40x40mm, round cross-rails 25mm diameter, prominent through-bolt heads, height 110cm"
```

---

## Prompt fragmentation - kiedy uzywac

Jesli skrypt z parametrami nie daje ci tego co chcesz po 2-3 probach:
1. Otworz `prompting-guide.md`
2. Zbuduj prompt recznie wg formatu
3. Przekaz przez `--extra` wlasnie te detale ktore chcesz wymusic

Skrypt zawsze dorzuca strukture bazowa (subject + connections + preserve), `--extra` tylko **dopelnia**.
