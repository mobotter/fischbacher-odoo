# Druck-Kopien für IoT-Berichte

Autor: Moritz Kern
Firma: Fischbacher GmbH + Co. KG
Odoo-Version: 19.0

## Funktion

Ergänzt Berichtaktionen um „Standard IoT-Kopien“.

Der Standard-Client erhält die ursprünglichen Druckaufträge unverändert.
Zusätzliche Exemplare werden serverseitig über
iot.channel.send_message() als iot_action eingereiht.

Beispiel: Bei 2 Kopien wird pro ursprünglichem Druckauftrag
ein zusätzlicher Auftrag über den IoT-Kanal eingereiht.

## Einrichtung

1. Modul installieren oder aktualisieren und Odoo neu starten.
2. Gewünschte Berichtaktion im Entwicklermodus öffnen.
3. „Standard IoT-Kopien“ auf die gewünschte Gesamtzahl setzen.
4. Über den normalen IoT-Druckweg testen.

Werte kleiner als 1 werden als 1 behandelt.

## Dokumentformat

Die von render_document gelieferten Base64-Daten werden nicht decodiert.
Für die zusätzliche Nachricht werden Base64-Bytes in einen
ASCII-String umgewandelt.

## Einschränkungen

Zusätzliche Druckaufträge benötigen eine funktionierende
WebSocket-/Bus-Verbindung zum IoT-System. Sie verwenden nicht
die WebRTC-/Longpolling-Fallbacks des normalen Browserdrucks.

Ein erfolgreich eingereihter Auftrag bestätigt nicht den
physischen Ausdruck. Für zusätzliche Aufträge registriert
dieses Modul keine Client-Erfolgsmeldungen.

Die Reihenfolge zwischen Standarddruck und zusätzlichen
Druckaufträgen ist nicht garantiert.

Overrides anderer Module, die render_document ohne super()
beenden, umgehen diese Erweiterung.

Das trifft in der untersuchten Installation auf
delivery_iot.report_shipping_labels und
delivery_iot.report_shipping_docs zu.
