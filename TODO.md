# TODO

## Beschlossen, noch nicht umgesetzt

- [ ] **Booking-Formular anschließen.** Das Formular (Name, E-Mail, Nachricht)
  wird angezeigt, verschickt aber nichts und sagt das beim Absenden auch.
  Offen: Nachricht speichern und per E-Mail zustellen, Spam-Schutz ohne
  Fremddienst, Einwilligungs-Hinweis zum Datenschutz, Bestätigungsmeldung.

## Vorschläge (nicht umgesetzt, brauchen eine Entscheidung)

Dinge, die mir beim Bauen aufgefallen sind. Nichts davon ist gemacht.

1. **Datenschutzerklärung und Impressum anpassen (vor dem Livegang nötig).**
   Der Text ist 1:1 von der Wix-Seite übernommen und beschreibt deren Technik:
   Wix als Baukasten und Hoster, Wix-Cookies, Google Analytics, eingebettete
   Social-Media-Elemente. Auf die neue Seite trifft das nicht zu, dafür fehlen
   der neue Hoster und die Server-Logs. Im Impressum steht außerdem noch
   "§ 5 TMG" (heute § 5 DDG).
2. **Bildbeschreibungen (Alt-Texte).** Alle importierten Bilder haben eine leere
   Beschreibung. Für Suchmaschinen und Screenreader wären kurze Beschreibungen
   sinnvoll; gepflegt werden sie im Admin am Bild.
3. **Bildunterschrift in der Großansicht.** Wix zeigt dort den Dateinamen
   (z. B. DSC01890.jpg). Hier erscheint die Beschreibung des Bildes, solange
   sie leer ist also nichts. Siehe ABWEICHUNGEN.md, Punkt 6.
4. **Sprechende Bildtitel.** Die Bilder heißen in der Bibliothek
   "Commercial 07" usw. Das erleichtert das Wiederfinden wenig.
5. **Vorschaubild für die Cinemagramme.** Bis ein Video geladen ist, ist sein
   Feld leer. Ein Standbild pro Video würde das überbrücken.
6. **Galerien der Startseite automatisch weiterlaufen lassen**, falls sie das
   bei Wix tun (konnte ich nicht sehen).
7. **Suchmaschinen und Teilen:** Beschreibungstext pro Seite, Vorschaubild für
   geteilte Links, sitemap.xml und robots.txt.
8. **Favicon** (das kleine Symbol im Browser-Tab) fehlt.
9. **Fehlerseiten** (404 "nicht gefunden", 500) haben noch das Aussehen der
   Wagtail-Vorlage.
10. **Suche** unter /search/ stammt aus der Wagtail-Vorlage, ist ungestaltet
    und nirgends verlinkt: entfernen oder gestalten.
11. **AVIF zusätzlich zu WebP** für noch kleinere Bilddateien.

## Erledigt

- [x] **Social-Media-Icons in der Fußzeile** statt der Textlinks (09.10.2026).
