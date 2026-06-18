# Partner History

## Übersicht

Dieses Modul erweitert den Odoo Partner (Kunde/Lieferant, `res.partner`) um eine **Historie mit Umsatz- und Margen-Daten** per Jahr. Es ermöglicht die Dokumentation von:

- **Jahres-Umsatz** (`total_turnover`) pro Partner
- **Jahres-Marge** (`total_margin`) pro Partner
- **Kategorie** (`category_id`) für Filterung/Zuordnung
- **Notiz** (`note`) für zusätzliche Informationen
- **Jahr** (`year`) als Selection von 1900 bis aktuell

Ideal für **Kundenhistorie**, **Vertriebs-Tracking** und **Marge-Analyse** pro Jahr.

## Technische Details

| Feld | Wert |
|---|---|
| Technischer Name | `partner_history` |
| Name | `partner_history` |
| Version | `1.0` |
| Author | `Michael Otto` |
| Lizenz | `LGPL-3` |
| Abhängigkeiten | `base`, `sale` |
| External Dependencies | Python: [], Bin: [] |

## Funktionsumfang

### Partner-Historie per Jahr

**Was:** Jede Partner hat eine Liste von Historie-Einträgen (`partner.history.fs`) mit Umsatz und Marge pro Jahr.

**Wie:**
- `res.partner` inherit mit `partner_history_ids` (One2many → `partner.history.fs`)
- Historie-Einträge enthalten:
  - `year`: Jahr (Selection 1900-attuale)
  - `category_id`: Produkt-Kategorie (Many2one)
  - `total_turnover`: Gesamtumsatz (Monetary)
  - `total_margin`: Gesamtmarge (Monetary)
  - `currency_id`: Währung (Many2one, default = company currency)
  - `note`: Notiz (Char)

**UI:**
- Neuer Notebook-Page **"History"** im Partner-Form
- Inline-editable List (`editable="bottom"`)
- Monetary Widgets für Umsatz und Marge
- `currency_id` column_invisible (wird benutzt für Widget, nicht angezeigt)

### Zeitzonen-sicheres Jahr

**Was:** `year` Selection nutzt `context_today()` für zeitzonen-sicheres aktuelles Jahr.

**Wie:**
```python
@api.model
def _get_year_selection(self):
    current = fields.Date.context_today(self).year
    return [(str(y), str(y)) for y in range(1900, current + 1)]
```

- Range: 1900 bis aktuell + 1
- Default: `str(fields.Date.context_today(self).year)`

### Monetary Felder

**Was:** `total_turnover` und `total_margin` nutzen `widget="monetary"` mit `currency_id`.

**Wie:**
```python
currency_id = fields.Many2one(
    'res.currency', 
    string='Currency', 
    default=lambda self: self.env.company.currency_id.id
)

total_turnover = fields.Monetary(string="Total Turnover", currency_field="currency_id")
total_margin = fields.Monetary(string="Total Margin", currency_field="currency_id")
```

- `currency_field="currency_id"` sagt Odoo welche Währung benutzen
- `widget="monetary"` in XML für korrekte Formatierung

## Enthaltene Assets

### `views/res_partner.xml`

**View:** `partner_form_view_inherit_partner_history`

- Inherit: `base.view_partner_form`
- XPath: `//notebook` position="inside"
- Neuer Page: `<page string="History">`
- Field: `partner_history_ids` mit `list editable="bottom"`

**List Fields:**
```xml
<field name="currency_id" column_invisible="True"/>  <!-- Für monetary Widget -->
<field name="year"/>
<field name="category_id"/>
<field name="total_turnover" widget="monetary"/>
<field name="total_margin" widget="monetary"/>
<field name="note"/>
```

### `security/ir.model.access.csv`

**Access:**
```csv
model_id:id,group_id:id,id,name,perm_read,perm_write,perm_create,perm_unlink
model_partner_history_fs,base.group_user,partner_history_fs_user,partner.history.fs.user,1,1,1,1
```

- **Modell:** `partner.history.fs`
- **Group:** `base.group_user` (alle Users)
- **Permissions:** Read=1, Write=1, Create=1, Unlink=1 (vollzugriff)

## Models

### `res.partner`

**Inherit:** `res.partner`

**Neues Feld:**
- `partner_history_ids` (One2many → `partner.history.fs`)
  - `string='Partner History'`
  - Related: `'partner_id'` auf History-Model

### `partner.history.fs`

**Name:** `partner.history.fs`

**Description:** `Partner History`

**Felder:**

#### `year` (Selection)

- Selection: `_get_year_selection()` (1900- aktuelle Jahr)
- String: `'Year'`
- Default: `str(fields.Date.context_today(self).year)` (aktuelles Jahr)
- Help: `"Select the year"`

**Zeitzonen-sicher:** Nutzt `context_today()` statt `datetime.now()`

#### `category_id` (Many2one)

- Model: `product.category`
- String: `'Categories'`

#### `currency_id` (Many2one)

- Model: `res.currency`
- String: `'Currency'`
- Default: `self.env.company.currency_id.id` (Firma-Währung)
- **Zweck:** Wird für `widget="monetary"` benutzt, `column_invisible="True"` in View

#### `total_turnover` (Monetary)

- String: `"Total Turnover"`
- `currency_field="currency_id"` (Währung riferimento)
- `widget="monetary"` in View für Formatierung

#### `total_margin` (Monetary)

- String: `"Total Margin"`
- `currency_field="currency_id"` (Währung riferimento)
- `widget="monetary"` in View für Formatierung

#### `partner_id` (Many2one)

- Model: `res.partner`
- String: `'Partner'`
- Related auf One2many `partner_history_ids`

#### `note` (Char)

- String: `'Note'`
- Freie Notiz

## API Methods

### `_get_year_selection()`

**Decorator:** `@api.model`

**Was:** Generiert Selection-Liste für Jahre.

**Wie:**
```python
current = fields.Date.context_today(self).year
return [(str(y), str(y)) for y in range(1900, current + 1)]
```

**Returns:** Liste von `(selection_value, display_value)` Tuples
- Beispiel: `[('1900', '1900'), ('1901', '1901'), ..., ('2026', '2026')]`

**Zeitzonen-sicher:** `context_today()` nutzt User-Timezone aus Context

## Odoo 19 Kompatibilität

### @api.model

- `@api.model` auf `_get_year_selection()` ist korrekt (keine Instanz nötig)
- Alternative: `@api.model` kann auch `@api.depends()` nutzen wenn Selection dynamic

### Monetary Widget

- `widget="monetary"` in Odoo 19 funktioniert mit `currency_field`
- `column_invisible="True"` für `currency_id` ist korrekt (wird intern benutzt)

### context_today

- `fields.Date.context_today(self)` ist zeitzonen-sicher
- Alternative: `self.env.context.get('tz')` für Timezone

## Installation

1. Modul in den Addons-Pfad von Odoo legen
2. App-Liste aktualisieren
3. Modul installieren
4. Partner-Form neu laden (F5)

## Workflow

### Historie-Eintrag erstellen

1. **Partner öffnen** (Kunde/Lieferant)
2. **Notebook Page "History"** klicken
3. **Leere Row** in Liste (automatisch durch `editable="bottom"`)
4. **Felder füllen:**
   - `year`: Jahr auswählen (z.B. "2024")
   - `category_id`: Kategorie auswählen (optional)
   - `total_turnover`: Umsatz eingeben (z.B. "50000.00")
   - `total_margin`: Marge eingeben (z.B. "15000.00")
   - `note`: Notiz (optional)
5. **Automatisch gespeichert** (inline editable)

### Historie anzeigen

1. **Partner öffnen**
2. **Page "History"** klicken
3. **Alle Einträge** per Jahr anzeigen
4. **Umsatz und Marge** mit Währung-formatiert

## Hinweise

- **Währung:** Default ist Firma-Währung (`company.currency_id`)
- **Monetary Widget:** Formatiert automatisch mit Währung-Symbol (z.B. "€ 50.000,00")
- **Column Invisible:** `currency_id` wird nicht angezeigt, aber für Widget benutzt
- **Editable Bottom:** Inline-Bearbeitung ohne separaten Form
- **Year Range:** 1900 bis aktuell + 1 (automatisch aktualisiert)
- **Zeitzonen-sicher:** `context_today()` nutzt User-Timezone
- **Access:** Alle Users (`base.group_user`) haben Full Access

## Verwendung

### Für Vertriebs-Tracking

- Historie pro Jahr dokumentieren
- Umsatz und Marge per Jahr tracken
- Kategorie für Segmentierung (z.B. Produktgruppen)

### Für Kundenanalyse

- Warenkorb-Historie per Jahr
- Marge-Analyse pro Kunde
- Notiz für besondere Informationen

### Für Reporting

- Daten für Dashboard nutzen
- Filter nach Kategorie
- Vergleich Jahr über Jahr
