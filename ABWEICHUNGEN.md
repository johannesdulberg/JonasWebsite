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

### 3. Navigation: kein "More"-Menü auf mittleren Breiten

- **Bei Wix:** Auf dem Handy ein Menü-Symbol (drei Striche), das ist jetzt
  genauso umgesetzt. Auf Breiten dazwischen wandern Menüpunkte, die nicht in
  die Zeile passen, in ein "More"-Menü.
- **Jetzt:** Ab Tablet-Breite stehen alle Punkte nebeneinander und brechen bei
  Platzmangel in eine zweite Zeile um.
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

## Galerien

### 5. Raster: gleich hohe Zeilen statt der Wix-Collage

- **Bei Wix:** eine Collage, in der Bilder in unterschiedlich großen Gruppen
  ineinandergeschachtelt sind (Commercial, Outdoor).
- **Jetzt:** Zeilen aus ganzen, unbeschnittenen Bildern. Alle Bilder einer
  Zeile sind gleich hoch, jede Zeile füllt die Breite, die Reihenfolge läuft
  von links nach rechts.
- **Warum:** Die Collage berechnet Wix für jede Bildschirmbreite mit eigenem
  Programmcode neu. Das Zeilenraster kommt ohne JavaScript aus, zeigt jedes
  Bild vollständig, hält die Reihenfolge lesbar und passt sich jeder Breite an.
- **Rückbau:** groß (eigener Layout-Algorithmus).
- **Status:** offen

### 6. Großansicht ohne Dateinamen als Bildunterschrift

- **Bei Wix:** Unter dem großen Bild steht der Dateiname, z. B. "DSC01890.jpg".
- **Jetzt:** Dort steht die Beschreibung des Bildes aus dem Admin. Sie ist bei
  allen importierten Bildern leer, es erscheint also nichts.
- **Warum:** Der Dateiname ist vermutlich ungewollt stehen geblieben. So kann
  pro Bild eine echte Unterschrift gepflegt werden.
- **Rückbau:** klein (Dateinamen beim Import als Beschreibung eintragen).
- **Status:** offen

## Offene Punkte (noch keine Abweichung)

Hier habe ich ohne Vorlage gebaut, weil mir von diesen Seiten kein Bild
vorliegt. Das wird angepasst, sobald Screenshots da sind.

- **Other:** Aufteilung in Abschnitte und Zuordnung der Bilder folgt dem
  Quelltext der Wix-Seite, nicht dem sichtbaren Aufbau.
- **Booking:** Anordnung von Text, Bildreihe, Kontakt und Formular. Die
  Formularfelder (Name, E-Mail, Nachricht) sind angenommen.
- **About:** Bild links, Text rechts.
- **Outdoor:** als Raster wie Commercial.

