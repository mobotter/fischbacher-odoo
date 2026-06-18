# Sale Partner Ref Display

## Übersicht

Zeigt ref - name bei Kunden und default_code - name bei Produkten in Sales/Subs

Das Modul erweitert primär den Verkaufsauftrag (sale.order) und die Produktauswahl in Sales und Subscriptions um eine kontextgesteuerte Anzeige von Referenzen.

## Funktionsumfang

### Kundenanzeige im Verkauf

- Das Feld `partner_id` im Verkaufsauftrag zeigt den Kunden als "ref - name".
- Falls keine `ref` vorhanden ist, wird "id - name" verwendet.
- Die Suche nach Kunden unterstützt sowohl `ref` als auch `name`.
- Bei rein numerischer Eingabe wird zusätzlich nach `id` gesucht.
- Der Kontext-Flag `show_ref_prefix` steuert, ob diese Anzeige aktiviert ist.

### Produktanzeige in Sales und Subscriptions

- Produkte werden in Sales und Subscriptions als "default_code - name" angezeigt.
- Die Produktsuche unterstützt sowohl Suche nach `default_code` als auch nach `name`.
- Quick Create aus der Produktsuche ist blockiert.
- Die Bezeichnung in Verkaufszeilen (`sale.order.line.name`) wird automatisch angepasst.

## Technische Details

| Feld | Wert |
|---|---|
| Technischer Name | `sale_partner_ref_display` |
| Version | `19.0.1.0.0` |
| Kategorie | `Sales` |
| Author | `Moritz Kern` |
| Lizenz | `LGPL-3` |
| Abhängigkeiten | `sale, product, sale_subscription` |

## Enthaltene Modelle

### `res_partner`

Erweitert `display_name` und `name_search` von `res.partner`.

Funktionen:
- Anzeige als "ref - name" (oder "id - name" wenn keine ref)
- Suche nach ref und name im Kunden-Search
- Unterstützung von Search nach ID bei rein numerischer Eingabe
- Kontext-Flag `show_ref_prefix` steuert die Anzeige

### `product_product`

Erweitert `display_name` und `name_search` von `product.product`.

Funktionen:
- Anzeige als "default_code - name"
- Suche nach default_code und name
- Blockiert Quick Create aus der Produktsuche (`forbid_quick_create_product`)

### `product_template`

Erweitert `display_name` und `name_search` von `product.template`.

Funktionen:
- Anzeige als "default_code - name"
- Suche nach default_code und name

### `sale_order_line`

Erweitert `sale.order.line`.

Funktionen:
- Passt die Bezeichnung in Verkaufszeilen an ("default_code - name")
- Übernimmt `_compute_product_id_change` und setzt `name` neu

## Enthaltene Views

### views/sale_order_views.xml

Das Modul definiert folgende Views:

- `view_order_form_partner_ref`: Sale Order Form - Partner mit `show_ref_prefix`
- `view_order_form_product_display`: Sale Order Form - Produkt mit `forbid_quick_create`
- `view_subscription_form_partner_ref`: Subscription Form - Partner mit `show_ref_prefix`
- `view_subscription_form_product_display`: Subscription Form - Produkt mit `forbid_quick_create`

## JavaScript

- `static/src/js/partner_ref_widget.js`: Wird im Backend-Asset `web.assets_backend` eingebunden.

## Installation

1. Modul in den Addons-Pfad von Odoo legen.
2. App-Liste aktualisieren.
3. Modul installieren oder bei Änderungen upgraden.

## Hinweise

- Die Anzeige von "ref - name" bei Kunden ist kontextgesteuert und wird durch `show_ref_prefix=True` aktiviert.
- Quick Create von Produkten aus der Suche ist in Sales und Subscriptions deaktiviert.
- Die Produktbezeichnung in Verkaufszeilen wird automatisch auf "default_code - name" gesetzt.
