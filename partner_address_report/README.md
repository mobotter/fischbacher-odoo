# Partner Address Report

## Übersicht

Dieses Modul erstellt einen **druckbaren Adress-Report für Partner** (Kunden/Kontaktpersonen) in Odoo. Es bietet zwei Report-Varianten:

1. **PDF-Report (A6)**: Standard-Adress-Report für Druck auf A6-Etiketten
2. **ZPL-Report (A6)**: Zellettikette im ZPL-Format für Barcode/Etiketten-Drucker

Ideal für **Adress-Etiketten**, **Paketadressen**, **Kundenadressen** und **Feldservice**.

## Technische Details

| Feld | Wert |
|---|---|
| Technischer Name | `partner_address_report` |
| Name | `Partner Address Report` |
| Version | `19.0.1.0.0` |
| Author | `Odolution` |
| Kategorie | `Contacts` |
| Lizenz | `LGPL-3` |
| Abhängigkeiten | `base` |
| Application | `False` |
| Installable | `True` |
| Summary | `Custom printable report for res.partner` |

## Funktionsumfang

### 1. PDF-Report (A6)

**Was:** Standard-Adress-Report als PDF für Druck auf A6-Etiketten (105mm × 148mm).

**Wie:**
- Template: `partner_address_report.partner_address_template`
- Report Type: `qweb-pdf`
- Binding: `res.partner` (binding_model_id)
- Filename: `'Partner_Address_' + (object.name or '')`

**Layout:**
- Font: `'Courier New', monospace` (serifenlos, gut lesbar)
- Font Size: `12px` für Haupttext
- Unternehmen-Adresse oben (ganz klein)
- Trennlinie: `2px solid #222`, `width: 60%`, linksbündig
- Partner-Adresse unten (groß, `font-size: 18px`)
- Einzeiliger Aufbau mit `<br/>`

**Adress-Format:**

**Unternehmen (oben):**
Unternehmensname | Straße | ZIP Stadt

**Partner (unten):**
Partner Name
Straße
ZIP Stadt, Land


### 2. ZPL-Report (A6)

**Was:** Zellettikette im **ZPL-Format** (Zebra Programming Language) für Barcode/Etiketten-Drucker.

**Wie:**
- Template: `partner_address_report.zpl_partner_address_template`
- Report Type: `qweb-text`
- Binding: `res.partner`
- Filename: `'Partner_Address_' + (object.name or '')`

**Layout:**
- Font Size: `30` für Unternehmen, `60` für Partner
- Position: `FO820,150` (rechtsbündig für Unternehmen)
- Vertical Line: `GB3,1500,6` (3px breit, 1500px hoch, 6px dick)
- Line Spacing: `60` (für dynamische Position)
- X-Position: Start `600`, dekrementiert um `line_spacing`

**ZPL-Befehle:**
- `^XA`: Start Etikette
- `^XZ`: Ende Etikette
- `^CI28`: UTF-8 Encoding
- `^FWR`: Right-to-Left Writing
- `^POB`: Print Orientation Bottom
- `^FX`:注释 (Comment)
- `^CF`: Font Size
- `^FO`: Position (X, Y)
- `^FD`: Field Data
- `^FS`: Field Separator

**Adress-Format:**

**Unternehmen (oben rechts):**
Unternehmensname | Straße | ZIP Stadt

**Partner (unten links, dynamisch):**
Parent Name (falls Kontaktperson)
Partner Name
Straße
Straße2 (optional)
ZIP Stadt
Land


### Dynamic Positioning (ZPL)

**Was:** X-Position wird dynamisch für jede Zeile dekrementiert.

**Wie:**
```xml
<t t-set="x_pos" t-value="600"/>
<t t-set="line_spacing" t-value="60"/>

<!-- Parent Name -->
^FO<t t-esc="x_pos"/>,150^FD<t t-esc="doc.parent_id.name"/>^FS
<t t-set="x_pos" t-value="x_pos - line_spacing"/>

<!-- Partner Name -->
^FO<t t-esc="x_pos"/>,150^FD<t t-esc="doc.name"/>^FS
<t t-set="x_pos" t-value="x_pos - line_spacing"/>
```

**Berechnung:**
- Start: `x_pos = 600`
- Jede Zeile: `x_pos = x_pos - 60`
- Ergebnis: 600, 540, 480, 420, 360 (5 Zeilen)

### String Splitting Utility

**Was:** `split_by_limit(text, limit)` zerlegt langen Text in Wortblöcke, begrenzt auf maximale Länge.

**Wie:**
```python
def split_by_limit(self, text, limit):
    if not text:
        return []
    
    words = str(text).split()
    result = []
    current = ""

    for w in words:
        if len(current) + len(w) + (1 if current else 0) <= limit:
            current += (" " if current else "") + w
        else:
            result.append(current)
            current = w

    if current:
        result.append(current)

    return result
```

**Features:**
- `None`/`False`-Check für leere Straßen
- `str(text)` für Type-Safety
- Word-Tokenizer (split nach Leerzeichen)
- Maximal-Limit per Wort
- Leerzeichen zwischen Wörtern (+1)

**Verwendung:** Wird für Straßen-Zeichenumbruch in Reports benutzt (optional, noch nicht im Template)

## Enthaltene Reports

### `report/partner_report_action.xml`

**Reports:**

1. **`action_report_partner_address`**
   - Name: `Partner Address Report (A6)`
   - Model: `res.partner`
   - Binding: `binding_model_id="base.model_res_partner"`
   - Type: `report` (binding_type)
   - Report Type: `qweb-pdf`
   - Report Name: `partner_address_report.partner_address_template`
   - Report File: `partner_address_report.partner_address_template`
   - Print Name: `'Partner_Address_' + (object.name or '')`

2. **`action_zpl_report_partner_address`**
   - Name: `Partner Address Report ZPL (A6)`
   - Model: `res.partner`
   - Binding: `binding_model_id="base.model_res_partner"`
   - Type: `report` (binding_type)
   - Report Type: `qweb-text`
   - Report Name: `partner_address_report.zpl_partner_address_template`
   - Report File: `partner_address_report.zpl_partner_address_template`
   - Print Name: `'Partner_Address_' + (object.name or '')`

**Paper Format:**
- `paperformat_id` ist kommentiert (optional für A6)
- Kann aktiviert werden: `<field name="paperformat_id" ref="partner_address_report.paperformat_din_a6"/>`

## Templates

### `report/partner_report_template.xml`

**Template:** `partner_address_template`

**Layout:**
```xml
<t t-foreach="docs" t-as="doc">
    <t t-call="web.basic_layout">
        <t t-set="company" t-value="doc.company_id or user.company_id"/>

        <div class="page">
            <main style="font-family: 'Courier New', monospace; font-size: 12px;">
                <!-- Unternehmen Adresse -->
                <div>
                    <t t-esc="company.name"/> |
                    <t t-if="company.street"> <t t-esc="company.street"/></t> |
                    <t t-if="company.city">
                        <t t-if="company.zip"> <t t-esc="company.zip"/></t>
                        <t t-esc="company.city"/>
                    </t>
                </div>
                
                <!-- Trennlinie -->
                <hr style="border-top: 2px solid #222; width: 60%; margin-left: 0; text-align: left;"/>

                <!--_partner Adresse -->
                <div style="margin-top: 20px;font-size: 18px;">
                    <t t-esc="doc.name"/><br/>
                    <t t-if="doc.street"><t t-esc="doc.street"/></t><br/>
                    <t t-if="doc.zip"><t t-esc="doc.zip"/></t>
                    <t t-if="doc.city">
                        <t t-esc="doc.city"/>
                        <t t-if="doc.country_id">, <t t-esc="doc.country_id.name"/></t>
                    </t>
                </div>
            </main>
        </div>
    </t>
</t>
```

**Features:**
- `t-call="web.basic_layout"`: Odoo Standard-Layout
- `t-set="company"`: Unternehmen aus `company_id` oder `user.company_id`
- `t-if`: Bedingte Anzeige (Straße, ZIP, Stadt, Land)
- `t-esc`: Escaped Output (Sicherheit)

### `report/zpl_partner_report_template.xml`

**Template:** `zpl_partner_address_template`

**ZPL-Code:**
```xml
<t t-translation="off">
^XA
^CI28
^FWR
^POB

^FX Top section with company address.
^CF0,30
^FO820,150^FD<t t-esc="doc.company_id.name or user.company_id.name"/>
<t t-if="doc.company_id.street or user.company_id.street"> | <t t-esc="doc.company_id.street or user.company_id.street"/></t>
<t t-if="doc.company_id.zip or user.company_id.zip"> | <t t-esc="doc.company_id.zip or user.company_id.zip"/></t> 
<t t-if="doc.company_id.city or user.company_id.city"><t t-esc="doc.company_id.city or user.company_id.city"/></t>^FS

^FO770,150^GB3,1500,6^FS

^FX Second section with client address.
^CF,60

<!-- Dynamic X-Position -->
<t t-set="x_pos" t-value="600"/>
<t t-set="line_spacing" t-value="60"/>

<!-- 1. Parent Name (falls Kontaktperson) -->
<t t-if="doc.company_type == 'person' and doc.parent_id">
    ^FO<t t-esc="x_pos"/>,150^FD<t t-esc="doc.parent_id.name"/>^FS
    <t t-set="x_pos" t-value="x_pos - line_spacing"/>
</t>

<!-- 2. Partner Name -->
^FO<t t-esc="x_pos"/>,150^FD<t t-esc="doc.name"/>^FS
<t t-set="x_pos" t-value="x_pos - line_spacing"/>

<!-- 3. Straße -->
<t t-if="doc.street">
    ^FO<t t-esc="x_pos"/>,150^FD<t t-esc="doc.street"/>^FS
    <t t-set="x_pos" t-value="x_pos - line_spacing"/>
</t>

<!-- 4. Straße2 (optional) -->
<t t-if="doc.street2">
    ^FO<t t-esc="x_pos"/>,150^FD<t t-esc="doc.street2"/>^FS
    <t t-set="x_pos" t-value="x_pos - line_spacing"/>
</t>

<!-- 5. ZIP Stadt -->
<t t-set="city_string" t-value="(doc.zip + ' ' if doc.zip else '') + (doc.city if doc.city else '')"/>
<t t-if="city_string.strip()">
    ^FO<t t-esc="x_pos"/>,150^FD<t t-esc="city_string"/>^FS
    <t t-set="x_pos" t-value="x_pos - line_spacing"/>
</t>

<!-- 6. Land -->
<t t-if="doc.country_id">
    ^FO<t t-esc="x_pos"/>,150^FD<t t-esc="doc.country_id.name"/>^FS
</t>

^XZ
</t>
```

**Features:**
- `t-translation="off"`: Keine Translation für ZPL-Befehle
- `t-set`/`t-value`: Dynamische Variablen (x_pos, line_spacing, city_string)
- `t-if`: Bedingte Anzeige (Parent, Straße, Straße2, ZIP, Stadt, Land)
- `t-esc`: Escaped Output

## Models

### `res.partner`

**Inherit:** `res.partner`

**Method:**

#### `split_by_limit(text, limit)`

**Was:** Zerlegt langen Text in Wortblöcke, begrenzt auf maximale Länge.

**Args:**
- `text`: Der zu zerlegende Text (Straße, Name, etc.)
- `limit`: Maximale Länge per Block

**Returns:** Liste von Text-Blöcken (maximal keine Limit, aber flexibel)

**Beispiel:**
```python
text = "Musterstraße 123 Beispielstadt"
limit = 20

# Ergebnis:
["Musterstraße 123", "Beispielstadt"]
```

**Verwendung:** Noch nicht im Template, aber für zukünftige Zeichenumbruch-Funktionalität verfügbar

## Berichte ausführen

### PDF-Report drucken

1. **Partner öffnen** (Kunde/Kontaktperson)
2. **Aktions-Menü** klicken (oben rechts)
3. **"Partner Address Report (A6)"** wählen
4. **PDF generiert** und im Browser geöffnet
5. **Auf A6-Etikett** drucken

### ZPL-Report drucken

1. **Partner öffnen** (Kunde/Kontaktperson)
2. **Aktions-Menü** klicken
3. **"Partner Address Report ZPL (A6)"** wählen
4. **ZPL-Text generiert** und im Browser geöffnet
5. **ZPL an Etiketten-Drucker** senden (z.B. via `curl` oder Python)

**ZPL senden Beispiele:**

** CURL:**
```bash
curl -X POST -H "Content-Type: application/zpl" \
  --data-binary @report.zpl \
  http://printer-ip/print
```

**Python:**
```python
import requests

with open('report.zpl', 'r') as f:
    zpl_data = f.read()

response = requests.post(
    'http://printer-ip/print',
    data=zpl_data,
    headers={'Content-Type': 'application/zpl'}
)
```

## Odoo 19 Kompatibilität

### Report Binding

- `binding_model_id="base.model_res_partner"`: Korrekte Model-Referenz
- `binding_type="report"`: Korrekte Binding-Type
- `report_type="qweb-pdf"` / `"qweb-text"`: Odoo 19 Report-Typen

### Template Syntax

- `t-call="web.basic_layout"`: Odoo 19 Layout-Call
- `t-set`/`t-value`: Odoo 19 Variablen
- `t-if`/`t-esc`: Standard Odoo 19 Template

### ZPL Encoding

- `^CI28`: UTF-8 Encoding (Odoo 19 Standard)
- `t-translation="off"`: Keine Translation für ZPL-Befehle

## Installation

1. Modul in den Addons-Pfad von Odoo legen
2. App-Liste aktualisieren
3. Modul installieren
4. Partner-Form neu laden (F5)

## Workflow

### A6-Etikette drucken

1. **Partner auswählen** (Kunde/Kontaktperson)
2. **"Partner Address Report (A6)"** drucken
3. **PDF auf A6-Etikett** drucken
4. **etikett an Paket** kleben

### ZPL-Etikette drucken

1. **Partner auswählen**
2. **"Partner Address Report ZPL (A6)"** drucken
3. **ZPL-Text kopieren**
4. **ZPL an Etiketten-Drucker** senden
5. **Etikette aus Drucker** nehmen
6. **etikett an Paket** kleben

## Hinweise

- **A6 Format:** 105mm × 148mm (Standard-Etiketten-Format)
- **Courier New:** Monospace Font für gleichmäßige Zeilen
- **Trennlinie:** 2px dick, 60% breit, linksbündig
- **ZPL UTF-8:** `^CI28` für deutsche Zeichen (ä, ö, ü, ß)
- **Dynamic Position:** X-Position dekrementiert um 60 per Zeile
- **Parent Name:** Nur wenn `company_type == 'person'` und `parent_id` vorhanden
- **Filename:** `'Partner_Address_' + name` für automatische Benennung
- **Company Address:** `doc.company_id` oder `user.company_id` (Fallback)

## ZPL-Befehle

| Befehl | Beschreibung |
|---|---|
| `^XA` | Start Etikette |
| `^XZ` | Ende Etikette |
| `^CI28` | UTF-8 Encoding |
| `^FWR` | Right-to-Left Writing |
| `^POB` | Print Orientation Bottom |
| `^FX` | Comment (Annotation) |
| `^CF0,30` | Font Size 30 (Unternehmen) |
| `^CF,60` | Font Size 60 (Partner) |
| `^FO820,150` | Position X=820, Y=150 |
| `^FD` | Field Data (Text) |
| `^FS` | Field Separator |
| `^GB3,1500,6` | Graphic Box (Line) 3px×1500px×6px |

## Fehlerbehandlung

### Unternehmen nicht vorhanden

- `doc.company_id or user.company_id`: Fallback auf User-Company
- Wenn keine Company: `user.company_id` benutzt

### Straßen nicht vorhanden

- `t-if="doc.street"`: Bedingte Anzeige
- `split_by_limit()`: None/False-Check für leere Straßen

### ZPL nicht lesbar

- `t-translation="off"`: Keine Translation
- UTF-8 mit `^CI28`
- Plott"ZPL-Viewer" für Testing
