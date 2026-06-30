


Profilavatar

wie kann ich in odoo 19 doppelte internal_reference finden
2 Schritte abgeschlossen
Am einfachsten findest du doppelte internal_reference in Odoo 19 über eine SQL-Abfrage auf product_template.default_code, weil das das Standardfeld für die interne Referenz ist. Odoo liefert out of the box keine strikte Duplikat-Prüfung für diese Felder; Duplikate werden daher meist per Suche, SQL oder Automatisierung geprüft bzw. verhindert.

SQL für Duplikate
sql
SELECT default_code, COUNT(*) AS cnt
FROM product_template
WHERE default_code IS NOT NULL
  AND default_code <> ''
GROUP BY default_code
HAVING COUNT(*) > 1
ORDER BY cnt DESC, default_code;
Das zeigt dir jede interne Referenz, die mehr als einmal vorkommt.

Welche Produkte betroffen sind
Wenn du zusätzlich die konkreten Datensätze sehen willst:

sql
SELECT pt.id, pt.name, pt.default_code
FROM product_template pt
WHERE pt.default_code IN (
    SELECT default_code
    FROM product_template
    WHERE default_code IS NOT NULL
      AND default_code <> ''
    GROUP BY default_code
    HAVING COUNT(*) > 1
)
ORDER BY pt.default_code, pt.name;
Damit bekommst du alle betroffenen Produkte je doppelter Referenz in einer Liste.

Im Odoo-UI prüfen
Im Produktbereich kannst du nach Internal Reference filtern, aber die Suche hängt davon ab, ob du auf Template- oder Variantenebene arbeitest; in älteren Odoo-Versionen war das Verhalten hier uneinheitlich dokumentiert. Für eine echte Dublettensuche ist SQL oder eine Server Action daher zuverlässiger.

Dubletten künftig verhindern
Wenn du nicht nur finden, sondern auch verhindern willst, kannst du eine Automated Action auf product.template anlegen, die bei default_code-Änderungen nach einem vorhandenen gleichen Wert sucht und dann einen Fehler wirft. Für sauberere Daten in größeren Setups ist oft auch ein kleines Custom Module sinnvoller als rein manuelle Kontrolle.

Wenn du willst, schreibe ich dir direkt eine Odoo 19 Server Action oder ein SQL-Query für pgAdmin/psql passend zu deinem Setup.

wie mache ich das über das terminal?
2 Schritte abgeschlossen
Ja — über das Terminal ist das am saubersten per psql gegen deine Odoo-Datenbank. Odoo dokumentiert die CLI zwar allgemein, aber für die Dublettensuche selbst ist die Datenbankabfrage der passende Weg.

Direkt in psql
Melde dich zuerst auf dem Server an und öffne dann die Datenbank:

bash
psql -U odoo -d DEINE_DB
Dann diese Abfrage ausführen:

sql
SELECT default_code, COUNT(*) AS cnt
FROM product_template
WHERE default_code IS NOT NULL
  AND default_code <> ''
GROUP BY default_code
HAVING COUNT(*) > 1
ORDER BY cnt DESC, default_code;
Das listet alle doppelten internen Referenzen auf.

Betroffene Produkte anzeigen
Wenn du die konkreten Produkte sehen willst:

sql
SELECT pt.id, pt.name, pt.default_code
FROM product_template pt
WHERE pt.default_code IN (
    SELECT default_code
    FROM product_template
    WHERE default_code IS NOT NULL
      AND default_code <> ''
    GROUP BY default_code
    HAVING COUNT(*) > 1
)
ORDER BY pt.default_code, pt.name;
Damit bekommst du die Produkte direkt im Terminal ausgegeben.

Einzeiler per Shell
Wenn du es ohne interaktive psql-Session machen willst:

bash
psql -U odoo -d DEINE_DB -c "
SELECT default_code, COUNT(*) AS cnt
FROM product_template
WHERE default_code IS NOT NULL
  AND default_code <> ''
GROUP BY default_code
HAVING COUNT(*) > 1
ORDER BY cnt DESC, default_code;
"
Das ist praktisch für schnelle Checks oder Cron-Jobs.

Falls du auf dem Odoo-Server bist
Wenn du nur den Datenbanknamen nicht sicher weißt, kannst du ihn meist in der Odoo-Config oder per CLI-Setup prüfen; Odoo bietet dafür eine Kommandozeilen-Schnittstelle an. Bei mehreren Datenbanken ist es sinnvoll, erst die richtige DB zu identifizieren und dann die Abfrage auszuführen.

Wenn du die Duplikate exportieren willst
Ich kann dir auch einen fertigen Terminal-Befehl geben, der das Ergebnis direkt als CSV speichert, zum Beispiel:

bash
psql -U odoo -d DEINE_DB -c "\copy (
  SELECT default_code, COUNT(*) AS cnt
  FROM product_template
  WHERE default_code IS NOT NULL
    AND default_code <> ''
  GROUP BY default_code
  HAVING COUNT(*) > 1
  ORDER BY cnt DESC, default_code
) TO 'duplikate_internal_reference.csv' CSV HEADER"
Das ist oft die beste Variante, wenn du die Liste anschließend in Excel oder Numbers weiterbearbeiten willst.

wieso konnte sowas passieren? muss die internal_reference nicht eineindeutig sein?
2 Schritte abgeschlossen
Kurz: nein, in Odoo ist internal_reference bzw. default_code standardmäßig nicht eineindeutig erzwungen. Odoo erlaubt also Duplikate, und genau deshalb können solche Fälle überhaupt entstehen.

Warum das passieren kann
Der häufigste Grund ist, dass das Feld im Standard nur ein normales Produktfeld ist, aber keine harte Unique-Constraint auf Datenbankebene hat. Dadurch kann ein Import, eine manuelle Bearbeitung oder auch eine Automatisierung denselben Wert mehrfach setzen.

Typische Ursachen
Import von Produkten ohne Dublettenprüfung.

Manuelle Anlage oder Massenbearbeitung.

Automated Actions oder Custom-Code, der default_code setzt.

Mehrere Stellen im System, etwa product.template und Varianten, die unterschiedlich behandelt werden können.

Warum Odoo das nicht erzwingt
Odoo behandelt Internal Reference eher als empfohlenes SKU-Feld als als zwingend eindeutigen Primärschlüssel. Für manche Firmen ist das Feld leer, frei vergeben oder sogar nur informativ, deshalb ist es nicht automatisch wie eine eindeutige ID abgesichert. In der Praxis müssen Firmen mit strikten SKU-Regeln das oft selbst absichern, etwa per Automatisierung oder Custom Constraint.

Was das für dich bedeutet
Wenn du echte Eindeutigkeit willst, musst du sie aktiv einbauen, zum Beispiel per:

SQL-Constraint im Custom-Modul,

Automated Action mit Fehlermeldung,

oder regelmäßiger Prüfung per SQL im Terminal.

Ein gutes Beispiel: Wenn ein Import zwei Produkte mit ABC-100 anlegt, akzeptiert Odoo das ohne zusätzliche Absicherung. Erst eine eigene Regel verhindert das zuverlässig.

Praxisregel
Für ein sauberes ERP solltest du default_code wie eine SKU behandeln: ein Wert pro Produkt, ohne Ausnahmen. Wenn du das im Team sicherstellen willst, ist eine technische Sperre besser als nur Prozessdisziplin.

Ich kann dir als Nächstes ein kleines Odoo-Custom-Modul oder eine PostgreSQL-Constraint zeigen, die Dubletten dauerhaft verhindert.

für product.product
2 Schritte abgeschlossen
Ja — für product.product ist die sauberste Lösung eine Constraint direkt auf der Variantenebene. Odoo behandelt default_code standardmäßig nicht als hart eindeutiges Feld, deshalb musst du die Eindeutigkeit selbst erzwingen.

Modul für Varianten
Wenn der SKU pro Variante eindeutig sein soll, dann prüfst du auf product.product:

__manifest__.py

python
{
    "name": "Product Variant Default Code Unique",
    "version": "19.0.1.0.0",
    "depends": ["product"],
    "data": [],
    "installable": True,
    "application": False,
}
models/__init__.py

python
from . import product_product
models/product_product.py

python
from odoo import api, models, _
from odoo.exceptions import ValidationError

class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.constrains("default_code")
    def _check_unique_default_code(self):
        for record in self:
            code = (record.default_code or "").strip()
            if not code:
                continue

            duplicate = self.search([
                ("id", "!=", record.id),
                ("default_code", "=", code),
            ], limit=1)

            if duplicate:
                raise ValidationError(
                    _("Variant Internal Reference '%s' already exists.") % code
                )
Das blockiert Duplikate beim Speichern der Variante.

Optional: SQL-Constraint
Wenn du eine harte Datenbankregel willst, geht auch:

python
from odoo import models

class ProductProduct(models.Model):
    _inherit = "product.product"

    _sql_constraints = [
        (
            "default_code_unique",
            "unique(default_code)",
            "Variant Internal Reference must be unique.",
        )
    ]
Das ist strenger, aber nur sinnvoll, wenn bereits keine Duplikate mehr existieren.

Eindeutig oder leer
Leere Werte werden in beiden Varianten oben durch if not code: continue zugelassen. Wenn du default_code verpflichtend machen willst, ergänzt du zusätzlich required=True im Feld oder eine weitere Constraint. Für viele Setups ist das aber zu streng, weil manche Varianten bewusst noch keinen Code haben.

Praxis-Empfehlung
Für deinen Fall würde ich zuerst auf product.product absichern und zusätzlich im Import-/Migrationsprozess eine Dublettenprüfung laufen lassen. So verhinderst du, dass spätere Änderungen oder Massenimporte wieder doppelte Varianten-SKUs erzeugen. In Odoo-Projekten ist das meist robuster als nur auf manuelle Pflege zu vertrauen.

Ich kann dir als Nächstes die fertige Modulstruktur mit __init__.py, models, security und optionalem XML für eine Upgrade-sichere Version schreiben.

ja

Klar — ich habe dir ein kleines Odoo-19-Modul für product.product vorbereitet, das default_code bei Varianten eindeutig erzwingt .

Enthalten
default_code bleibt leer erlaubt.

Doppelte nicht-leere Varianten-Codes werden beim Speichern blockiert.

Die Prüfung läuft auf product.product, also auf Variantenebene .

Dateien
_manifest_.py

_init_.py

models/_init_.py

models/product_product.py

README.md

Nächster sinnvoller Schritt
Wenn du willst, ergänze ich dir als Nächstes noch:

eine SQL-Constraint statt Python-Constraint,

eine case-insensitive Prüfung,

oder eine Variante, die auch bei Importen sauber abbricht.

ich brauche nur die readme.md
3 Schritte abgeschlossen
README
Product Variant Default Code Unique
Dieses Modul erzwingt die Eindeutigkeit von default_code auf dem Modell product.product, also auf Variantenebene.

Verhalten
Leere default_code-Werte bleiben erlaubt.

Nicht-leere doppelte Varianten-Codes werden beim Speichern blockiert.

Bei einem Konflikt wird ein ValidationError ausgelöst.

Einsatzfall
Das Modul ist sinnvoll, wenn jede Produktvariante eine eigene eindeutige interne Referenz bzw. SKU haben soll.
 Odoo erzwingt diese Eindeutigkeit standardmäßig nicht zuverlässig selbst, deshalb ist eine zusätzliche Constraint sinnvoll.

Technische Umsetzung
Das Modul erweitert product.product und prüft per @api.constrains("default_code"), ob bereits eine andere Variante mit demselben default_code existiert. Wird ein Duplikat gefunden, wird das Speichern mit einer Validierungsfehlermeldung abgebrochen.

Installation
Den Modulordner in einen Addons-Pfad von Odoo kopieren.

Die App-Liste in Odoo aktualisieren.

Das Modul installieren.

Hinweis vor produktivem Einsatz
Wenn bereits doppelte Varianten-Codes in der Datenbank vorhanden sind, müssen diese zuerst bereinigt werden, bevor die Regel in laufenden Prozessen sauber greift.
 Das gilt besonders bei bestehenden Importen, Massenänderungen oder Fremdsystem-Synchronisationen.


Derzeit geöffnet
Product Variant Default Code Unique
Dieses Modul erzwingt die Eindeutigkeit von default_code auf dem Modell product.product, also auf Variantenebene.

Verhalten
Leere default_code-Werte bleiben erlaubt.

Nicht-leere doppelte Varianten-Codes werden beim Speichern blockiert.

Bei einem Konflikt wird ein ValidationError ausgelöst.

Einsatzfall
Das Modul ist sinnvoll, wenn jede Produktvariante eine eigene eindeutige interne Referenz bzw. SKU haben soll. Odoo erzwingt diese Eindeutigkeit standardmäßig nicht zuverlässig selbst, deshalb ist eine zusätzliche Constraint sinnvoll.

Technische Umsetzung
Das Modul erweitert product.product und prüft per @api.constrains("default_code"), ob bereits eine andere Variante mit demselben default_code existiert. Wird ein Duplikat gefunden, wird das Speichern mit einer Validierungsfehlermeldung abgebrochen.

Installation
Den Modulordner in einen Addons-Pfad von Odoo kopieren.

Die App-Liste in Odoo aktualisieren.

Das Modul installieren.

Hinweis vor produktivem Einsatz
Wenn bereits doppelte Varianten-Codes in der Datenbank vorhanden sind, müssen diese zuerst bereinigt werden, bevor die Regel in laufenden Prozessen sauber greift. Das gilt besonders bei bestehenden Importen, Massenänderungen oder Fremdsystem-Synchronisationen.

Follow-ups

Aufbau der manifest.py für eigene Odoo Module

Best Practices für Modulversionierung in Odoo 19

Unterschiede zwischen Python Constrains und SQL Constraints Odoo

Fehlerbehebung bei Modul-Update-Konflikten in Odoo

Automatisierte Tests für Odoo Module erstellen

Artefakte
5

Quellen
82
Lass den Computer das für dich erstellen
Der Computer erstellt vollständige Dokumente und Berichte aus nur einer einzigen Eingabeaufforderung. Er liefert fertige Ergebnisse als Google Docs, Word, PDF und mehr.



# Product Variant Default Code Unique

Dieses Modul erzwingt die Eindeutigkeit von `default_code` auf dem Modell `product.product`, also auf Variantenebene.[1][2]

## Verhalten

- Leere `default_code`-Werte bleiben erlaubt.
- Nicht-leere doppelte Varianten-Codes werden beim Speichern blockiert.
- Bei einem Konflikt wird ein `ValidationError` ausgelöst.

## Einsatzfall

Das Modul ist sinnvoll, wenn jede Produktvariante eine eigene eindeutige interne Referenz bzw. SKU haben soll.[2] Odoo erzwingt diese Eindeutigkeit standardmäßig nicht zuverlässig selbst, deshalb ist eine zusätzliche Constraint sinnvoll.[1]

## Technische Umsetzung

Das Modul erweitert `product.product` und prüft per `@api.constrains("default_code")`, ob bereits eine andere Variante mit demselben `default_code` existiert. Wird ein Duplikat gefunden, wird das Speichern mit einer Validierungsfehlermeldung abgebrochen.

## Installation

1. Den Modulordner in einen Addons-Pfad von Odoo kopieren.
2. Die App-Liste in Odoo aktualisieren.
3. Das Modul installieren.

## Hinweis vor produktivem Einsatz

Wenn bereits doppelte Varianten-Codes in der Datenbank vorhanden sind, müssen diese zuerst bereinigt werden, bevor die Regel in laufenden Prozessen sauber greift.[3] Das gilt besonders bei bestehenden Importen, Massenänderungen oder Fremdsystem-Synchronisationen.[4][5]
