# Abweichungen von der Wix-Seite

Hier steht jede Stelle, an der der Nachbau bewusst von der bisherigen Seite
abweicht. Die Liste ist zum gemeinsamen Durchgehen gedacht: Jeder Punkt lässt
sich einzeln zurücknehmen.

Status: **offen** = noch nicht besprochen, **bestätigt** = bleibt so,
**zurückgenommen** = wieder wie bei Wix.

## Kopf- und Fußzeile

### 1. Social-Media-Links als Text statt als Icons

- **Bei Wix:** kleine Icons für Instagram und TikTok.
- **Jetzt:** die Namen als Textlinks ("Instagram", "TikTok").
- **Warum:** Im Admin lässt sich so jede Plattform eintragen, ohne dass für
  jede ein Icon im Code hinterlegt sein muss. Text ist außerdem für
  Screenreader eindeutig und passt zur reduzierten Typografie.
- **Rückbau:** klein. Icons als SVG hinterlegen und pro Link auswählbar machen.
- **Status:** wird zurückgenommen (Entscheidung vom 08.10.2026: Icons), Umsetzung steht in TODO.md

### 2. Jahr im Copyright aktualisiert sich selbst

- **Bei Wix:** fest "© 2025".
- **Jetzt:** immer das laufende Jahr.
- **Warum:** Eine veraltete Jahreszahl lässt eine Seite ungepflegt wirken, und
  niemand muss im Januar daran denken.
- **Rückbau:** sehr klein (festes Jahr als Feld in den Einstellungen).
- **Status:** offen

### 3. Navigation: Menü-Knopf auf dem Handy, kein "More"

- **Bei Wix:** Menüpunkte, die nicht in die Zeile passen, wandern in ein
  "More"-Menü.
- **Jetzt:** Ab Tablet-Breite stehen alle Punkte nebeneinander. Auf dem Handy
  gibt es einen Knopf "Menü", der die Liste aufklappt.
- **Warum:** Ein "More"-Menü versteckt je nach Bildschirmbreite andere Seiten.
  So ist auf jedem Gerät vorhersehbar, was sichtbar ist.
- **Rückbau:** mittel.
- **Status:** offen

## Offene Punkte (noch keine Abweichung)

- **Farben und Schrift** sind vorläufig (weißer Hintergrund, fast schwarzer
  Text, Systemschrift), weil mir das Aussehen der Wix-Seite noch nicht
  vorliegt. Die Werte stehen gesammelt in `config/static_src/tailwind.css`
  und werden anhand der Screenshots angepasst.
