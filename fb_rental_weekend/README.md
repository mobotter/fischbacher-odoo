# Fischbacher – Mietdauer und Mietpreise ohne Wochenende

Autor: Moritz Kern  
Firma: Fischbacher GmbH + Co. KG  
Version: 19.0.1.1.0; Odoo 19, Abhängigkeit sale_renting.

## Verhalten
Checkbox „Wochenende berechnen“, Standard aus. Aktiv = native Preisberechnung.
Inaktiv = Wochenendstunden ausgeschlossen. Firmenkontakt-Zeitzone, sonst Europe/Berlin.
duration_days und remaining_hours werden angepasst; Reststunden aufgerundet wie im Standard.
Nur für die Tarifermittlung wird end_date = start_date + berechenbare Sekunden übergeben.
Tatsächliche Reservierungs-/Rückgabedaten und Beschreibungen bleiben unverändert.
Ein reines Wochenende kostet 0. Native Tarifauswahl, Mengen und Währungen bleiben erhalten.

## Preisaktualisierung
Checkbox-/Datumsänderungen aktualisieren Mietpositionen in draft/sent via onchange und write,
über die native _recompute_rental_prices-Methode. Neue Mietpositionen nutzen den Preis-Hook.
Normale Verkaufspositionen sind vom expliziten Refresh durch den nativen Filter ausgeschlossen.
Der Button „Mietpreise aktualisieren“ verwendet ebenfalls die neue Berechnung.
Bestehende Angebote werden beim Upgrade NICHT massenhaft neu bepreist.
ACHTUNG: Native Preisaktualisierung kann manuelle Mietpreise/Rabatte überschreiben.

## Installation/Update
Vorher Testdatenbank und Backup verwenden. Alten Ordner fb_rental_weekend vollständig
ersetzen, Odoo neu starten und das installierte Modul aktualisieren.
CLI: odoo-bin -d DATENBANK -u fb_rental_weekend --stop-after-init
Bei bestehenden Angeboten danach einmal „Mietpreise aktualisieren“ betätigen.

## Grenzen
Keine Feiertags-, Verspätungsgebühren- oder mk_*-Änderungen. Dauerbasierte Standardtarife.
Datumsabhängige Saison-/Drittanbietertarife separat prüfen (synthetisches Preisende).
Produktkatalog-Vorschau kann Standardpreise zeigen; die Mietposition nutzt den neuen Hook.
Keine pauschale Neuberechnung bestätigter Aufträge durch den write/onchange-Refresh.
Andere native Aktionen können wie bisher Preise neu berechnen.

## Tests
01.10.2026 08:00 UTC bis 06.10.2026 08:00 UTC: aus 3 Tage, an 5 Tage.
Tagespreis 100 EUR, Menge 1, ohne günstigere Mehrtagestarife: aus 300, an 500 EUR netto.
Samstag 00 Uhr bis Montag 00 Uhr lokal: aus 0 EUR.
Freitag 12 Uhr bis Montag 12 Uhr lokal: 24 berechenbare Stunden.
Normale Verkaufs-/Transportpositionen, Menge >1, Wochenpreise und Auftragssummen prüfen.
Syntax, XML und drei isolierte Zeitberechnungen geprüft. Keine laufende Odoo-Installation
oder Integrationstests. Implementiert anhand des vom Benutzer gelieferten Quellcodes.
