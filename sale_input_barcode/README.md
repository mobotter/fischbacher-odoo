# Sale Input Barcode

## Übersicht

Dieses Modul erweitert den Odoo Verkaufsauftrag (sale.order) um eine **automatische Produkt-Eingabe via Barcode**. Nach der Produktauswahl wird **sofort eine neue Verkaufszeile** angelegt, damit der nächste Produkt-Barcode direkt eingegeben werden kann.

Ideal für **schnelle Masseneingaben** von Produkten im Verkaufsauftrag, besonders geeignet für:

- Barcode-Scanner im Verkauf
- Schnelle Bestell-Eingabe ohne manuelles "Produkt hinzufügen" klicken
- Wareneingang mit schnellen Produkt-Scans

## Technische Details

| Feld | Wert |
|---|---|
| Technischer Name | `sale_input_barcode` |
| Name | `Sale Input Barcode` |
| Version | `19.0.5.0.0` |
| Author | `Moritz Kern` |
| Kategorie | `Sales/Sales` |
| Lizenz | `AGPL-3` |
| Abhängigkeiten | `sale_management`, `product`, `web` |
| Application | `False` |
| Installable | `True` |

## Funktionsumfang

### Automatische neue Verkaufszeile nach Produktauswahl

**Was:** Nach der Auswahl eines Produkt in der Verkaufszeile wird **automatisch eine neue Zeile** angelegt.

**Wie:**
- JavaScript-Event Listener auf `keydown` für `Enter`-Taste
- Detectet Produkt-Input im Feld `product_template_id`
- Bei `Enter`:
  - Klickt automatisch auf "Produkt hinzufügen" (`Add a product`)
  - Fokussiert das **neueste** Produkt-Input-Feld
  - Clear den Inputwert für nächsten Barcode

**Workflow:**
1. Produkt-Barcode im Input eingeben (oder auswählen)
2. `Enter` drücken
3. Produkt wird ausgewählt
4. **Automatisch neue Zeile** angelegt
5. Input-Feld der neuen Zeile ist fokussiert und clear
6. Nächster Barcode kann eingegeben werden

### Duplicate Barcode Lines Merge

**Was:** Bei duplizierten Produkten in Verkaufszeilen wird die Menge automatisch zusammengefasst.

**Wie:**
- `SaleOrder._merge_duplicate_barcode_lines()`
- Grouped nach `product_id.id`
-第一位 Zeile bleibt, weitere werden entfernt
- Menge wird addiert: `grouped[key].product_uom_qty += line.product_uom_qty`
- Duplicate Lines werden `unlink()`

**Trigger:**
- Beim Erstellen: `@api.model_create_multi create()`
- Beim Schreiben: `write()`

**Beispiel:**
Zeile 1: Produkt A, Menge 2
Zeile 2: Produkt A, Menge 3
→ Nach Merge:
Zeile 1: Produkt A, Menge 5
## Enthaltene Assets

### `web.assets_backend`

Backend-Assets:

**`static/src/js/sale_order_line.js`:**
- Event Listener auf `keydown` für `Enter`-Taste
- Detectet Produkt-Input mit Selector: `td[name="product_template_id"] input.o-autocomplete--input`
- Klick auf "Produkt hinzufügen" mit Selector: `.o_sale_input_barcode_order_line .o_field_x2many_list_row_add a[role="button"]`
- Auto-Select der aktiven Dropdown-Option
- Retry-Mechanismen für DOM-Ready (12 retries, 120-150ms delay)

### `views/sale_order_views.xml`

**View:** `view_order_form_sale_input_barcode`

- Inherit: `sale.view_order_form`
- XPath: `//field[@name='order_line']` position="attributes"
- Setzt Klasse: `class="o_sale_input_barcode_order_line"` auf order_line Field

**Warum Klasse nötig:** JavaScript-Detector nutzt Klasse für Selector

## Models

### `sale.order`

**Inherit:** `sale.order`

**Neues Feld:**
- `barcode_scan` (Char): Barcode Scan
  - `string='Barcode Scan'`
  - `copy=False` (nicht beim Kopieren übertragen)

**Methoden:**

#### `_merge_duplicate_barcode_lines()`

**Was:** Merge duplicate Produkt-Lines und addiert Menge.

**Wie:**
```python
grouped = {}
lines_to_remove = self.env['sale.order.line']

for line in order.order_line.filtered(lambda l: not l.display_type and l.product_id):
    key = line.product_id.id
    if key not in grouped:
        grouped[key] = line
        continue
    
    grouped[key].product_uom_qty += line.product_uom_qty
    lines_to_remove |= line

if lines_to_remove:
    lines_to_remove.unlink()
```

**Trigger:**
- `create()`: Nach `super().create(vals_list)`
- `write()`: Nach `super().write(vals)`

#### `create(vals_list)`

**Override:** Erstellt Orders und merge dupl icate Lines.

```python
orders = super().create(vals_list)
orders._merge_duplicate_barcode_lines()
return orders
```

#### `write(vals)`

**Override:** Schreibt Orders und merge duplicate Lines.

```python
res = super().write(vals)
self._merge_duplicate_barcode_lines()
return res
```

## Security

### `security/ir.model.access.csv`

**Access:**
```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_sale_order_barcode_user,sale.order.barcode.user,sale.model_sale_order,sales_team.group_sale_salesman,1,1,1,0
```

- **Modell:** `sale.order`
- **Group:** `sales_team.group_sale_salesman` (Salesman)
- **Permissions:** Read=1, Write=1, Create=1, Unlink=0 (kein Delete)

## JavaScript Logik (sale_order_line.js)

### Selectors

**ADD_PRODUCT_SELECTOR:**
```javascript
'.o_sale_input_barcode_order_line .o_field_x2many_list_row_add a[role="button"]'
```
- Klick-Link für "Produkt hinzufügen" / "Add a product"

**PRODUCT_INPUT_SELECTOR:**
```javascript
'td[name="product_template_id"] input.o-autocomplete--input'
```
- Produkt-Input-Feld im Order-Line Table

### Functions

#### `getAddProductLink()`

Findet "Produkt hinzufügen" Link im DOM.

#### `getNewestProductInput()`

Findet das **neueste** (letzte) Produkt-Input-Feld.

#### `focusNewestProductInput(retries=12)`

- Fokussiert neuestes Input
- Clear Wert: `input.value = ""`
- Setzt `ignoreEnterUntil = Date.now() + 650` (650ms Ignore nach Focus)
- Retry bis 12x bei 150ms delay

#### `addNextProductLine()`

- Klickt auf "Produkt hinzufügen"
- Fokussiert nach 450ms neues Input

#### `getActiveOption(input)`

Findet die aktive Dropdown-Option (aria-activedescendant oder .ui-state-active).

#### `tryAutoSelect(input, retries=12)`

- Prüft ob Dropdown expanded (`aria-expanded="true"`)
- Prüft ob reale Option (nicht "lädt..." / "loading...")
- Klickt Option automatisch
- Nach 350ms: Prüft ob Input-value gesetzt und Dropdown closed
- Wenn ja: `addNextProductLine()` (neue Zeile)
- Retry bis 12x bei 120ms delay

### Event Listener

**`keydown` auf Document:**

```javascript
document.addEventListener("keydown", (ev) => {
    const target = ev.target;
    if (!(target instanceof HTMLInputElement)) return;
    if (!target.matches(PRODUCT_INPUT_SELECTOR)) return;
    if (ev.key !== "Enter") return;
    
    ev.preventDefault();
    ev.stopPropagation();
    ev.stopImmediatePropagation();
    
    if (Date.now() < ignoreEnterUntil) return;
    
    const value = (target.value || "").trim();
    if (!value) return;
    
    window.setTimeout(() => {
        const currentValue = (target.value || "").trim();
        const currentExpanded = target.getAttribute("aria-expanded");
        
        if (!currentValue) return;
        
        if (currentExpanded === "true") {
            tryAutoSelect(target);  // Auto-select Dropdown-Option
            return;
        }
        
        addNextProductLine();  // Neue Zeile
    }, 250);
}, true);
```

**Logik bei Enter:**
1. PrevDrvent + StopPropagation + StopImmediatePropagation
2. Ignore wenn innerhalb von 650ms nach Focus
3. Pr ufe value (nicht empty)
4. 250ms Delay für DOM-Ready
5. Wenn Dropdown expanded: `tryAutoSelect()` (auto-select Option)
6. Wenn Dropdown closed: `addNextProductLine()` (neue Zeile)

## Odoo 19 Kompatibilität

### OWL Module Syntax

- `/** @odoo-module **/` am Anfang (auch wenn nicht importiert)
- jQuery-DOM-Selector nutzen (`document.querySelectorAll`)
- Keine Odoo-Services für DOM-Zugriff

### Event Handling

- `ev.preventDefault()` + `ev.stopPropagation()` + `ev.stopImmediatePropagation()`
- `instanceof HTMLInputElement` Type-Check
- `target.matches()` Selector-Check

### Retry-Mechanismen

- `focusNewestProductInput()`: 12 retries bei 150ms
- `tryAutoSelect()`: 12 retries bei 120ms
- Timeout für DOM-Ready: 250ms, 350ms, 450ms

## Installation

1. Modul in den Addons-Pfad von Odoo legen
2. App-Liste aktualisieren
3. Modul installieren
4. Verkaufsauftrag-Form neu laden (F5 + Cache clear)

## Workflow

###Masseneingabe mit Barcode-Scanner

1. Verkaufsauftrag öffnen oder erstellen
2. In `order_line` Tabelle klicken
3. **Produkt-Barcode** eingeben (oder manuell auswählen)
4. **`Enter` drücken**
5. Produkt wird ausgewählt
6. **Automatisch neue Zeile** angelegt
7. Neues Input-Feld ist fokussiert und clear
8. **Nächster Barcode** eingeben
9. Wiederholen ab Schritt 4

### Beispiel
Input: "ARTIKEL-001" → Enter
→ Produkt "ARTIKEL-001" ausgewählt
→ Neue Zeile angelegt, Input fokussiert

Input: "ARTIKEL-002" → Enter
→ Produkt "ARTIKEL-002" ausgewählt
→ Neue Zeile angelegt, Input fokussiert

Input: "ARTIKEL-001" → Enter
→ Produkt "ARTIKEL-001" ausgewählt
→ Neue Zeile angelegt
→ _merge_duplicate_barcode_lines() läuft
→ Zeilen 1 und 3 merged: Menge addiert


## Hinweise

- **Barcode-Scanner:** Ideal für schnelle Masseneingabe mit Barcode-Scanner
- **Enter-Taste:** `Enter` triggert Auswahl + neue Zeile
- **Auto-Select:** Dropdown-Option wird automatisch ausgewählt wenn expanded
- **Duplicate Merge:** Duplizierte Produkte werden automatisch mit Menge zusammengefasst
- **Ignore Enter:** 650ms Ignore nach Focus für korrekte DOM-Init
- **Retry-Loops:** 12 retries für DOM-Ready bei langsamen Loads
- **Klasse nötig:** `o_sale_input_barcode_order_line` auf `order_line` Field für Selector

## Fehlerbehandlung

### Input nicht fokussiert

- Retry bis 12x bei 150ms für `focusNewestProductInput()`
- user muss ggf. manuell ins Input klicken

### Dropdown nicht expanded

- `tryAutoSelect()` retry bis 12x bei 120ms
- Wenn kein expanded: direkte `addNextProductLine()`

### Keine "Produkt hinzufügen" gefunden

- `getAddProductLink()` returns `null`
- Keine nuova Zeile angelegt
- user muss manuell klicken

### Duplicate nicht merged

- Prüfe `display_type` Filter (nur echte Produkt-Lines)
- Prüfe `product_id` Filter (nur Lines mit Produkt)
