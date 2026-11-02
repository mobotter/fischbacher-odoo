Fischbacher DATEV Deferred BU-Schlüssel
=======================================

Odoo-19-Custom-Modul für den DATEV-DATA-Export.

Das Modul ergänzt den DATEV-BU-Schlüssel ``40`` für automatisch erzeugte Deferred-Revenue-Buchungen auf Konto ``3900``.

Zweck
-----

Bei der Rechnungsabgrenzung erzeugt Odoo Buchungen zwischen:

::

    Erlöskonto 4400
    Konto 3900 Passive Rechnungsabgrenzung

Die automatisch erzeugten Deferred-Buchungszeilen enthalten keine ``tax_ids``. Der Standard-DATEV-Exporter kann deshalb den DATEV-Code der Steuer nicht ermitteln und lässt den BU-Schlüssel leer.

Dieses Modul übernimmt die DATEV-CSV-Exportmethode und ergänzt folgende Regel:

::

    Konto 3900 ODER Gegenkonto 3900
    Deferred Entry Type = revenue
    Ursprungsbuchung vorhanden
    Keine Steuer auf der Buchungszeile
    → BU-Schlüssel 40

Die ursprüngliche Rechnung bleibt unverändert und wird weiterhin mit der regulären Umsatzsteuer exportiert.

Voraussetzungen
---------------

- Odoo 19.
- Odoo Enterprise.
- Installiertes Modul ``l10n_de_reports``.
- Deutsche Buchhaltungslokalisierung.
- DATEV-DATA-Export über den Hauptbuchbericht.
- Konto ``3900`` für passive Rechnungsabgrenzung.
- Deferred-Revenue-Buchungen mit ``deferred_entry_type = revenue``.

Modulstruktur
-------------

::

    fischbacher_datev_deferred_bu/
    ├── __init__.py
    ├── __manifest__.py
    ├── README.rst
    └── models/
        ├── __init__.py
        └── datev_export.py

Installation
------------

1. Modul in das Repository kopieren
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Das Modul muss in einem Add-ons-Pfad liegen, der von Odoo geladen wird, beispielsweise:

::

    /home/odoo/src/user/fischbacher_datev_deferred_bu/

Der Add-ons-Pfad muss im Odoo-System enthalten sein.

2. Git-Commit erstellen
~~~~~~~~~~~~~~~~~~~~~~~

::

    git add fischbacher_datev_deferred_bu/
    git commit -m "Add DATEV BU key 40 for deferred revenue"
    git push

Auf Odoo.sh anschließend den Build der Ziel-Branch abwarten.

3. Apps-Liste aktualisieren
~~~~~~~~~~~~~~~~~~~~~~~~~~~

In Odoo:

1. Entwicklermodus aktivieren.
2. **Apps → Apps-Liste aktualisieren** öffnen.
3. Nach ``Fischbacher DATEV Deferred BU-Schlüssel`` suchen.
4. Modul installieren.

Falls das Modul nicht erscheint, den Filter ``Apps`` entfernen und die Liste erneut aktualisieren.

Modul aktualisieren
-------------------

Nach Änderungen am Python-Code die Version in ``__manifest__.py`` erhöhen:

::

    "version": "19.0.1.0.1",

Danach committen und pushen:

::

    git add fischbacher_datev_deferred_bu/
    git commit -m "Update DATEV deferred BU key logic"
    git push

Alternativ kann das Modul in einer Shell aktualisiert werden:

::

    odoo-bin -d "$PGDATABASE" \
        -u fischbacher_datev_deferred_bu \
        --stop-after-init

Funktionsweise
--------------

Der Standardexporter liest DATEV-BU-Schlüssel aus den Steuern einer Buchungszeile:

::

    codes = set(taxes.mapped("l10n_de_datev_code"))

Die Deferred-Revenue-Zeilen von Odoo enthalten jedoch:

::

    tax_ids = []

Die Custom-Methode prüft deshalb zusätzlich:

::

    if (
        aml.move_id.deferred_entry_type == "revenue"
        and aml.move_id.deferred_original_move_ids
        and (aml.account_id.code == "3900" or to_account_code == "3900")
    ):
        code_correction = "40"

Der Wert wird in die neunte DATEV-Spalte geschrieben:

::

    array[8] = code_correction

Diese Spalte heißt:

::

    BU-Schlüssel

Erwartetes Ergebnis
-------------------

Vor der Erweiterung:

::

    64;H;EUR;;;;3900;4400;;1708;MISC/2026/08/0848;...

Nach der Erweiterung:

::

    64;H;EUR;;;;3900;4400;40;1708;MISC/2026/08/0848;...

Weitere erwartete Beispiele:

::

    1600;H;EUR;;;;3900;4400;40;1708;MISC/2026/08/0837;...
    43;H;EUR;;;;3900;4400;40;1708;MISC/2026/08/0836;...

Die DATEV-Datei befindet sich im exportierten ZIP-Archiv unter:

::

    EXTF_accounting_entries.csv

Testen
------

1. Deferred-Moves prüfen
~~~~~~~~~~~~~~~~~~~~~~~~

Im Odoo.sh-Terminal:

::

    odoo-bin shell -d "$PGDATABASE" <<'PY'
    for move_id in [35201, 35212, 35213, 35214, 35235, 35236]:
        move = env["account.move"].browse(move_id)
        print(
            move.id,
            "deferred_entry_type=", move.deferred_entry_type,
            "deferred_original_move_ids=", move.deferred_original_move_ids.ids,
            "deferred_move_ids=", move.deferred_move_ids.ids,
        )
    PY

Erwartetes Ergebnis:

::

    deferred_entry_type= revenue
    deferred_original_move_ids= [35200]

2. Buchungszeilen prüfen
~~~~~~~~~~~~~~~~~~~~~~~~

::

    odoo-bin shell -d "$PGDATABASE" <<'PY'
    invoice = env["account.move"].browse(35200)

    for move in invoice.deferred_move_ids:
        for line in move.line_ids:
            if line.account_id.code in ("3900", "4400"):
                print(
                    "move=", move.id,
                    "line=", line.id,
                    "account=", line.account_id.code,
                    "debit=", line.debit,
                    "credit=", line.credit,
                    "tax_ids=", line.tax_ids.ids,
                    "deferred_entry_type=", move.deferred_entry_type,
                    "original_moves=", move.deferred_original_move_ids.ids,
                )
    PY

Bei den Deferred-Zeilen ist erwartungsgemäß:

::

    tax_ids = []
    deferred_entry_type = revenue
    original_moves = [35200]

3. DATEV-Export ausführen
~~~~~~~~~~~~~~~~~~~~~~~~~

In Odoo:

1. **Buchhaltung → Bericht → Hauptbuch** öffnen.
2. Den gewünschten Zeitraum auswählen.
3. **DATEV DATA (ZIP)** exportieren.
4. ``EXTF_accounting_entries.csv`` aus dem ZIP öffnen.
5. Nach Konto ``3900`` filtern.
6. Spalte ``BU-Schlüssel`` kontrollieren.

Erwartet:

::

    BU-Schlüssel = 40

Fachliche Abgrenzung
--------------------

Die normale Subscription-Rechnung wird weiterhin mit der regulären Umsatzsteuer gebucht, beispielsweise:

::

    Nettoerlös:       1.664,00 €
    19 % Umsatzsteuer:  316,16 €
    Brutto:           1.980,16 €

Die Deferred-Revenue-Buchungen verteilen den Nettobetrag über den Leistungszeitraum:

::

    Erlöskonto 4400 an Konto 3900

Das Modul fügt dabei keinen Umsatzsteuerbetrag hinzu. Es ergänzt ausschließlich den BU-Schlüssel ``40`` in der DATEV-Exportdatei.

Die fachliche Behandlung muss mit dem Steuerberater abgestimmt werden, insbesondere für:

- passive Rechnungsabgrenzung.
- Umsatzsteuerzeitpunkt.
- DATEV-BU-Schlüssel.
- Behandlung von Subscription-Leistungen.
- periodenübergreifende Rechnungen.

Sicherheitsregeln
-----------------

Das Modul:

- ändert keine bestehenden Buchungen.
- schreibt keine Steuer auf bestehende Buchungszeilen.
- ändert nicht die ursprüngliche Subscription-Rechnung.
- verändert nicht die Steuerdefinition ``Rechnungsabgrenzung 0%``.
- wirkt nur beim DATEV-CSV-Export.
- setzt BU ``40`` nur für Deferred-Revenue-Zeilen auf Konto ``3900`` oder mit Gegenkonto ``3900``.

Fehlerbehebung
--------------

BU-Schlüssel bleibt leer
~~~~~~~~~~~~~~~~~~~~~~~~

Prüfe:

::

    Konto = 3900 ODER Gegenkonto = 3900
    move.deferred_entry_type = revenue
    move.deferred_original_move_ids ist nicht leer

Prüfe außerdem, ob das Custom-Modul installiert ist und ob nach einer Codeänderung die Manifest-Version erhöht wurde.

Modul wird nicht angezeigt
~~~~~~~~~~~~~~~~~~~~~~~~~~

Prüfe:

::

    find /home/odoo/src/user/fischbacher_datev_deferred_bu -maxdepth 2 -type f

Danach:

1. Apps-Liste aktualisieren.
2. Filter ``Apps`` entfernen.
3. Odoo.sh-Build-Log prüfen.
4. ``__manifest__.py`` kontrollieren.
5. Abhängigkeit ``l10n_de_reports`` prüfen.

Export schlägt mit einem Python-Fehler fehl
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Die Methode ``_l10n_de_datev_get_csv()`` muss exakt zur installierten Odoo-19-Version passen. Bei einem Enterprise-Update sollte die kopierte Methode mit der aktuellen Datei verglichen werden:

::

    sed -n '264,500p' \
    /home/odoo/src/enterprise/l10n_de_reports/models/datev_export_csv.py

Die Custom-Datei muss insbesondere bei Änderungen an folgenden Bereichen aktualisiert werden:

- DATEV-Header.
- Anzahl der CSV-Spalten.
- Fremdwährungslogik.
- Steuerberechnung.
- Zahlungslogik.
- Rundungskorrektur.

Wartung bei Odoo-Updates
------------------------

Da die komplette Methode ``_l10n_de_datev_get_csv()`` aus der Enterprise-Version übernommen wird, muss sie bei Updates verglichen werden.

Nach einem Odoo-Update:

::

    diff -u \
    /home/odoo/src/enterprise/l10n_de_reports/models/datev_export_csv.py \
    /home/odoo/src/user/fischbacher_datev_deferred_bu/models/datev_export.py

Dabei sollte die Custom-Datei weiterhin nur die gewünschte fachliche Änderung enthalten:

::

    elif (
        aml.move_id.deferred_entry_type == "revenue"
        and aml.move_id.deferred_original_move_ids
        and (aml.account_id.code == "3900" or to_account_code == "3900")
    ):
        code_correction = "40"

Lizenz
------

LGPL-3, sofern nicht anders im Projekt festgelegt.
