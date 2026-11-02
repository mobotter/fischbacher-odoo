Global Quantity Discounts (Mengenstaffeln)
==========================================

|Odoo 19.0| |LGPL-3|

Dieses Odoo-19-Modul vereinheitlicht die Preisfindung in Angeboten und
Aufträgen: die Kundenpreisliste und zentrale Preislisten wie
**„Default“** (Staffelpreise am Produkt) und **„Mengenstaffeln (EUR)“**
werden gemeinsam betrachtet, der günstigste Preis gewinnt.
Kundenspezifische Preise gelten nur für den jeweiligen Kunden. Nicht
rabattfähige Produkte erhalten keine Rabatte.

Preisfindung
------------

+------+--------------------------------+-------------------------------+
| Rang | Quelle                         | Regel                         |
+======+================================+===============================+
| 1    | **Festpreis aus einem noch     | gilt immer, über allem        |
|      | gültigen Angebot des Kunden**  |                               |
|      | (Modul                         |                               |
|      | ``sale_customer_offer_price``) |                               |
+------+--------------------------------+-------------------------------+
| 2    | **Global markierte             | günstigster Preis aus 2–3     |
|      | Preislisten**: Default (1) mit | gewinnt                       |
|      | den Staffelpreisen aus dem     |                               |
|      | Produkt-Reiter „Preise“ und    |                               |
|      | Mengenstaffeln (234), inkl.    |                               |
|      | Kategorie- und globaler Regeln |                               |
+------+--------------------------------+-------------------------------+
| 3    | **Preisliste des Kunden** bzw. |                               |
|      | des Angebots – inkl. ihrer     |                               |
|      | Einträge im Reiter „Preise“    |                               |
+------+--------------------------------+-------------------------------+

Weitere Regeln:

- **Nicht rabattfähige Produkte** erhalten aus keiner Quelle eine
  Rabattregel (auch nicht aus der Mengenstaffel). Es zählen nur
  Festpreise – oder der Listenpreis. Manuell eingetragene
  Positionsrabatte sind nicht gesperrt.
- Innerhalb einer Preisliste gilt der Odoo-Standard: die erste passende
  Regel (Variante vor Produkt vor Kategorie vor global, dann höchste
  Mindestmenge).
- Rabatte verschiedener Preislisten werden **nicht kumuliert**;
  prozentuale Staffeln rechnen vom Listenpreis.
- Bei Gleichstand gewinnt die Preisliste des Angebots.

Kundenspezifische Preise
~~~~~~~~~~~~~~~~~~~~~~~~

Einträge im Reiter „Preise“ gehören immer zu einer Preisliste:

- Liegen sie in **Default** oder **Mengenstaffeln** (global markiert),
  gelten sie für alle Kunden.
- Liegen sie in einer **Kundenpreisliste** (z. B. „Jako“, „Bau Med“),
  gelten sie nur für Angebote mit genau dieser Preisliste. Dort
  konkurrieren sie mit Default und Mengenstaffeln; der günstigere Preis
  gewinnt.

Kundenpreislisten deshalb **nicht** als „Global berücksichtigen“
markieren.

Als Rabattregel gilt:

+------------------------------------------------------------+---------+
| Regeltyp (``compute_price``)                               | Rabatt? |
+============================================================+=========+
| ``percentage`` mit positivem Prozentsatz                   | ja      |
+------------------------------------------------------------+---------+
| ``percentage`` mit negativem Prozentsatz (Aufschlag)       | nein    |
+------------------------------------------------------------+---------+
| ``formula`` auf Basis Verkaufspreis/Preisliste mit         | ja      |
| ``price_discount > 0`` oder ``price_surcharge < 0``        |         |
+------------------------------------------------------------+---------+
| ``formula`` auf Basis Kosten (``standard_price``)          | nein    |
+------------------------------------------------------------+---------+
| ``fixed`` (Festpreis)                                      | nein    |
+------------------------------------------------------------+---------+

.. _beispiele-klebeband-listenpreis-450--mengenstaffel-25--ab-60-stück:

Beispiele (KLEBEBAND, Listenpreis 4,50 €, Mengenstaffel 25 % ab 60 Stück)
-------------------------------------------------------------------------

= =========== ================ ======== ==========================
# Rabattfähig Kundenpreisliste 50 Stück 70 Stück
= =========== ================ ======== ==========================
1 ja          10 % Rabatt      4,05 €   **3,375 €** (Staffel)
2 nein        10 % Rabatt      4,50 €   **4,50 €** (keine Rabatte)
3 nein        Festpreis 3,80 € 3,80 €   **3,80 €** (Festpreis)
= =========== ================ ======== ==========================

Mit einem Staffel-Festpreis in der Default-Preisliste, z. B. 3,20 € ab
100 Stück, erhalten ab 100 Stück alle drei Fälle 3,20 €. Ein Festpreis
aus einem gültigen Angebot des Kunden (z. B. 3,90 €) bleibt dagegen bei
jeder Menge bestehen.

Alle Fälle sind als automatisierte Tests hinterlegt
(``tests/test_global_quantity_discounts.py``).

**Rundung:** 3,375 € hat drei Nachkommastellen. Bei der
Dezimalgenauigkeit **„Product Price“** = 2 (Odoo-Standard) wird 3,38 €
berechnet. Für exakte Staffelpreise auf 3 Stellen erhöhen (Einstellungen
→ Technisch → Dezimalgenauigkeit); das wirkt auf alle Einzelpreise und
Belege.

Anzeige in der Angebotszeile
----------------------------

Ist **„Rabatte auf Positionen“** aktiv und gewinnt eine prozentuale
Regel, zeigt Odoo die Zeile als Listenpreis mit Rabatt an (4,50 € − 25
%). Bei nicht rabattfähigen Produkten gewinnt nie eine prozentuale
Regel, der Rabatt bleibt 0 %.

Konfiguration
-------------

1. **Verkauf → Produkte → Preislisten**: „Mengenstaffeln (EUR)“ und
   „Default“ mit **Global berücksichtigen** markieren (beim
   Installieren/Update automatisch: Mengenstaffeln bzw. ID 234 und ID
   1).
2. Allgemeine Staffelpreise am Produkt im Reiter **„Preise“** der
   Preisliste **Default** oder **Mengenstaffeln** zuordnen; Sonderpreise
   der Kundenpreisliste.
3. Am Produkt **„Rabattfähig“** bei Bedarf deaktivieren (gilt für
   Vorlage und alle Varianten).
4. Nur Preislisten derselben Währung und Gesellschaft werden verglichen.

Technische Umsetzung
--------------------

+----------------------------------------------------+----------------------------------+
| Stelle                                             | Zweck                            |
+====================================================+==================================+
| ``product.template.discount_allowed``              | Feld „Rabattfähig“, Varianten    |
|                                                    | erben es über ``_inherits``      |
+----------------------------------------------------+----------------------------------+
| ``product.pricelist.is_global_quantity_pricelist`` | „Global berücksichtigen“         |
|                                                    | (ersetzt feste ID 234)           |
+----------------------------------------------------+----------------------------------+
| ``product.pricelist._compute_price_rule``          | Vergleicht Kundenpreisliste und  |
|                                                    | globale Preislisten; gibt die    |
|                                                    | Regel des günstigsten Preises    |
|                                                    | zurück                           |
+----------------------------------------------------+----------------------------------+
| ``product.pricelist.item._is_applicable_for``      | Überspringt Rabattregeln bei     |
|                                                    | nicht rabattfähigen Produkten    |
+----------------------------------------------------+----------------------------------+
| ``hooks.py``                                       | Markiert bei der Installation    |
|                                                    | Mengenstaffeln (234) und Default |
|                                                    | (1) als global                   |
+----------------------------------------------------+----------------------------------+

``sale.order.line`` verwendet in Odoo 19 nur die **Regel**
(``pricelist_item_id``, ermittelt über ``_get_product_rule`` mit
``compute_price=False``) und berechnet den Preis daraus selbst. Deshalb
gibt ``_compute_price_rule`` die gewinnende Regel zurück und berechnet
die Preise für den Vergleich intern immer. Der Context-Schlüssel
``skip_global_quantity_pricelist`` verhindert Rekursion.

Positionen mit Festpreis aus ``sale_customer_offer_price`` werden nicht
über Preislisten neu berechnet (Test
``test_offer_fixed_price_beats_everything``).

Modulstruktur
-------------

.. code:: text

   global_quantity_discounts/
   ├── __init__.py
   ├── __manifest__.py
   ├── hooks.py
   ├── README.md
   ├── README.rst
   ├── models/
   │   ├── __init__.py
   │   ├── product_pricelist.py
   │   ├── product_pricelist_item.py
   │   └── product_template.py
   ├── tests/
   │   ├── __init__.py
   │   └── test_global_quantity_discounts.py
   └── views/
       ├── product_pricelist_views.xml
       └── product_views.xml

Installation und Update
-----------------------

Odoo.sh: Modul committen und pushen, dann in der Datenbank
aktualisieren. Lokal:

.. code:: bash

   odoo -d <datenbank> -u global_quantity_discounts --stop-after-init

Tests:

.. code:: bash

   odoo -d <testdatenbank> -i global_quantity_discounts \
        --test-enable --test-tags /global_quantity_discounts --stop-after-init

Fehlerbehebung
--------------

.. code:: python

   # Global markierte Preislisten
   env["product.pricelist"].search([("is_global_quantity_pricelist", "=", True)])

   # Preis und gewinnende Regel prüfen
   pl = env["product.pricelist"].browse(<kundenpreisliste_id>)
   product = env["product.product"].browse(<produkt_id>)
   price, rule_id = pl._get_product_price_rule(product, 70)
   env["product.pricelist.item"].browse(rule_id).pricelist_id.name

Bekannte Einschränkungen
------------------------

- Preislisten anderer Währung werden nicht verglichen.
- Angebote ohne Preisliste erhalten keine Preisregel (Odoo-Standard).
- „Rabattfähig“ sperrt keine manuell eingetragenen Positionsrabatte.

Changelog
---------

.. _190130-2026-09-23:

19.0.1.3.0 (2026-09-23)
~~~~~~~~~~~~~~~~~~~~~~~

- Migrationsskripte entfernt (Modul war produktiv noch nicht
  installiert).

- Kundenspezifische Preise (auch im Produkt-Reiter „Preise“) gelten nur
  für Kunden mit dieser Preisliste; global gelten nur markierte
  Preislisten.

- Nicht rabattfähige Produkte erhalten aus keiner Preisliste eine
  Rabattregel mehr (auch nicht aus der Mengenstaffel).

- Feld „Auch für nicht rabattfähige Produkte“ entfernt.

.. _190120-2026-09-23:

19.0.1.2.0 (2026-09-23)
~~~~~~~~~~~~~~~~~~~~~~~

- Mehrere Preislisten können global berücksichtigt werden (Default mit
  den Staffelpreisen aus dem Produkt-Reiter „Preise“ und
  Mengenstaffeln).
- Migration: ID 1 wird global markiert.
- Test: Festpreis aus Kundenangebot gilt über allen Preislisten.

.. _190110-2026-09-23:

19.0.1.1.0 (2026-09-23)
~~~~~~~~~~~~~~~~~~~~~~~

- **Fehlerbehebung:** Die Preisberechnung brach mit ``TypeError`` ab
  (falsche Signatur von ``_compute_price_rule``); zudem wurden nicht
  existierende Felder (``discount_type``, ``discount``) verwendet.
- **Fehlerbehebung:** In Angebotszeilen wurde die Staffel nie
  angewendet, da Odoo 19 dort ``compute_price=False`` übergibt.
- ``discount_allowed`` nur noch auf der Produktvorlage; bisherige
  Variantenwerte werden migriert.
- Rabattregeln werden über ``_is_applicable_for`` übersprungen, sodass
  nachrangige Festpreisregeln greifen.
- Staffel-Preisliste über Feld „Globale Mengenstaffel“ statt fester ID
  234.
- Preisberechnung der Staffel über Odoo-Standard (``_compute_price``):
  Datum, Kategorie, Einheit, Formeln, Rundung werden korrekt
  berücksichtigt.
- Feld „Rabattfähig“ im Produktformular korrekt platziert.
- Tests für Szenarien 1–3, Anzeige mit Positionsrabatt und Sonderfälle.
- README neu in UTF-8, zusätzlich ``README.md``; Manifest mit
  ``website`` und deutscher Beschreibung.

.. _190100-2026-08-27:

19.0.1.0.0 (2026-08-27)
~~~~~~~~~~~~~~~~~~~~~~~

- Erste Version für Odoo 19.

Autor
-----

Moritz Kern Fischbacher GmbH + Co. KG – https://fischbacher.de

Lizenz
------

LGPL-3. Copyright (c) 2026 Moritz Kern, Fischbacher GmbH + Co. KG

.. |Odoo 19.0| image:: https://img.shields.io/badge/Odoo-19.0-875A7B.svg
.. |LGPL-3| image:: https://img.shields.io/badge/license-LGPL--3-blue.svg
