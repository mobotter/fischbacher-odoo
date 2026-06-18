# Adds Custom Fields to Products

## Übersicht

Dieses Modul erweitert Odoo-Produkte und Produktkategorien um zahlreiche projektspezifische Felder. Es unterstützt insbesondere:

- **Suche und Identifikation**: Suchbegriffe, Kurznamen, Herstellernummer
- **Vermietung**: Prüfdaten für TÜV, UVV und Bremsen
- **Webshop**: Webshop-Link, externe IDs, nicht-variantierende Attribute
- **Lieferanten**: Hauptlieferant und Lieferanten-Produktnummer
- **Kategorien**: Kategorie-Nummer für vollständige Namensbildung

## Technische Details

| Feld | Wert |
|---|---|
| Technischer Name | `product_custom_fields` |
| Name | `Adds Custom Fields to Products` |
| Author | `Odolution` |
| Lizenz | `LGPL-3` |
| Abhängigkeiten | `sale, website_sale` |

## Erweiterte Modelle

### `product.product`

Erweitert das Produktmodell um folgende Felder:

**Suche und Identifikation:**
- `search_term` (Char): Suchbegriff für erweiterte Produktsuche
- `short_term` (Char): Kurzname des Produkt
- `manufacturer_number` (Char): Herstellernummer
- `dsp3_id` (Char): DSP3-ID

**Vermietung:**
- `is_rental_available` (Boolean): Ist für Vermietung verfügbar
- `inspection_date` (Date): Prüfdatum (TÜV)
- `uvv_date` (Date): UVV-Prüfdatum
- `brake_inspection_date` (Date): Bremsen-Prüfdatum

**Lieferanten:**
- `main_supplier_id` (Many2one): Hauptlieferant (berechnet aus `seller_ids`)
- `main_supplier_product_number` (Char): Lieferanten-Produktnummer

**Webshop und externe IDs:**
- `webshop_link` (Char): Webshop-Link (mit URL-Widget)
- `external_id` (Integer): Externe ID
- `brand_id` (Many2one): Marke (product.brand)

**Dimensionen:**
- `length` (Char): Länge
- `width` (Char): Breite
- `height` (Char): Höhe

**One2many/Many2many:**
- `product_website_product_attribute_ids` (One2many): Website-Attributwerte für Produkt
- `product_website_attribute_ids` (Many2many): Website-Attribute

**Boni und Sonderverkäufe:**
- `bonus_applicable` (Boolean): Bonus anwendbar
- `special_sale_applicable` (Boolean): Sonderverkauf anwendbar

### `product.category`

Erweitert Produktkategorien um:

- `category_number` (Char): Kategorie-Nummer
- `complete_name` (Char, computed): Vollständiger Name mit Kategorie-Nummer

Die `complete_name`-Berechnung fügt die Kategorie-Nummer im Format ein:
- Mit Parent: `Parent /[{category_number}] Name`
- Ohne Parent: `[{category_number}] Name`

### `product.brand` (Neues Modell)

Eigenes Modell für Produktmarken:

- `name` (Char): Markenname
- `image` (Image): Markenbild
- `external_id` (Integer): Externe ID

### `product.website.attribute` (Neues Modell)

Modell für nicht-variantierende Website-Attribute:

- `name` (Char): Attributname
- `external_id` (Integer): Externe ID
- `sequence` (Integer): Sequenz
- `visible` (Boolean): Sichtbar
- `option_ids` (One2many): Attributoptionen

### `product.website.attribute.value` (Neues Modell)

Modell für Attributoptionen:

- `name` (Char): Optionname
- `external_id` (Integer): Externe ID
- `attribute_id` (Many2one): Attribut

### `product.website.attribute.product` (Neues Modell)

Verknüpfung von Produkten mit Website-Attributen:

- `product_id` (Many2one): Produkt
- `attribute_id` (Many2one): Attribut
- `value_ids` (Many2many): Werte

## Odoo 19 Upgrade-Hinweise

### Bekannte Probleme ⚠️

1. **Manifest ohne version**: Für Odoo 19 `version: '19.0.1.0.0'` hinzufügen (HIGH)
2. **Duplicate View IDs**: `product_website_attribute_view_tree` wird zweimal definiert (MEDIUM)
3. **Duplicate Action IDs**: `website_attribute_action` wird zweimal definiert (MEDIUM)
4. **Search View XML**: Mehrere `<field name="name">` im gleichen Record - invalid XML (HIGH)
5. **Missing Groups**: Access-Groups sind nicht definiert - brauchen ir.groups (HIGH)
6. **@api.model**: Deprecated in Odoo 19 (MEDIUM)

### Empfehlung

- Duplicate IDs korrigieren (unique IDs für jede View/Action)
- Search View mit separate Records umstrukturieren
- Groups in security definieren
- version, installable, auto_install im Manifest hinzufügen

## Installation

1. Modul in den Addons-Pfad von Odoo legen.
2. App-Liste aktualisieren.
3. Modul installieren oder bei Änderungen upgraden.

## Hinweise

- Das Modul ist primär für Vermietungs-Baumaschinen konzipiert (Prüfdaten, Vermietung-Flag)
- Website-Attribute sind "non Variant Creating" - erzeugen keine Produktvarianten
- `main_supplier_id` wird automatisch aus dem ersten Seller berechnet
- `complete_name` bei Kategorien includes Kategorie-Nummer für bessere Lesbarkeit
