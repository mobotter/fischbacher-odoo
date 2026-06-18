# Sale Partner Ref Display

## Übersicht

Zeigt die Kundenreferenz (`partner.ref`) direkt in den Verkaufsbeleg-Ansichten von Odoo an.

## Funktionsumfang

- Erweitert die Standard-Sale-Order-Ansichten um die Anzeige der Kundenreferenz.
- Das Feld `partner_id.ref` wird im Tree- und/oder Kanban-View des Verkaufsbelegs sichtbar.
- Damit ist die Referenz des Kunden direkt in der Bestell-Übersicht lesbar, ohne die Partner-Form öffnen zu müssen.

## Typischer Einsatz

- Schnellere Zuordnung von Bestellungen zu Kundenreferenzen.
- Übersichtlichere Listenansichten im Verkauf.
- Vermeidung von Doppelarbeit beim manuellen Nachschauen der Kundenreferenz.

## Technische Details

- Technischer Name: `sale_partner_ref_display`
- Erweitert wahrscheinlich: `sale.order` Model und/oder `sale.order.tree` View
- Zeigt Feld: `partner_id.ref` (Kundenreferenz) in Sale Order Views

## Installation

1. Modul in den Addons-Pfad von Odoo legen.
2. App-Liste aktualisieren.
3. Modul installieren oder bei Änderungen upgraden.

## Hinweise

Die konkrete Erweiterung erfolgt typischerweise über ein related field auf `partner_id.ref` in `sale.order` und eine Anpassung der Tree/Kanban-View. Bei Änderungen im Sale-Modul sollten View-IDs und Referenzen geprüft werden.
