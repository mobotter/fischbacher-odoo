# Adds Custom Fields to Products

## Übersicht

Dieses Modul erweitert Odoo-Produkte (`product.product`) und Produktkategorien (`product.category`) um zahlreiche projektspezifische Felder. Es unterstützt insbesondere:

- **Suche und Identifikation**: Suchbegriff, Kurzname, Herstellernummer, DSP3-ID
- **Vermietung**: Prüfdaten für TÜV, UVV und Bremsen
- **Webshop**: Webshop-Link, externe IDs, nicht-variantierende Website-Attribute
- **Lieferanten**: Hauptlieferant und Lieferanten-Produktnummer
- **Kategorien**: Kategorie-Nummer für vollständige Namensbildung
- **Boni und Sonderverkäufe**: Bonus- und Sonderverkauf-Flags

## Technische Details

| Feld | Wert |
|---|---|
| Technischer Name | `product_custom_fields` |
| Name | `Adds Custom Fields to Products` |
| Author | `Odolution` |
| Version | `19.0.1.0.0` |
| Lizenz | `LGPL-3` |
| Abhängigkeiten | `sale`, `website_sale` |
| Installable | `True` |
| Auto Install | `False` |

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
- `main_supplier_id` (Many2one → `product.supplierinfo`): Hauptlieferant (automatisch berechnet aus `seller_ids[0]`)
- `main_supplier_product_number` (Char): Lieferanten-Produktnummer (automatisch berechnet)

**Webshop und externe IDs:**
- `webshop_link` (Char): Webshop-Link (mit URL-Widget)
- `external_id` (Integer): Externe ID
- `brand_id` (Many2one → `product.brand`): Marke

**Dimensionen:**
- `length` (Char): Länge
- `width` (Char): Breite  
- `height` (Char): Höhe

**One2many/Many2many:**
- `product_website_product_attribute_ids` (One2many → `product.website.attribute.product`): Website-Attributwerte für Produkt
- `product_website_attribute_ids` (Many2many → `product.website.attribute`): Website-Attribute

**Boni und Sonderverkäufe:**
- `bonus_applicable` (Boolean): Bonus anwendbar
- `special_sale_applicable` (Boolean): Sonderverkauf anwendbar

### `product.category`

Erweitert Produktkategorien um:

- `category_number` (Char): Kategorie-Nummer
- `complete_name` (Char, computed): Vollständiger Name mit Kategorie-Nummer

**Berechnung von `complete_name`:**
- Mit Parent: `Parent /[{category_number}] Name`
- Ohne Parent: `[{category_number}] Name`

### Neue Modelle

#### `product.brand`

Eigenes Modell für Produktmarken:

- `name` (Char): Markenname (auch `_rec_name`)
- `image` (Image): Markenbild
- `external_id` (Integer): Externe ID

#### `product.website.attribute`

Modell für **nicht-variantierende** Website-Attribute (erzeugen keine Produktvarianten):

- `name` (Char): Attributname (auch `_rec_name`)
- `external_id` (Integer): Externe ID
- `sequence` (Integer): Sequenz
- `visible` (Boolean): Sichtbar
- `option_ids` (One2many → `product.website.attribute.value`): Attributoptionen

#### `product.website.attribute.value`

Modell für Attributoptionen:

- `name` (Char): Optionname (auch `_rec_name`)
- `external_id` (Integer): Externe ID
- `attribute_id` (Many2one → `product.website.attribute`): Attribut

#### `product.website.attribute.product`

Verknüpfung von Produkten mit Website-Attributen:

- `product_id` (Many2one → `product.product`): Produkt
- `attribute_id` (Many2one → `product.website.attribute`): Attribut
- `value_ids` (Many2many → `product.website.attribute.value`): Werte

### `product.supplierinfo` (indirekt)

Die Felder `main_supplier_id` und `main_supplier_product_number` auf `product.product` werden automatisch aus `seller_ids[0]` berechnet.

## Enthaltene Views

### `views/product_form.xml`

**View:** `product_form_view_inherit`

Erweiterte Produktformularansicht:

- Felder nach `categ_id`: `search_term`, `short_term`
- Felder nach `default_code`: `dsp3_id`
- Felder nach `product_tooltip`: `bonus_applicable`, `special_sale_applicable`, `manufacturer_number`, `main_supplier_id`, `main_supplier_product_number`
- Neuer Notebook-Page **"Product Data"** mit:
  - Group **"Base Data"**: `brand_id`, `width`, `length`, `height`, `weight`
  - Group **"Rent Data"**: `inspection_date`, `uvv_date`, `brake_inspection_date`
  - Group **"Website Data"**: `webshop_link` (URL-Widget), `external_id`, `product_website_product_attribute_ids` (One2many-Liste)

### `views/product_search.xml`

**Views:** 4 separate Records für erweiterte Produktsuche:

1. `product_search_form_view_inherited_name`: "Product" – Suche nach default_code, name, barcode, search_term, short_term
2. `product_search_form_view_inherited_shortterm`: "Kurzname" – Suche nach short_term
3. `product_search_form_view_inherited_searchterm`: "Suchbegriff" – Suche nach search_term
4. `product_search_form_view_inherited_manufacturer`: "Herstellernummer" – Suche nach manufacturer_number

### `views/category.xml`

**View:** `product_category_form_view_inherit`

Erweiterte Kategorieansicht:

- Feld nach `parent_id`: `category_number`

### `views/product_attribute.xml`

**Views:**

- `product_website_attribute_view_form`: Formular für Website-Attribute
- `product_website_attribute_view_tree`: Liste für Website-Attribute (editable="bottom", sequence mit handle)
- `product_website_attribute_value_view_tree`: Liste für Website-Attributwerte (editable="bottom")

### `views/menu.xml`

**Menüpunkte unter "Produktkonfiguration" (sale.prod_config_main):**

- `menu_website_attribute_config`: "Website Attributes" → Action `website_attribute_action`
- `menu_website_attribute_value_config`: "Website Attribute Values" → Action `website_attribute_value_action`

## Security

### `security/groups.xml`

Definiert Benutzergruppen für neue Modelle:

- `product_brand_user`: Product Brand User
- `product_website_attribute_user`: Website Attribute User
- `product_website_attribute_value_user`: Website Attribute Value User
- `product_website_attribute_product_user`: Website Attribute Product User

### `security/ir.model.access.csv`

Definiert Zugriffsrechte (Read/Write/Create/Delete = 1,1,1,1) für:

- `product.brand`
- `product.website.attribute`
- `product.website.attribute.value`
- `product.website.attribute.product`

## Methods

### `product.product._compute_supplier()`

**Depends:** `seller_ids`, `seller_ids.product_code`, `seller_ids.partner_id`, `seller_ids.price`

Berechnet automatisch:
- `main_supplier_id` = `seller_ids[0].partner_id`
- `main_supplier_product_number` = `seller_ids[0].product_code`

### `product.product.name_search()`

Erweiterte Suche nach:
- `name`
- `default_code`
- `description_sale`
- `search_term`
- `short_term`

### `product.category._compute_complete_name()`

**Depends:** `name`, `parent_id.complete_name`

Berechnet `complete_name` mit Kategorie-Nummer im Format:
- Mit Parent: `Parent /[{category_number}] Name`
- Ohne Parent: `[{category_number}] Name`

## Odoo 19 Upgrade

Dieses Modul wurde für **Odoo 19** aktualisiert:

✅ `version: '19.0.1.0.0'` im Manifest  
✅ `installable: True` im Manifest  
✅ `auto_install: False` im Manifest  
✅ `@api.model` entfernt (deprecated in Odoo 19)  
✅ `_rec_name = "name"` für neue Modelle (`product.brand`, `product.website.attribute`, `product.website.attribute.value`)  
✅ Duplicate View ID korrigiert (`product_website_attribute_value_view_tree`)  
✅ Duplicate Action ID korrigiert (`website_attribute_value_action`)  
✅ Search View mit separate Records umstrukturiert (4 Records statt 1 mit multiple field)  
✅ Groups in `security/groups.xml` definiert  

## Installation

1. Modul in den Addons-Pfad von Odoo legen
2. App-Liste in Odoo aktualisieren
3. Modul installieren oder bei bestehender Installation upgraden

## Hinweise

- Das Modul ist primär für **Vermietungs-Baumaschinen** konzipiert (Prüfdaten, Vermietung-Flag)
- Website-Attribute sind **"non Variant Creating"** – erzeugen keine Produktvarianten
- `main_supplier_id` wird **automatisch** aus dem ersten Seller (`seller_ids[0]`) berechnet
- `complete_name` bei Kategorien enthält Kategorie-Nummer für bessere Lesbarkeit
- `webshop_link` nutzt das Odoo **URL-Widget** für klickbare Links
