# DIN 5008 - Sale Fischbacher

Dieses Odoo-Modul passt das Standard-DIN-5008-Layout in Odoo 19 an das Corporate Design der Fischbacher GmbH an. Der Fokus liegt auf Angeboten, Rechnungen und dem allgemeinen externen Berichtslayout.

## Funktionen

Das Modul erweitert und überschreibt bestehende QWeb-Reports und Layouts, um ein einheitliches Fischbacher-Branding in DIN-5008-Dokumenten sicherzustellen.

### Enthaltene Anpassungen

- Kompakte Absenderzeile im Adressfenster
- Dokumenttitel in der Hausfarbe `#0069b4`
- Angepasstes Seitenlayout mit Seitenzahlen
- Individuell gestalteter Footer mit:
  - Hausanschrift
  - Kontaktinformationen
  - Bankverbindungen
  - rechtlichen Unternehmensangaben
- Angepasstes Tabellen-Styling für Angebots- und Rechnungspositionen

## Technische Details

- Modulname: `DIN 5008 - Sale Fischbacher`
- Version: `19.0.1.0.0`
- Lizenz: `LGPL-3`
- Autor: `Odolution`
- Kategorie: `Accounting/Localizations`
- Abhängigkeit: `l10n_din5008`

## Betroffene Reports und Layouts

Das Modul erweitert unter anderem folgende QWeb-Templates:

- `l10n_din5008.external_layout_din5008`
- `l10n_din5008_sale.report_saleorder_document`
- `sale.report_saleorder_document`
- `account.report_invoice_document`

## Anpassungen im Detail

### Adressbereich

Die Absenderdaten werden im Adressfenster als kompakte einzeilige Darstellung ausgegeben. Zusätzlich wird eine horizontale Trennlinie eingebunden, um den Bereich optisch sauber abzuschließen.

### Dokumenttitel

Die Hauptüberschrift des Dokuments, etwa Rechnung oder Angebotsnummer, wird typografisch angepasst und in der blauen Fischbacher-Hausfarbe dargestellt.

### Footer

Der Footer wurde vollständig neu strukturiert und in mehrere Spalten gegliedert. Enthalten sind Anschrift, Kontakt, Bankdaten sowie rechtliche Unternehmensinformationen. Seitenzahlen werden rechtsbündig im unteren Bereich ausgegeben.

### Tabellen-Styling

Die Tabellenköpfe von Angebots- und Rechnungszeilen erhalten ein angepasstes `border-bottom`-Styling, um die Lesbarkeit und visuelle Struktur zu verbessern.

## Installation

1. Modul in das Odoo-Addons-Verzeichnis kopieren.
2. Apps-Liste aktualisieren.
3. Nach **DIN 5008 - Sale Fischbacher** suchen.
4. Modul installieren.

## Verzeichnisstruktur

```text
din5008_sale_fischbacher/
├── __manifest__.py
└── report/
    ├── external_layout_fischbacher.xml
    └── report_sale_order_document_fischbacher.xml
```

## Einsatzbereich

Das Modul eignet sich für Unternehmen, die ihre Odoo-Dokumente im DIN-5008-Format an ein bestehendes Corporate Design anpassen möchten. Es ist besonders sinnvoll, wenn Angebote und Rechnungen optisch konsistent mit bestehenden Geschäftsdokumenten ausgegeben werden sollen.

## Hinweise

Das Modul arbeitet über QWeb-Template-Inheritance und XPath-Anpassungen an bestehenden Odoo-Reports. Bei Änderungen in den zugrunde liegenden Odoo- oder `l10n_din5008`-Templates sollten die XPaths geprüft und gegebenenfalls angepasst werden.
