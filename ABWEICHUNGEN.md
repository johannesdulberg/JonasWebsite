# Abweichungen von der Wix-Seite

Hier steht jede Stelle, an der der Nachbau bewusst von der bisherigen Seite
abweicht. Die Liste ist zum gemeinsamen Durchgehen gedacht: Jeder Punkt lässt
sich einzeln zurücknehmen.

Status: **offen** = noch nicht besprochen, **bestätigt** = bleibt so,
**zurückgenommen** = wieder wie bei Wix.

## Kopf- und Fußzeile

### 1. Social-Media-Links als Text statt als Icons

- **Status:** zurückgenommen am 09.10.2026. Die Fußzeile zeigt wieder Icons wie
  bei Wix. Im Admin wählt man pro Link eine Plattform; ein Link ohne Plattform
  erscheint als Text (z. B. LinkedIn, wofür die Icon-Sammlung kein Icon hat).

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

### 4. Schriften: frei lizenzierte Entsprechungen, vom eigenen Server

- **Bei Wix:** ein fetter, geometrischer Schriftzug und eine leichte Schrift im
  Stil von Avenir für Untertitel und Menü, ausgeliefert von Wix-Servern.
- **Jetzt:** Montserrat (Schriftzug) und Nunito Sans (alles andere), als
  Dateien im Projekt. Geräte, die Avenir selbst mitbringen (Mac, iPhone),
  sehen trotzdem Nunito Sans, damit die Seite überall gleich aussieht.
- **Warum:** Avenir ist eine kostenpflichtige Schrift, die Lizenz steckt im
  Wix-Abo und gilt nicht für einen eigenen Server. Beide Ersatzschriften sind
  frei (OFL) und kommen dem Original nahe. Vom eigenen Server geladen, geht
  keine Besucher-IP an Dritte (DSGVO).
- **Rückbau:** klein, wenn eine Lizenz für die Originalschriften gekauft wird:
  Dateien austauschen, zwei Zeilen in `config/static_src/tailwind.css`.
- **Status:** offen
