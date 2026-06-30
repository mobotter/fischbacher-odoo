# Product Variant Default Code Unique

Dieses Modul erzwingt die Eindeutigkeit von `default_code` auf dem Modell `product.product`, also auf Variantenebene.

## Verhalten

- Leere `default_code`-Werte bleiben erlaubt.
- Nicht-leere doppelte Varianten-Codes werden beim Speichern blockiert.
- Bei einem Konflikt wird ein `ValidationError` ausgelöst.

## Einsatzfall

Das Modul ist sinnvoll, wenn jede Produktvariante eine eigene eindeutige interne Referenz bzw. SKU haben soll. Odoo erzwingt diese Eindeutigkeit standardmäßig nicht zuverlässig selbst, deshalb ist eine zusätzliche Constraint sinnvoll.

## Technische Umsetzung

Das Modul erweitert `product.product` und prüft per `@api.constrains("default_code")`, ob bereits eine andere Variante mit demselben `default_code` existiert. Wird ein Duplikat gefunden, wird das Speichern mit einer Validierungsfehlermeldung abgebrochen.

## Installation

1. Den Modulordner in einen Addons-Pfad von Odoo kopieren.
2. Die App-Liste in Odoo aktualisieren.
3. Das Modul installieren.

## Hinweis vor produktivem Einsatz

Wenn bereits doppelte Varianten-Codes in der Datenbank vorhanden sind, müssen diese zuerst bereinigt werden, bevor die Regel in laufenden Prozessen sauber greift. Das gilt besonders bei bestehenden Importen, Massenänderungen oder Fremdsystem-Synchronisationen.
