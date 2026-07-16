# Prefix Search Views

Dieses Modul ändert ausgewählte Odoo-Search-Views so, dass die Suche auf
**beginnt mit** statt auf **enthält** basiert.

## Was das Modul macht

- Kontakte-Suche auf Präfixsuche umstellen.
- Produkt-Suche auf Präfixsuche umstellen.
- Nur Search Views, keine Many2one-Autocomplete.

## Installation

1. Modul in deinen Custom Addons Ordner legen.
2. Apps-Liste in Odoo aktualisieren.
3. Modul **Prefix Search Views** installieren.

## Konfiguration

Es ist keine zusätzliche Konfiguration nötig.

## Technischer Hinweis

Das Modul erweitert die Suchansichten per XML-Inheritance und verwendet
`filter_domain` mit `=ilike` und einem `%` am Ende.

## Verwendete Bereiche

- Contacts
- Produkte
- Produktbezogene Ansichten in angebundenen Modulen
