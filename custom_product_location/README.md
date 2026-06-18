# Product Location Column

Dieses Odoo-Modul erweitert Produkte um eine zusätzliche Spalte für Lagerorte in der Produktlistenansicht. Dabei werden die internen Lagerorte eines Produkts aus den vorhandenen Lagerbeständen ermittelt und als kommagetrennte Zeichenkette angezeigt.

## Funktionen

Das Modul ergänzt das Modell `product.template` um ein berechnetes Feld:

- `location_names` – zeigt alle internen Lagerorte eines Produkts an

Zusätzlich wird die Standard-Produktlistenansicht erweitert und die neue Spalte direkt nach `uom_id` eingefügt.

## Technische Details

- Modulname: `Product Location Column`
- Version: `19.0.1.0.0`
- Abhängigkeiten:
  - `product`
  - `stock`
- Lizenz: `LGPL-3`

## Funktionsweise

Für jedes Produkt werden `stock.quant`-Einträge mit Bestand größer als 0 und mit Lagerorten vom Typ `internal` gesucht. Aus diesen Datensätzen werden die vollständigen Lagerortnamen gelesen, Dubletten entfernt und anschließend als Text im Feld `location_names` zusammengeführt.

## Installation

1. Modul in das Odoo-Addons-Verzeichnis kopieren.
2. Apps-Liste aktualisieren.
3. Nach **Product Location Column** suchen.
4. Modul installieren.

## Verzeichnisstruktur

```text
product_location_column/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   └── product_template.py
└── views/
    └── product_template_views.xml
```

## Einsatzbereich

Das Modul ist hilfreich, wenn in der Produktübersicht direkt sichtbar sein soll, in welchen internen Lagerorten ein Artikel verfügbar ist. Das eignet sich besonders für Lager, Verkauf und Disposition.

## Hinweise

Das Feld ist nicht gespeichert (`store=False`) und wird zur Laufzeit berechnet. Bei großen Datenmengen kann das in Listenansichten zu Performance-Einbußen führen.
