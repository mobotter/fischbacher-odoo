# List View Default

Odoo-19-Modul von **Moritz Kern**, das ausgewählte Odoo-Fensteraktionen standardmäßig in der Listenansicht öffnet.

Die Listenansicht wird bevorzugt geöffnet. Kanban- und Formularansichten bleiben verfügbar, sofern sie für die jeweilige Aktion eingerichtet sind.

## Funktionen

Das Modul ist für häufig verwendete Übersichten vorgesehen, unter anderem:

- Produkte.
- Produktvarianten.
- Kunden.
- Lagerprodukte.
- Lager- und Bestandsübersichten.
- Mietprodukte.
- Abonnementprodukte.
- ähnliche Produkt- und Partnerübersichten.

Die aktuelle Manifest-Konfiguration lädt nur:

```text
data/product_actions.xml
data/partner_actions.xml
```

Lager-, Rental- und Subscription-Aktionen sind nicht automatisch enthalten, weil ihre Fensteraktions-XML-IDs je nach Odoo-Edition, installierten Apps und Datenbank variieren können.

## Unterstützte Version

- Odoo 19.0.

## Manifest

Das Modul verwendet aktuell folgendes Manifest:

```python
# -*- coding: utf-8 -*-

{
    "name": "List View Default",
    "version": "19.0.1.0.0",
    "category": "Tools",
    "summary": "Opens selected Odoo actions in list view by default",
    "description": """
List View Default
=================

Makes list views the default view for commonly used Odoo actions, including:

- Products
- Product variants
- Customers
- Stock products
- Stock product variants
- Rental products
- Subscription products
- Similar product and partner overviews

Kanban and form views remain available where supported.
    """,
    "author": "Moritz Kern",
    "license": "LGPL-3",
    "depends": [
        "product",
        "stock",
        "sale_management",
    ],
    "data": [
        "data/product_actions.xml",
        "data/partner_actions.xml",
    ],
    "installable": True,
    "application": False,
}
```

## Modulstruktur

```text
list_view_default/
├── __init__.py
├── __manifest__.py
└── data/
    ├── product_actions.xml
    └── partner_actions.xml
```

## Abhängigkeiten

Das Manifest setzt folgende Odoo-Module voraus:

```python
"depends": [
    "product",
    "stock",
    "sale_management",
],
```

### `product`

Wird für Produktvorlagen und Produktvarianten benötigt.

### `stock`

Wird für Lager- und Bestandsfunktionen benötigt.

### `sale_management`

Wird für Verkaufs- und produktbezogene Verkaufsfunktionen benötigt.

Rental und Subscriptions sind aktuell keine direkten Abhängigkeiten des Manifests. Wenn diese Funktionen erweitert werden sollen, müssen die entsprechenden Apps zunächst in der konkreten Odoo-19-Installation geprüft werden.

## Technischer Ansatz

Das Modul ändert die Reihenfolge der Ansichtstypen im Feld `view_mode` einer bestehenden Fensteraktion.

Beispiel:

```text
kanban,list,form
```

wird zu:

```text
list,kanban,form
```

Dadurch öffnet Odoo zuerst die Listenansicht. Kanban und Formular bleiben über die Ansichtsschalter erreichbar.

## Wichtiger XML-Hinweis

`ir.actions.act_window` besitzt kein Feld `inherit_id`.

Dieses Muster ist falsch:

```xml
<record id="my_action" model="ir.actions.act_window">
    <field name="inherit_id" ref="product.product_template_action"/>
    <field name="view_mode">list,kanban,form</field>
</record>
```

Für Fensteraktionen muss die vorhandene, vollständig qualifizierte externe XML-ID direkt als Record-ID verwendet werden:

```xml
<record id="product.product_template_action"
        model="ir.actions.act_window">
    <field name="view_mode">list,kanban,form</field>
</record>
```

`inherit_id` wird für geerbte Ansichten des Modells `ir.ui.view` verwendet, nicht für Fensteraktionen.

## Produktaktionen

Beispielinhalt für `data/product_actions.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>

    <!-- Produkte -->
    <record id="product.product_template_action"
            model="ir.actions.act_window">
        <field name="view_mode">list,kanban,form</field>
    </record>

    <!-- Produktvarianten -->
    <record id="product.product_variant_action"
            model="ir.actions.act_window">
        <field name="view_mode">list,kanban,form</field>
    </record>

</odoo>
```

Die XML-IDs sind Beispiele und müssen in der Ziel-Datenbank existieren. Wenn eine ID nicht vorhanden ist, schlägt die Installation mit folgendem Fehler fehl:

```text
Cannot update missing record 'module.external_id'
```

## Kundenaktionen

Beispielinhalt für `data/partner_actions.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>

    <!-- Kunden -->
    <record id="base.action_partner_customer_form"
            model="ir.actions.act_window">
        <field name="view_mode">list,kanban,form</field>
    </record>

</odoo>
```

Auch diese externe XML-ID muss in deiner Datenbank vorhanden sein.

## XML-IDs prüfen

Aktiviere zuerst den Entwicklermodus:

```text
Einstellungen → Entwicklermodus aktivieren
```

Öffne anschließend:

```text
Einstellungen
→ Technisch
→ Benutzeroberfläche
→ Fensteraktionen
```

Suche dort nach:

```text
Produkte
Produktvarianten
Kunden
```

Öffne die verwendete Fensteraktion und notiere die externe XML-ID.

Wichtig ist, dass du die Aktion prüfst, die tatsächlich vom Menü geöffnet wird. Mehrere Menüs können dasselbe Modell verwenden, aber auf unterschiedliche Fensteraktionen zeigen.

## Prüfung per SQL

Wenn du Datenbankzugriff besitzt, kannst du vorhandene Fensteraktions-XML-IDs mit PostgreSQL suchen:

```sql
SELECT
    imd.module,
    imd.name,
    imd.model,
    imd.res_id,
    a.name,
    a.res_model,
    a.view_mode
FROM ir_model_data AS imd
JOIN ir_act_window AS a
  ON imd.model = 'ir.actions.act_window'
 AND imd.res_id = a.id
WHERE imd.model = 'ir.actions.act_window'
  AND a.res_model IN (
      'product.template',
      'product.product',
      'res.partner'
  )
ORDER BY a.res_model, a.name;
```

Die vollständige externe ID setzt sich aus `module.name` zusammen, beispielsweise:

```text
product.product_template_action
```

## Installation

### 1. Modul kopieren

Kopiere das Modul in ein Odoo-Addon-Verzeichnis, zum Beispiel:

```text
/opt/odoo/custom-addons/list_view_default
```

### 2. Addons-Pfad prüfen

Stelle sicher, dass das Verzeichnis in `addons_path` enthalten ist:

```ini
addons_path = /opt/odoo/odoo/addons,/opt/odoo/custom-addons
```

### 3. Apps-Liste aktualisieren

1. Entwicklermodus aktivieren.
2. Apps öffnen.
3. `Apps-Liste aktualisieren` ausführen.
4. Nach `List View Default` suchen.
5. Modul installieren.

### 4. Installation per Kommandozeile

Bei einer selbst verwalteten Odoo-Installation:

```bash
./odoo-bin -d DEINE_DATENBANK -u list_view_default --stop-after-init
```

Oder beispielsweise:

```bash
sudo -u odoo odoo -d DEINE_DATENBANK -u list_view_default --stop-after-init
```

Passe Datenbankname, Odoo-Befehl und Pfade an deine Umgebung an.

## Odoo Online und Odoo.sh

Prüfe, ob deine Umgebung eigene Addons unterstützt.

- Bei Odoo.sh wird das Modul normalerweise über ein Git-Repository und den ausgewählten Branch bereitgestellt.
- Bei einer selbst verwalteten Odoo-Installation wird es in einem Addon-Verzeichnis installiert.
- Bei Odoo Online ohne Custom-Addon-Unterstützung kann dieses Modul nicht installiert werden. Dann muss die Einstellung über Studio oder andere verfügbare Konfigurationsmöglichkeiten erfolgen.

## Rental und Subscriptions

Rental- und Subscription-Aktionen sind installationsabhängig. Sie sind im aktuellen Manifest nicht enthalten.

Bevor du sie ergänzt:

1. Prüfe, ob die Apps installiert sind.
2. Ermittle die tatsächlichen Fensteraktionen.
3. Prüfe deren externe XML-IDs.
4. Ergänze nur bestätigte IDs in neuen XML-Dateien.
5. Ergänze die zugehörigen Module in `depends`.

Beispiel:

```python
"depends": [
    "product",
    "stock",
    "sale_management",
    "sale_renting",
    "sale_subscription",
],
```

Verwende diese Erweiterung nur, wenn die Module in deiner Umgebung vorhanden sind.

## Studio-Kompatibilität

Studio kann nach der Installation weiterhin verwendet werden.

Dieses Modul ist für die Reihenfolge von Ansichtstypen zuständig. Studio kann weiterhin:

- Listenfelder und Spalten anpassen.
- Felder hinzufügen oder entfernen.
- Felder verschieben.
- Filter und Gruppierungen konfigurieren.
- Formular- und Kanban-Ansichten bearbeiten.
- Sichtbarkeitsbedingungen definieren.

Bei Änderungen am exakt gleichen Ansichtselement können Modul- und Studio-Anpassungen miteinander konkurrieren. Für eine klare Wartung empfiehlt sich folgende Aufteilung:

- `list_view_default`: bevorzugte Startansicht.
- Studio: einfache Layout-, Feld- und Filteranpassungen.
- separates Custom-Modul: komplexe, versionskontrollierte Ansichtsänderungen.

## Fehlerbehebung

### `Invalid field 'inherit_id' in 'ir.actions.act_window'`

Ursache: `inherit_id` wurde bei einer Fensteraktion verwendet.

Lösung:

```xml
<record id="product.product_template_action"
        model="ir.actions.act_window">
    <field name="view_mode">list,kanban,form</field>
</record>
```

### `Cannot update missing record`

Ursache: Die verwendete externe XML-ID existiert nicht.

Lösung:

1. Externe XML-ID im Entwicklermodus prüfen.
2. Die XML-ID im Modul korrigieren.
3. Den betreffenden XML-Block vorübergehend entfernen.
4. Nur bestätigte IDs laden.

### Ansicht öffnet weiterhin Kanban

Prüfe:

- Ob `list` am Anfang von `view_mode` steht.
- Ob du die richtige Fensteraktion bearbeitest.
- Ob mehrere Menüs unterschiedliche Aktionen verwenden.
- Ob Studio oder ein anderes Modul eine weitere Aktion verwendet.
- Ob eine gespeicherte Benutzeransicht aktiv ist.
- Ob ein Browser-Neuladen erforderlich ist.

### Keine Listenansicht vorhanden

Prüfe unter:

```text
Einstellungen
→ Technisch
→ Benutzeroberfläche
→ Ansichten
```

ob für das Modell eine Listenansicht existiert.

## Upgrade

Nach Änderungen an den XML-Dateien muss das Modul aktualisiert werden:

```bash
./odoo-bin -d DEINE_DATENBANK -u list_view_default --stop-after-init
```

Anschließend gegebenenfalls den Odoo-Dienst neu starten:

```bash
sudo systemctl restart odoo
```

## Rückgängigmachen

Um eine Änderung zurückzunehmen, entferne den entsprechenden `<record>`-Block und aktualisiere das Modul erneut.

Alternativ kannst du das Feld `view_mode` der Fensteraktion im Entwicklermodus manuell auf den ursprünglichen Wert zurücksetzen.

Vor Änderungen in einer produktiven Datenbank sollte ein Backup erstellt werden.

## Sicherheit und Wartung

Das Modul:

- ändert keine Zugriffsrechte.
- ändert keine Geschäftslogik.
- verändert keine Produkt- oder Lagerdaten.
- ändert ausschließlich `view_mode` der referenzierten Fensteraktionen.

Vor dem produktiven Einsatz:

- Teste das Modul in einer Testdatenbank.
- Prüfe jede externe XML-ID.
- Teste die betroffenen Menüs mit verschiedenen Benutzerrollen.
- Kontrolliere bestehende Studio-Anpassungen.
- Erstelle ein Datenbank-Backup.

## Lizenz

LGPL-3.

## Autor

Moritz Kern.
