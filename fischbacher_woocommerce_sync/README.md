# Fischbacher WooCommerce Preis- und Bestandssync

Autor: Moritz Kern  
Firma: Fischbacher GmbH + Co. KG

## Zweck

Synchronisiert manuell aus dem Odoo-Produktformular:

- Odoo `list_price` als WooCommerce-Nettopreis `regular_price`
- Odoo `qty_available` als WooCommerce-Bestand `stock_quantity`

Produktname, Beschreibung, Bilder, Kategorien und weitere WooCommerce-Felder bleiben unverändert.

## Zuordnung

- Odoo: `default_code`
- WooCommerce: `SKU`

Die SKU muss in WooCommerce genau einmal vorhanden sein.

## Installation

1. Ordner in den Odoo-Addons-Pfad kopieren.
2. Odoo neu starten.
3. Apps-Liste aktualisieren.
4. Modul installieren.
5. Unter Einstellungen > Allgemeine Einstellungen > WooCommerce Sync konfigurieren.
6. Produkt öffnen und auf „Bestand und Preis nach Woo“ klicken.

## Hinweis

Das Modul ist zunächst für einfache WooCommerce-Produkte gedacht, nicht für Variationen.
