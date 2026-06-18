# Lots Serial

## Übersicht

Dieses Modul erweitert `stock.lot` in Odoo um prüfungsrelevante Datumsfelder für Serien- und Losnummern. Es unterstützt die Verwaltung von TÜV-, UVV- und Sicherheitsbrems-Prüfungen direkt am jeweiligen Lot und stellt deren Status farblich in der Listenansicht dar.

## Funktionsumfang

- Fügt am Modell `stock.lot` drei zusätzliche Datumsfelder hinzu:
  - `tuv_date` für die allgemeine TÜV-Prüfung
  - `uvv_date` für die UVV-Prüfung
  - `safety_brake_date` für Sicherheitsbremsen-Prüfung oder -Wechsel
- Berechnet für jedes Prüfdatum einen Statuswert:
  - `green` bei mehr als 3 Monaten Restlaufzeit
  - `orange` bei weniger als 3 Monaten Restlaufzeit
  - `red` bei abgelaufener Prüfung oder fehlendem Datum
- Ergänzt die Formularansicht von Lots/Seriennummern um die drei Datumsfelder.
- Ergänzt die Listenansicht um farblich dekorierte Datumsfelder für eine schnelle visuelle Prüfung.

## Technische Details

| Feld | Beschreibung |
|---|---|
| `tuv_date` | Datum der TÜV-Prüfung |
| `uvv_date` | Datum der UVV-Prüfung |
| `safety_brake_date` | Datum für Sicherheitsbremse |
| `tuv_status` | Berechneter Status für TÜV |
| `uvv_status` | Berechneter Status für UVV |
| `safety_brake_status` | Berechneter Status für Sicherheitsbremse |

Die Statusberechnung erfolgt über eine Hilfsmethode, die auf Basis des Referenzdatums ein Ablaufdatum und ein Warnfenster von 3 Monaten berechnet. Für `tuv_date` und `uvv_date` wird eine Gültigkeit von 1 Jahr verwendet, für `safety_brake_date` eine Gültigkeit von 6 Jahren.

## Statuslogik

Die Ampellogik arbeitet nach folgendem Schema:

- **Grün**: Prüfung läuft noch länger als 3 Monate.
- **Orange**: Prüfung läuft in weniger als 3 Monaten ab.
- **Rot**: Prüfung ist abgelaufen oder es wurde kein Datum hinterlegt.

Damit eignet sich das Modul besonders für Geräte oder Maschinen, bei denen wiederkehrende Prüfungen dokumentiert und frühzeitig überwacht werden müssen.

## Ansichtsanpassungen

Das Modul erweitert folgende Standardansichten von Odoo:

- Formularansicht `stock.view_production_lot_form`
- Listenansicht `stock.view_production_lot_tree`

In der Listenansicht werden die Datumsfelder mit `decoration-success`, `decoration-warning` und `decoration-danger` eingefärbt. Dadurch lassen sich fällige oder abgelaufene Prüfungen direkt in der Übersicht erkennen.

## Typischer Einsatz

Das Modul ist besonders sinnvoll für mietbare oder prüfpflichtige Maschinen, Geräte und Komponenten, bei denen Seriennummern bzw. einzelne Lots verwaltet werden und Prüfintervalle nachvollziehbar bleiben müssen.

## Installation

1. Modul in den Addons-Pfad von Odoo legen.
2. App-Liste aktualisieren.
3. Modul installieren oder bei Änderungen upgraden.

## Hinweise

Die Statusfelder sind berechnete Felder und werden nicht persistent gespeichert. Für die Farbkennzeichnung in der Listenansicht ist entscheidend, dass die berechneten Statuswerte im jeweiligen Datensatz korrekt verfügbar sind. Bei Erweiterungen der Prüfintervalle oder zusätzlicher Prüfarten kann die Methode `get_color_status` als zentrale Logik wiederverwendet werden.
