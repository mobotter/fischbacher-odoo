# Fischbacher Stock Auto Location

Odoo 19 Custom Module zur automatischen Zielort-Setzung bei Wareneingaengen.

## Beschreibung

Dieses Modul setzt beim Bestaetigen eines Wareneingangs (Vorgangstyp "Eingaenge / Anlieferungen") den Zielort (`location_dest_id`) pro Move automatisch auf den **letzten internen Lagerort mit Bestand** des Produkts.

### Use Case

- Produkte werden eingekauft und per Wareneingang eingebucht.
- Statt alle Produkte in einen festen Ziellagerort (z. B. `Partners/Kunden/Vermietete Geraete/E01`) zu legen, werden sie automatisch dorthin gebucht, wo sie bereits Lagerbestand haben.
- Ideal fuer Mietgeraete, die nach Rueckgabe wieder an ihren bisherigen Ort zurueckkehren sollen.

## Installation

### Voraussetzungen

- Odoo 19.0
- Module `stock` und `purchase_stock` installiert
- Entwicklermodus aktiviert

### Schritte

1. Modul-Ordner `fischbacher_stock_auto_location` in dein Odoo-Addons-Verzeichnis kopieren, z. B.:
   ```bash
   /opt/odoo/addons/fischbacher_stock_auto_location
   ```
2. Odoo neustarten (falls noetig) und im Backend:
   - Entwicklermodus aktivieren.
   - `Apps → Apps-Liste aktualisieren` klicken.
   - Modul "Fischbacher Stock Auto Location" suchen und installieren.

## Konfiguration

Das Modul benoetigt keine zusaetzliche Konfiguration. Es greift automatisch bei allen Wareneingaengen vom Vorgangstyp "Eingaenge / Anlieferungen" (in deinem System ID 1).

Falls du den Vorgangstyp explizit anpassen moechtest, Aendere in `models/stock_picking.py` die Zeile:

```python
if picking.picking_type_id.id != 1:
    continue
```

Passe die ID `1` an die ID deines tatsaechlichen Vorgangstyps an (zu finden unter `Lager → Konfiguration → Vorgangstypen`).

## Funktionsweise

Beim Bestaetigen eines Wareneingangs (`action_confirm` auf `stock.picking`):

1. Das Modul filtert alle Incoming-Pickings (`picking_type_code == 'incoming'`).
2. Fuer jeden Vorgangstyp "Eingaenge / Anlieferungen" (ID 1) wird folgende Logik ausgefuehrt:
   - Fuer jede `stock.move` im Transfer:
     - Suche in `stock.quant` den letzten internen Lagerort mit Bestand > 0 fuer das Produkt.
     - Setze `move.location_dest_id` auf diesen Lagerort.
   - Falls kein Bestand existiert, bleibt der Standard-Zielort des Vorgangstyps erhalten.

### Beispiel-Logik (Auszug)

```python
quant = StockQuant.search(
    [
        ("product_id", "=", product.id),
        ("location_id.usage", "=", "internal"),
        ("quantity", ">", 0),
    ],
    order="id desc",
    limit=1,
)
if quant and quant.location_id:
    move.location_dest_id = quant.location_id
```

## Anpassungen

### 1. Anderer Vorgangstyp

Wenn du die Logik auf einen anderen Vorgangstyp anwenden moechtest, Aendere die ID in `models/stock_picking.py`:

```python
if picking.picking_type_id.id != 1:  # Hier ID anpassen
    continue
```

### 2. Lagerort mit groesstem Bestand statt letztem Eintrag

Standardmaessig wird der Lagerort mit dem hoechsten `id` (letzter Eintrag) genommen. Wenn du stattdessen den Lagerort mit dem **groessten Bestand** nehmen moechtest, Aendere:

```python
order="id desc"
```

zu:

```python
order="quantity desc"
```

### 3. Nur fuer bestimmte Produktkategorien

Falls die Logik nur fuer bestimmte Produktkategorien gelten soll, ergaenze eine Pruefung:

```python
if move.product_id.categ_id.id not in [KATEGORIE_ID_1, KATEGORIE_ID_2]:
    continue
```

### 4. Fallback-Verhalten anpassen

Aktuell bleibt bei Produkten ohne Bestand der Standard-Zielort des Vorgangstyps erhalten. Wenn du stattdessen einen festen Fallback-Lagerort nutzen moechtest, ergaenze:

```python
else:
    move.location_dest_id = self.env.ref("stock.stock_location_stock").id  # Beispiel: WH/Stock
```

## Testing

1. Erstelle eine neue Bestellung mit Produkten, die bereits Bestand haben.
2. Bestaetige die Bestellung und Oeffne den Wareneingang (`Eingaenge / Anlieferungen`).
3. Pruefe in den Move-Lines, ob `location_dest_id` auf den erwarteten Lagerort gesetzt wurde.

## Known Issues / Einschraenkungen

- Die Logik basiert auf `stock.quant` mit `quantity > 0`. Wenn ein Produkt Ueberall 0 Bestand hat, wird der Standard-Zielort verwendet.
- Bei Produkten mit mehreren Lagerorten mit Bestand wird der "letzte" Eintrag (nach `id`) genommen. Das ist nicht zwingend der "logisch beste" Ort, sondern der zuletzt beschriebene.

## Lizenz

LGPL-3

## Autor

Fischbacher GmbH & Co. KG

## Support

Bei Fragen oder Anpassungswuenschen bitte internes Ticket an das ERP-Team erstellen.
