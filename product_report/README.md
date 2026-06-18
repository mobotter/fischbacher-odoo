# Product Report

## Übersicht

Dieses Modul erzeugt Barcode-Etiketten für Produkte in Odoo. Es bietet zwei Report-Varianten:

- **PDF-Etikett** (QWeb-PDF) für normalen Druck oder Anzeige
- **ZPL-Etikett** (QWeb-Text) für Zebra-Barcode-Drucker

## Funktionsumfang

### PDF Barcode Report

- Generiert ein Etikett mit:
  - `default_code` (Produktcode) in großer, fetter Schrift
  - `name` (Produktname) darunter in leichter Schrift
  - Barcode als Grafik im Widget `barcode` (Code128)
  - Human-readable Barcode-Nummer unter dem Barcode
- Papierformat: 80 mm × 30 mm (Portrait)
- Margin: 2 mm oben/unten/links/rechts
- Wird als `report_type: qweb-pdf` ausgegeben

### ZPL Barcode Report

- Generiert ZPL-Kommandos für Zebra-Drucker
- Enthaltene Elemente:
  - `default_code` oben in großer Schrift (CFB, 30,15)
  - `name` in maximal 2 Linien, jeweils bis 23 Zeichen breit
  - Barcode (Code128) mit ^BC
  - Human-readable Barcode-Nummer unter dem Barcode
- Wird als `report_type: qweb-text` ausgegeben

### Produktmodell

- `product.product` wird um eine Hilfsmethode `split_by_limit` erweitert:
  - Zerlegt langen Text in Wörterblöcke
  - Maximale Länge per Limit
  - Begrenzt auf maximal 2 Linien

## Technische Details

| Feld | Wert |
|---|---|
| Technischer Name | `product_report` |
| Name | `Product Report` |
| Version | `19.0.1.0.0` |
| Author | `Ali Khan | Odolution` |
| Website | `https://odolution.com` |
| Lizenz | `LGPL-3` |
| Abhängigkeiten | `base, stock, web, product` |
| Anwendung | `True` (application) |
| Sequence | `1` |

## Enthaltene Reports

### report/action_product_barcode_report.xml

- **paperformat_product_barcode**: Papierformat für Barcode-Etiketten (80×30 mm)
- **action_product_barcode_report**: PDF Report für `product.product`
  - `report_name`: `product_report.report_barcode_label`
  - `binding_model_id`: `product.model_product_product`
  - `binding_type`: `report`
- **action_zpl_product_barcode_report**: ZPL Report für `product.product`
  - `report_type`: `qweb-text`
  - `report_name`: `product_report.report_barcode_label_zpl`

### report/report_product_barcode.xml

- **report_barcode_label**: Template für PDF-Etikett
  - Zeigt `default_code`, `name`, Barcode und Barcode-Nummer

### report/zpl_product_barcode_report.xml

- **report_barcode_label_zpl**: Template für ZPL-Etikett
  - ZPL-Kommandos für Zebra-Drucker
  - `default_code` oben, `name` in 2 Linien, Barcode, human-readable Nummer

## Helper-Funktion

### `product.product.split_by_limit(text, limit)`

- Zerlegt langen Text in Wörterblöcke
- Maximale Länge per `limit`
- Begrenzt auf maximal 2 Linien
- Wird im ZPL-Report für `name` verwendet

## Installation

1. Modul in den Addons-Pfad von Odoo legen.
2. App-Liste aktualisieren.
3. Modul installieren oder bei Änderungen upgraden.

## Hinweise

- Das PDF-Report nutzt das Odoo-Barcodelayout im Widget `barcode`.
- Das ZPL-Report erzeugt direkte Zebra-Kommandos und ist für Zebra-Drucker optimiert.
- Die `split_by_limit`-Funktion sorgt dafür, dass lange Produktnamen in maximal 2 Linien mit begrenzter Breite dargestellt werden.
- Das Modul ist als `application: True` markiert und hat `sequence: 1`.
