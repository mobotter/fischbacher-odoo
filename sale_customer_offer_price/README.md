# Sale Customer Offer Price

![Odoo 19.0](https://img.shields.io/badge/Odoo-19.0-875A7B.svg)
![LGPL-3](https://img.shields.io/badge/license-LGPL--3-blue.svg)

Dieses Odoo-19-Modul erweitert Angebote um eine Preisprüfung für bestehende,
noch offene Kundenangebote. Hat ein Artikel für denselben Kunden in einem
anderen gültigen, laufenden Angebot einen günstigeren effektiven Preis, kann
dieser über einen Assistenten kontrolliert als Festpreis in die aktuelle
Angebotsposition übernommen werden.

Ein Festpreis ist nicht rabattierbar und bleibt bei Mengenänderungen sowie bei
„Preise aktualisieren“ unverändert. Die Funktion ist ausdrücklich auf Angebote
beschränkt; bestätigte Verkaufsaufträge, Rechnungen, POS-Vorgänge und andere
Prozesse werden nicht beeinflusst.

## Funktionen

- Sucht gültige, offene Angebotspositionen desselben kommerziellen Kunden in
  anderen Angeboten.
- Berücksichtigt nur Angebote mit Status `draft` (Entwurf) oder `sent`
  (Gesendet), die nicht gesperrt (`locked`) sind.
- Berücksichtigt nur noch gültige Angebote; `validity_date` darf nicht in der
  Vergangenheit liegen (Tagesdatum in der Zeitzone des Benutzers).
- Vergleicht nur Positionen desselben Produkts, derselben Mengeneinheit,
  derselben Gesellschaft und derselben Währung.
- Ermittelt den niedrigsten effektiven Einzelpreis einschließlich eines
  eventuell vorhandenen Positionsrabatts der Quellposition.
- Rundet und vergleicht Preise auf die Genauigkeit „Product Price“.
- Zeigt in der Angebotsposition den Button **Preis prüfen**, sobald ein
  günstigerer Preis existiert.
- Zeigt Quellangebot, Status, Angebotsdatum, Gültigkeit, Menge, Rabatt,
  Zeilensumme und Ersparnis pro Einheit im Wizard an.
- Validiert Quelle und Ziel beim Klick auf **Festpreis übernehmen** erneut auf
  dem Server.
- Übernimmt den Preis als Festpreis mit `discount = 0.0` und speichert die
  Quellposition in `price_source_line_id`.
- Schützt Festpreise serverseitig gegen Rabatte (UI, Import, RPC,
  Server-Aktionen).
- Führt manuelle Preisänderungen als manuellen Festpreis.

## Begriffe und Preisregeln

### Effektiver Quellpreis

```
Effektiver Quellpreis = price_unit × (1 − discount / 100)
```

| Position              | price_unit | Rabatt | Effektiver Einzelpreis |
|-----------------------|-----------:|-------:|-----------------------:|
| Gültiges Quellangebot | 100,00 EUR |  20 %  |              80,00 EUR |
| Aktuelles Angebot     |  90,00 EUR |   0 %  |              90,00 EUR |

Der Wizard bietet in diesem Beispiel 80,00 EUR als günstigeren Kundenpreis an.
Bei einer Festpreisposition ist der effektive Preis `fixed_price_value`.

### Festpreis in der Zielposition

Nach der Übernahme wird geschrieben:

```python
{
    "price_unit": source_effective_price,
    "discount": 0.0,
    "fixed_price": True,
    "fixed_price_value": source_effective_price,
    "price_source": "wizard",
    "price_source_line_id": source_line.id,
}
```

Regeln für Festpreise in offenen, gültigen Angeboten:

- `price_unit` ist der vereinbarte Netto-Einzelpreis, `discount` ist immer `0.0`.
- Ein Rabatt ungleich 0 wird mit einer Fehlermeldung abgelehnt.
- Mengenänderungen berechnen den Preis nicht über die Preisliste neu.
- „Preise aktualisieren“ lässt Festpreispositionen unverändert.
- Eine manuelle Preisänderung macht aus `wizard` einen `manual`-Festpreis und
  löscht die Herkunftsreferenz.
- Ein Produkt- oder Mengeneinheitswechsel hebt den Festpreis auf
  (`price_source = auto`); der Preis wird wieder aus der Preisliste bestimmt.
- Festpreise bleiben vergleichsrelevant und können Quelle für weitere Angebote
  desselben Kunden sein.

Ein Festpreis von 80,00 EUR darf deshalb nicht zusätzlich mit 10 % rabattiert
werden – das würde den vereinbarten Preis unbemerkt auf 72,00 EUR senken.

## Geltungsbereich

Eine Ziel- oder Quellposition ist nur im Geltungsbereich, wenn:

- ihr Auftrag im Status `draft` oder `sent` steht und nicht gesperrt ist,
- das Angebot noch gültig ist (`validity_date` leer oder ≥ heute),
- die Position eine normale Produktposition und kein Abschnitt/Hinweis ist,
- Produkt, Mengeneinheit, Gesellschaft und Währung übereinstimmen,
- Quell- und Zielposition aus unterschiedlichen Angeboten stammen.

Hinweis: In Odoo 19 gibt es den Status `done` nicht mehr; gesperrte Aufträge
werden über das Feld `locked` gekennzeichnet.

## Technische Umsetzung

### Felder auf `sale.order.line`

| Feld                             | Typ              | Gespeichert | Zweck                                   |
|----------------------------------|------------------|:-----------:|-----------------------------------------|
| `price_source`                   | Selection        | ja          | `auto`, `wizard`, `manual`              |
| `fixed_price`                    | Boolean          | ja          | Position hat einen Festpreis            |
| `fixed_price_value`              | Float (Product Price) | ja     | gespeicherter Festpreis                 |
| `price_source_line_id`           | Many2one         | ja          | Herkunft eines Wizard-Festpreises       |
| `has_cheaper_customer_offer`     | Boolean          | nein        | steuert den Button „Preis prüfen“       |
| `cheaper_customer_price`         | Monetary         | nein        | günstigster gefundener Preis            |
| `cheaper_customer_offer_line_id` | Many2one         | nein        | günstigste gefundene Quellposition      |

Die drei Anzeige-Felder sind nicht gespeicherte Compute-Felder. Dadurch ist der
Button auch nach dem Speichern und Neuladen korrekt sichtbar.

### Erweiterungsstellen

| Methode                                   | Zweck                                                             |
|-------------------------------------------|-------------------------------------------------------------------|
| `sale.order.line._compute_price_unit`     | Festpreispositionen werden übersprungen                           |
| `sale.order.line._compute_discount`       | Festpreispositionen behalten 0 % Rabatt (auch bei Preislisten-Rabatt) |
| `sale.order._get_update_prices_lines`     | „Preise aktualisieren“ ignoriert Festpreise                       |
| `sale.order.line.write`                   | Rabattsperre, manueller Festpreis, Reset bei Produkt-/UoM-Wechsel |
| `sale.order.line.create`                  | Normalisiert explizit übergebene Festpreise                       |
| `_onchange_mark_manual_price`             | Kennzeichnet manuelle Preiseingaben im Formular                   |
| `_onchange_reset_fixed_price_on_product_or_uom` | Hebt den Festpreis bei Produkt-/UoM-Wechsel im Formular auf |

Manuelle Preise werden wie im Odoo-19-Standard über
`technical_price_unit != price_unit` erkannt. Das ist nötig, weil Odoo
Onchanges rekursiv auch für berechnete Änderungen auslöst – ein von der
Preisliste gesetzter Preis darf nicht als manueller Festpreis markiert werden.

### View-Hinweise

Die Festpreisfelder sind `readonly`. Damit ihre Onchange-Werte beim Speichern
an den Server übertragen werden, sind sie in Liste **und** Positionsformular
mit `force_save="1"` eingebunden. Das Rabattfeld ist bei `fixed_price`
zusätzlich im UI gesperrt; die maßgebliche Prüfung erfolgt serverseitig.

### Context-Schalter

`customer_offer_price_internal_write` wird ausschließlich vom Wizard für den
einen Übernahme-Schreibvorgang gesetzt. Er umgeht nur die Festpreisprüfung in
`write()` dieses Moduls, keine andere Logik.

## Modulstruktur

```text
sale_customer_offer_price/
├── __init__.py
├── __manifest__.py
├── README.md
├── README.rst
├── models/
│   ├── __init__.py
│   ├── sale_order.py
│   └── sale_order_line.py
├── security/
│   └── ir.model.access.csv
├── views/
│   ├── customer_offer_price_wizard_views.xml
│   └── sale_order_views.xml
└── wizard/
    ├── __init__.py
    └── customer_offer_price_wizard.py
```

## Zugriffsrechte

Der Wizard `customer.offer.price.wizard` ist für die Gruppe
`sales_team.group_sale_salesman` (Verkauf / Benutzer: nur eigene Belege)
freigegeben.

Die Suche nach Quellangeboten läuft mit den Rechten des Benutzers. Benutzer mit
„Nur eigene Belege“ sehen daher nur Preise aus Angeboten, die sie auch sonst
lesen dürfen.

## Installation

1. Das Verzeichnis `sale_customer_offer_price` in einen Addons-Pfad kopieren
   (bzw. im Odoo.sh-Repository committen).
2. Odoo neu starten und im Entwicklermodus **Apps → Apps-Liste aktualisieren**.
3. Nach „Sale Customer Offer Price“ suchen und installieren bzw. aktualisieren:

   ```bash
   odoo -d <datenbank> -u sale_customer_offer_price --stop-after-init
   ```

## Bedienung

1. Ein Angebot im Status Entwurf oder Gesendet öffnen.
2. Kunde und Produktposition erfassen.
3. Existiert für denselben kommerziellen Kunden ein anderes gültiges, offenes
   Angebot mit demselben Produkt, derselben Einheit und günstigerem
   effektivem Preis, erscheint in der Position der Button **Preis prüfen**.
4. Button klicken, Quellangebot, Gültigkeit, Preis, Rabatt und Ersparnis prüfen.
5. **Festpreis übernehmen** klicken.

## Testfälle

- Keine passende Quellposition vorhanden.
- Gültige Quellposition im Status `draft` bzw. `sent`.
- Quellangebot mit leerem, heutigem und abgelaufenem `validity_date`.
- Gültigkeitsgrenze kurz nach Mitternacht (Zeitzone Europe/Berlin).
- Quellposition mit Rabatt; Zielposition mit Rabatt.
- Übernahme als Festpreis mit `discount = 0.0`.
- Rabatt auf Festpreis setzen (UI und RPC) → Fehlermeldung.
- Mengenänderung einer Festpreisposition → Preis bleibt.
- Preisliste mit Mengenstaffel/Rabattregel → Festpreis bleibt, Rabatt 0 %.
- „Preise aktualisieren“ → Festpreise bleiben unverändert.
- Manuelle Preisänderung auf Wizard-Festpreis → `manual`, Herkunft gelöscht.
- Produkt- oder Einheitswechsel auf Festpreisposition → Festpreis aufgehoben.
- Mengenänderung einer normalen Position → wird nicht als manuell markiert.
- Wiederverwendung eines übernommenen Festpreises als Preisquelle.
- Gleicher Kunde über verschiedene Ansprechpartner.
- Andere Gesellschaft, Währung, Produkt oder Mengeneinheit.
- Günstigerer Preis im selben Angebot → wird ignoriert.
- Quellangebot wird nach Öffnen des Wizards bestätigt, storniert oder gesperrt.
- Zielangebot wird nach Öffnen des Wizards bestätigt.
- Preis oder Rabatt der Quelle wird vor der Übernahme geändert.
- Quellposition wird vor der Übernahme gelöscht.
- Abschnitts- und Hinweiszeilen.
- Mehrere gültige Quellangebote mit unterschiedlichen effektiven Preisen.

## Changelog

### 19.0.1.1.0

- Manifest: `website`, `description`, Autor mit Firma ergänzt.
- Vergleich auf gleiche Mengeneinheit und anderes Angebot eingeschränkt.
- Preise auf „Product Price“ gerundet, Vergleiche mit `float_compare`.
- Gültigkeitsdatum in Benutzer-Zeitzone; gesperrte Aufträge ausgeschlossen.
- Festpreisschutz über `_compute_price_unit`, `_compute_discount` und
  `_get_update_prices_lines` statt Onchange-Wiederherstellung.
- Manuelle Preiserkennung über `technical_price_unit` (verhindert falsche
  Markierung bei Mengenänderungen).
- Wizard-Festpreise werden bei manueller Preisänderung zu `manual` statt
  einen Fehler auszulösen; Rabattsperre für alle Festpreise.
- Produkt- oder Einheitswechsel hebt den Festpreis auf.
- Anzeige-Felder für günstigere Preise als nicht gespeicherte Compute-Felder.
- `force_save="1"` für die Festpreisfelder; Rabattsperre auch im
  Positionsformular.
- Wizard: Abbrechen über `special="cancel"`, Einheit wird angezeigt.

## Autor

Moritz Kern
Fischbacher GmbH + Co. KG – <https://fischbacher.de>

## Lizenz

LGPL-3. Copyright (c) 2026 Moritz Kern, Fischbacher GmbH + Co. KG
