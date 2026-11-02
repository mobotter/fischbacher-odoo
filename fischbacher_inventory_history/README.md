# Inventur / Abwertungen – individuelle Bestandsbewertung

Autor: Moritz Kern
Firma: Fischbacher GmbH + Co. KG
Version: 19.0.1.5.2

## Miet-/Abo-Bewertung

Abschnitt 2 berücksichtigt alle lagergeführten Produktvarianten mit
rent_ok oder recurring_invoice, einschließlich Nullbeständen und
archivierter Varianten.

Bewertungsmenge = max(Odoo-Stichtagsbestand, 1.0).

Der tatsächliche Odoo-Bestand wird nicht verändert.
Produkte mit beiden Haken werden nur einmal bewertet.

Preisquelle ist der neueste historische EK aus Lager 1 bis zum Stichtag.
Nur bei fehlender Historienzeile wird der aktuelle firmenbezogene
standard_price verwendet. Historischer EK 0,00 ist gültig.
Widersprüchliche oder unvollständige historische Preise werden als
Konflikte angezeigt und nicht stillschweigend ersetzt.

Varianten, Produktvorlagen, Überschneidungen und angehobene Mengen
werden im Bericht separat ausgewiesen.

## Unveränderte Bereiche

- Odoo-Standardbewertung und Abschlussbuchungen
- Abschnitt 1: Warenbestand mit tatsächlicher Stichtagsmenge
- Abschnitt 3: tatsächlicher Gesamtbestand zum 30.07.2026
- Abschnitt 4: importierte Dezember-2025-Bewertung für Lager 1 und ML
- Kostenpreise, Lagerbestände und Seriennummern

## Installation

Die Änderungen befinden sich direkt in valuation_report.py und
valuation_report.xml.

Frühere Imports valuation_rental_fix und valuation_scope sowie deren
XML-Asset-Einträge entfernen. Den Import valuation_report behalten.
Odoo vollständig neu starten, Modul aktualisieren und Browser-Assets
neu laden.

## Grenzen

Keine Anlagenabschreibung und keine PDF-/XLSX-Erweiterung.
Zuordnung anhand der heutigen Produkthaken.
Bestandsmengen aus dem bestehenden Bewertungskontext.
Historie weiterhin ohne Gesellschaftstrennung.
Die Mindestmenge ist eine individuelle Auswertungsregel.

Vor Produktivbetrieb in einer Testdatenbank prüfen.
