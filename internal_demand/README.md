Internal Demand
===============

Eigenbedarfsverwaltung fuer Odoo 19 auf Basis von Verkaufsangeboten und Verkaufsauftraegen.

Autor: Moritz Kern
Firma: Fischbacher GmbH + Co. KG
Technische Version: 19.0.1.0.0

Zweck
------

Das Modul erweitert Verkaufsauftraege mit dem Kennzeichen Eigenbedarf.
Ein bestehendes Angebot kann als Eigenbedarf markiert werden, ohne dass ein
neuer Datensatz erzeugt wird.

Angebotsnummer, Positionen, Mengen, Preise, Rabatte, Chatter, Aktivitaeten,
Anhaenge und Historie bleiben erhalten. Der bestehende Beleg wird nur mit dem
Feld is_internal_demand markiert.

Der Eigenbedarf ist unter Verkauf, Angebote, Eigenbedarf erreichbar.

Funktionen
----------

Eigenbedarf anlegen
~~~~~~~~~~~~~~~~~~~

Ueber Verkauf, Angebote, Eigenbedarf kann ein neuer Eigenbedarfsbeleg angelegt
werden. Neue Belege aus diesem Menue werden automatisch als Eigenbedarf
markiert.

Angebot umwandeln
~~~~~~~~~~~~~~~~~

Ein Angebot im Status Entwurf oder Gesendet kann ueber die Aktion
In Eigenbedarf umwandeln markiert werden.

Dabei wird keine Kopie erstellt und keine neue Angebotsnummer vergeben.
Preis, Menge und Rabatt vorhandener Positionen bleiben unveraendert.

Zurueck in Angebot umwandeln
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Ein Eigenbedarfsbeleg im Status Entwurf oder Gesendet kann ueber die Aktion
Zurueck in Angebot umwandeln wieder als normales Angebot markiert werden.

Auch bei dieser Rueckumwandlung werden Preis, Menge und Rabatt nicht veraendert.

Preislogik
----------

Beim Anlegen neuer Produktpositionen in einem Eigenbedarfsbeleg verwendet das
Modul den Standard-Verkaufspreis des Produkts. Vorhandene Positionen aus einem
umgewandelten Angebot werden nicht neu berechnet.

Der Standard-Verkaufspreis ist das Feld product.lst_price.

Neue Eigenbedarfspositionen erhalten den Standard-Verkaufspreis und einen
Rabatt von null Prozent. Vorhandene Positionen bleiben beim Umwandeln
unveraendert.

Bestaetigung
------------

Ein Eigenbedarfsbeleg bleibt technisch ein normaler sale.order und kann mit
dem Odoo-Standardbutton bestaetigt werden. Die Bestaetigung aendert durch
dieses Modul keine Preise, Mengen oder Rabatte.

Danach gelten die eingerichteten Odoo-Prozesse fuer Lagerreservierung,
Lagerentnahme, Beschaffung, Routen und Auswertungen.

Rechnungen
----------

Das Modul blockiert die Erstellung von Kundenrechnungen fuer Eigenbedarfsauftraege.

Installation
------------

1. Den Modulordner internal_demand in ein Odoo-Addons-Verzeichnis kopieren.
2. Sicherstellen, dass das Verzeichnis im Odoo-Addons-Pfad enthalten ist.
3. Odoo oder den Odoo.sh-Build neu starten.
4. Den Entwicklermodus aktivieren.
5. In Apps die Apps-Liste aktualisieren.
6. Nach Internal Demand suchen.
7. Das Modul installieren.

Aktualisierung
--------------

1. Aenderungen an Python- oder XML-Dateien deployen oder committen.
2. Das Modul Internal Demand in Apps aktualisieren.
3. Den Browser vollstaendig neu laden.

Modulstruktur
-------------

::

   internal_demand/
       __init__.py
       __manifest__.py
       README.md
       models/
           __init__.py
           sale_order.py
       views/
           sale_order_views.xml

Technische Umsetzung
--------------------

Datenmodell
~~~~~~~~~~~

Das Modul erweitert sale.order um das gespeicherte Boolean-Feld
is_internal_demand.

Eigenbedarfsbelege koennen mit einer Domain gefiltert werden, die
is_internal_demand auf True prueft.

Methoden
~~~~~~~~

Die Methode action_convert_to_internal_demand markiert ein bestehendes Angebot
als Eigenbedarf.

Die Methode action_convert_to_quotation entfernt die Eigenbedarf-Markierung.

Die Methode action_confirm bestaetigt den Beleg mit der Standardlogik.

Die Methode action_create_invoice blockiert Kundenrechnungen fuer Eigenbedarf.

Positionslogik
~~~~~~~~~~~~~~

Bei neuen Produktpositionen in einem Eigenbedarfsbeleg wird der
Standard-Verkaufspreis des Produkts verwendet. Bestehende Positionen eines
umgewandelten Angebots werden dabei nicht veraendert.

Berechtigungen
--------------

Das Modul verwendet die vorhandenen Berechtigungen aus Verkauf und Lager.
Es werden keine eigenen Benutzergruppen oder Zugriffsrechte angelegt.

Empfohlene Konfiguration
------------------------

Interner Partner
~~~~~~~~~~~~~~~~

Es empfiehlt sich ein eigener Kontakt mit der Bezeichnung Eigenbedarf
Fischbacher. Beim Erstellen eines neuen Eigenbedarfsbelegs verwendet das Modul
standardmaessig den Partner der aktuellen Gesellschaft.

Grosse Artikellisten
~~~~~~~~~~~~~~~~~~~~

Bei mehr als 200 Positionen empfiehlt sich ein CSV- oder XLSX-Import, ein
Assistent zur Massenerfassung oder die Uebernahme aus einer Vorlage. Dadurch
werden Browser-Interaktionen und unnötige Preisberechnungen reduziert.

Hinweise
--------

Individuelle Module, Studio-Anpassungen oder Drittanbieter-Module koennen
zusaetzliche Preis-, Steuer- oder Lagerlogik ausloesen. Diese Logik wird durch
das Modul nicht generell deaktiviert.

Die Umwandlung in Eigenbedarf und die Rueckumwandlung sind nur im Status
Entwurf oder Gesendet zulaessig.
