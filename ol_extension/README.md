# Fischbacher Extension

## Übersicht

Dieses Modul ist eine **kundenspezifische Erweiterung** für Fischbacher mit zahlreichen Anpassungen an Berichten, Modellen und Views. Es implementiert 7 verschiedene Task-Anforderungen für Verkaufsprozesse, Adress-Berichte und Partner-Datenverwaltung.

## Technische Details

| Feld | Wert |
|---|---|
| Technischer Name | `ol_extension` |
| Name | `Fischbacher Extension` |
| Version | `19.0.1.0.0` |
| Author | `Sana Khalid` |
| Kategorie | `Customizations` |
| Lizenz | `LGPL-3` |
| Abhängigkeiten | `base`, `contacts`, `stock`, `stock_delivery`, `sale`, `account`, `l10n_din5008`, `l10n_din5008_sale` |
| Application | `False` |
| Installable | `True` |
| Auto Install | `False` |

## Task IDs

| Task ID | Beschreibung |
|---|---|
| 51015 | Kontakte-Aktion auf Unternehmen-only filteren |
| 51016 | Client Info Lines zu Partner hinzufügen |
| 51017 | Contact Persons zu Partner hinzufügen |
| 51579 | Lieferschein-Report Titel und Warehouse anpassen |
| 51580 | Lieferadresse zu sale.order hinzufügen und Proforma Invoice Reports anpassen |
| 51827 | short_term Feld zu res.partner hinzufügen |
| 52132 | Leerlinie vor information_block in Invoice hinzufügen |

## Funktionsumfang

### 1. Client Info Lines (TASK 51016)

**Was:** Zeilen für Kundeninformationen im Partner (Kunde).

**Wie:**
- Neues Modell: `client.info`
- One2many auf `res.partner`: `client_info_ids`
- Felder:
  - `sequence`: Sequenz (default=10, widget="handle")
  - `pos`: Position (Char)
  - `info`: Info-Text (Char)
  - `partner_id`: Partner (Many2one, ondelete="cascade", invisible in Form)

**Order:** `sequence, id` (Sortierung nach Sequenz)

**UI in Partner:**
- Neuer Page **"Client Info"** im Partner-Form
- Liste `editable="bottom"` (Inline-Bearbeitung)
- Felder: `pos`, `info`

### 2. Contact Persons (TASK 51017)

**Was:** Ansprechpartner im Partner mit vollständigen Kontaktdaten.

**Wie:**
- Neues Modell: `contact.person`
- One2many auf `res.partner`: `contact_person_ids`
- Felder:
  - `salutation`: Anrede (Selection: mr, ms, buchh, dr_med, fr, hr, heerr, vater)
  - `first_name`: Vorname (Char)
  - `last_name`: Nachname (Char)
  - `phone_prefix`: Telefon-Präfix (Char)
  - `phone`: Telefon (Char)
  - `mobile`: Mobil (Char)
  - `info`: Info-Text (Char)
  - `email`: Email (Char)
  - `partner_id`: Partner (Many2one, ondelete="cascade")

**UI in Partner:**
- Neuer Page **"Contact Persons"** im Partner-Form
- Liste `editable="bottom"` (Inline-Bearbeitung)
- Felder: `salutation`, `first_name`, `last_name`, `phone_prefix`, `phone`, `mobile`, `info`, `email`
- Options: `no_create=False`, `no_edit=False`

### 3. Short Term (TASK 51827)

**Was:** Kurzname/Feld für schnelle Referenz im Partner.

**Wie:**
- Feld auf `res.partner`: `short_term` (Char)
- `copy=True` (beim Kopieren übertragen)

**UI in Partner:**
- Nach `mobile_blacklisted` Feld im Kopf-Section
- Einzelnes Feld

### 4. Delivery Address 2 (TASK 51580)

**Was:** Zusätzliche Lieferadresse im Verkaufsauftrag für manuelle Adressen.

**Wie:**
- Feld auf `sale.order`: `delivery_address` (Text)
- `copy=True` (beim Kopieren übertragen)

**UI in Sale Order:**
- Nach `partner_shipping_id` Feld
- Text-Feld für manuelle Adresse

### 5. Lieferschein Report (TASK 51579)

**Was:** Anpassungen im Lieferschein-Report (Delivery Note).

**Änderungen:**

**report_delivery_document_inherit:**
- Titel geändert zu: `"Delivery Note"`
- Ersetzt `din5008_document_title`

**report_delivery_document2_inherit:**
- Warehouse-Info nach `shipping_weight` hinzugefügt
- Zeigt `o.name` (Sale Order Name) als Warehouse

**UI:**
- Lieferschein zeigt "Delivery Note" statt Standard-Titel
- Warehouse (Sale Order) wird angezeigt

### 6. Proforma Invoice Report (TASK 51580)

**Was:** Angepasste Adress-Blöcke in Invoice und Proforma Invoice Reports.

**Änderungen:**

**report_invoice_document_inherit (Invoice):**
- Adress-Block ersetzt (`din5008_address_block`)
- **Shipping Address:**
  - Wenn `delivery_partner` vorhanden: Zeige manuelle Adresse (`delivery_partner`)
  - Wenn kein `delivery_partner`: Zeige `partner_shipping_id`
- **Beneficiary:**
  - Wenn `invoice_partner != commercial_partner`: Zeige invoizierende Partner
  - Mit VAT/Tax ID wenn vorhanden

**report_saleorder_document_inherit (Proforma/Sale Order):**
- Adress-Block ersetzt (`din5008_address_block`)
- **Proforma (context.proforma=True):**
  - Zeige separate Shipping und Beneficiary Addresses
  - Wenn `delivery_partner`: Manuelle Adresse
  - Beneficiary mit VAT/Tax ID
- **Normal (Proforma=False):**
  - Wenn `partner_invoice_id == partner_shipping_id`: Zeige "Invoicing and Shipping Address" kombiniert
  - Wenn unterschiedlich: Zeige separate Shipping und Invoicing Addresses

**Logik:**
```python
delivery_partner = o.line_ids.sale_line_ids.order_id.delivery_address
```

### 7. Leerlinie in Invoice (TASK 52132)

**Was:** Zusätzliche Leerlinie vor information_block in Invoice Report.

**Wie:**
- `<br />` vor `//div[hasclass('information_block')]`

**UI:**
- Mehr Abstand vor Informations-Block in Invoice

## Modelle

### `client.info`

**Name:** `client.info`

**Description:** `Client Info Lines`

**Order:** `sequence, id`

**Felder:**
- `sequence` (Integer): Sequenz, default=10
- `pos` (Char): Position
- `info` (Char): Info-Text
- `partner_id` (Many2one → `res.partner`): Partner, ondelete="cascade", index

### `contact.person`

**Name:** `contact.person`

**Description:** `Contact Persons`

**Felder:**
- `salutation` (Selection): Anrede
  - Optionen: `mr` (Mr.), `ms` (Ms.), `buchh` (Buchh.), `dr_med` (Dr. med.), `fr` (Fr.), `hr` (Hr), `heerr` (Heerr), `vater` (Vater)
- `first_name` (Char): Vorname
- `last_name` (Char): Nachname
- `phone_prefix` (Char): Telefon-Präfix
- `phone` (Char): Telefon
- `mobile` (Char): Mobil
- `info` (Char): Info-Text
- `email` (Char): Email
- `partner_id` (Many2one → `res.partner`): Partner, ondelete="cascade", index

### `res.partner`

**Inherit:** `res.partner`

**Neue Felder:**
- `client_info_ids` (One2many → `client.info`): Client Info Lines, copy=True
- `contact_person_ids` (One2many → `contact.person`): Contact Persons, copy=True
- `short_term` (Char): Short Term, copy=True

### `sale.order`

**Inherit:** `sale.order`

**Neues Feld:**
- `delivery_address` (Text): Delivery Address 2, copy=True

## Reports

### `reports/report_delivery_document.xml`

**Templates:**

1. **`report_delivery_document_inherit`**
   - Inherit: `stock.report_delivery_document`
   - Ersetzt Titel zu: `"Delivery Note"`
   - TASK: 51579

2. **`report_delivery_document2_inherit`**
   - Inherit: `stock_delivery.report_delivery_document2`
   - Nach `shipping_weight`: Warehouse-Info hinzugefügt
   - Zeigt Sale Order Name (`o.name`)
   - TASK: 51579

### `reports/report_invoice_document.xml`

**Template:**

**`report_invoice_document_inherit`:**
- Inherit: `l10n_din5008.report_invoice_document`
- Vor `information_block`: `<br />` (TASK 52132)
- Ersetzt `din5008_address_block`:
  - Shipping Address mit `delivery_partner` (manuelle Adresse)
  - Beneficiary mit VAT/Tax ID
  - TASK: 51580

**Korrektur:**
- **Original Fehler:** `doc.delivery_address` (Variable nicht definiert)
- **Korrektur:** `delivery_partner.replace('\n', '<br/>')`

### `reports/report_saleorder_document.xml`

**Template:**

**`report_saleorder_document_inherit`:**
- Inherit: `l10n_din5008_sale.report_saleorder_document`
- Ersetzt `din5008_address_block`:
  - **Proforma (context.proforma=True):**
    - Shipping Address mit `delivery_partner`
    - Beneficiary mit VAT/Tax ID
  - **Normal:**
    - Wenn `invoice == shipping`: Kombiniert "Invoicing and Shipping Address"
    - Wenn unterschiedlich: Separate Shipping und Invoicing Addresses
  - TASK: 51580

## Views

### `views/client_info.xml`

**Views für `client.info`:**

1. **`view_client_info_list`:**
   - Listeditable: `editable="bottom"`
   - Felder: `sequence` (widget="handle"), `pos`, `info`

2. **`view_client_info_form`:**
   - Form mit Group
   - Felder: `pos`, `info`, `partner_id` (invisible=1)

### `views/res_partner.xml`

**Änderungen:**

1. **`contacts.action_contacts` Override:**
   - Context: `{'search_default_type_company': 1}`
   - Zeigt nur Unternehmen in Kontakte-Liste
   - TASK: 51015
   - **Hinweis:** Globale Action override, betrifft alle Users

2. **`res_partner_form_inherit`:**
   - Inherit: `base.view_partner_form`
   - Nach `mobile_blacklisted`: `short_term` Feld (TASK 51827)
   - In Notebook:
     - Page "Client Info" mit `client_info_ids` (TASK 51016)
     - Page "Contact Persons" mit `contact_person_ids` (TASK 51017)

### `views/sale_order.xml`

**View:**

**`sale_order_form_inherit`:**
- Inherit: `sale.view_order_form`
- Nach `partner_shipping_id`: `delivery_address` Feld (Text)
- TASK: 51580

## Security

### `security/ir.model.access.csv`

**Access Rights:**

1. **`access_client_info_user`:**
   - Modell: `model_client_info`
   - Group: `base.group_user`
   - Permissions: Read=1, Write=1, Create=1, Unlink=1

2. **`access_contact_person_user`:**
   - Modell: `model_contact_person`
   - Group: `base.group_user`
   - Permissions: Read=1, Write=1, Create=1, Unlink=1

## Workflow

### Client Info hinzufügen

1. **Partner öffnen** (Kunde)
2. **Page "Client Info"** klicken
3. **Inline-Row** in Liste
4. **Felder füllen:**
   - `pos`: Position (z.B. "1", "2")
   - `info`: Info-Text (z.B. "Kundennummer: 12345")
5. **Automatisch gespeichert**

### Contact Person hinzufügen

1. **Partner öffnen** (Kunde)
2. **Page "Contact Persons"** klicken
3. **Inline-Row** in Liste
4. **Felder füllen:**
   - `salutation`: Anrede wählen
   - `first_name`: Vorname
   - `last_name`: Nachname
   - `phone_prefix`: Telefon-Präfix (z.B. "+49")
   - `phone`: Telefon
   - `mobile`: Mobil
   - `email`: Email
   - `info`: Info (optional)
5. **Automatisch gespeichert**

### Lieferadresse im Sale Order

1. **Sale Order öffnen**
2. **Lieferadresse Feld** (`delivery_address`) nach `partner_shipping_id`
3. **Manuelle Adresse eingeben** ( multiline Text)
4. **In Report angezeigt** (Proforma Invoice)

### Proforma Invoice drucken

1. **Sale Order öffnen**
2. **Aktions-Menü** → "Proforma Invoice"
3. **Report zeigt:**
   - Separate Shipping Address (mit manuelle `delivery_address`)
   - Beneficiary mit VAT/Tax ID
4. **PDF generiert**

## Odoo 19 Kompatibilität

### Template Syntax

- `t-set`/`t-value`: Odoo 19 Variablen
- `t-if`/`t-else`: Bedingte Anzeige
- `t-esc`/`t-raw`: Output (escaped/raw)
- `t-options`: Widget-Options

### Report Binding

- `inherit_id`: Korrekte Referenz auf Standard-Reports
- `xpath position="replace"`: Ersetzen ganzer Sections
- `position="before"`: Einfügen vor Element

### Variable Naming

**Invoice Report:**
- `o`: account.move (Invoice)
- `delivery_partner`: String (manuelle Adresse)
- **Korrektur:** `delivery_partner.replace('\n', '<br/>')` statt `doc.delivery_address`

**Sale Order Report:**
- `doc`: sale.order (Verkaufsauftrag)
- `delivery_address`: Text-Feld auf sale.order

## Installation

1. Modul in den Addons-Pfad von Odoo legen
2. App-Liste aktualisieren
3. Modul installieren
4. Partner/Sale Order neu laden (F5 + Cache clear)

## Hinweise

### TASK 51015 - Global Action Override

- **Achtung:** `contacts.action_contacts` Override betrifft **alle** Kontakte im System
- **Hinweis:** Nur Unternehmen werden in Kontakte-Liste angezeigt
- **Alternative:** Custom Action erstellen statt globales Override

### TASK 51580 - Delivery Address

- `delivery_address` ist **Text-Feld** für manuelle Adresse
- Wird in **Proforma Invoice** angezeigt ( Shipping Address)
- In **normal Sale Order**: Kombiniert wenn invoice == shipping

### TASK 51580 - Report Korrektur

- **Original Fehler:** `doc.delivery_address` in Invoice Report (Variable nicht definiert)
- **Korrektur:** `delivery_partner.replace('\n', '<br/>')`
- **Korrektur Datei:** `reports/report_invoice_document.xml`

### Client Info / Contact Persons

- `partner_id` ist **invisible** in List/Form (via One2many gesetzt)
- `copy=True`: Wird beim Kopieren von Partner übertragen
- `ondelete="cascade"`: Wird gelöscht wenn Partner gelöscht

### DIN 5008 Localization

- Modul nutzt `l10n_din5008` und `l10n_din5008_sale` für deutsche Adress-Formatierung
- `din5008_address_block`: Standard Adress-Block wird ersetzt

## Fehlerkorrektur

### ❌ ERROR: report_invoice_document.xml

**Issue:** Variable `doc` nicht definiert in Invoice Report

**Original:**
```xml
<div t-field="doc.delivery_address" t-options="{'widget': 'text'}" />
```

**Korrektur:**
```xml
<div t-esc="delivery_partner.replace('\n', '&lt;br/&gt;')" />
```

**Begründung:**
- Invoice Report nutzt `o` (account.move), nicht `doc`
- `delivery_partner` ist bereits als Variable gesetzt
- `t-esc` mit `replace()` für Zeilenumbrüche

### ⚠️ WARNING: contacts.action_contacts Override

**Issue:** Globale Action-Override betrifft alle Users

**Recommendation:**
- Wenn nur für Fischbacher: Custom Action erstellen
- Wenn für alle OK: Current behavior ist geplant

## Task ID Checkliste

| Task ID | Status | File |
|---|---|---|
| 51015 | ✅ Implemented | views/res_partner.xml |
| 51016 | ✅ Implemented | models/client_info.py, views/client_info.xml, views/res_partner.xml |
| 51017 | ✅ Implemented | models/contact_person.py, views/res_partner.xml |
| 51579 | ✅ Implemented | reports/report_delivery_document.xml |
| 51580 | ✅ Implemented (korrigiert) | models/sale_order.py, reports/report_saleorder_document.xml, reports/report_invoice_document.xml |
| 51827 | ✅ Implemented | models/res_partner.py, views/res_partner.xml |
| 52132 | ✅ Implemented | reports/report_invoice_document.xml |
