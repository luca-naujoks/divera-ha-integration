# DIVERA 24/7 – Home Assistant Integration

[![Buy me a Beer](https://img.buymeacoffee.com/button-api/?text=Buy%20me%20a%20Beer&emoji=🍺&slug=lassefactory&button_colour=FFDD00&font_colour=000000&font_family=Comic&outline_colour=000000&coffee_colour=ffffff)](https://www.buymeacoffee.com/lassefactory)

Eine inoffizielle Home Assistant Integration für DIVERA 24/7, die Einsätze in Echtzeit über eine WebSocket-Verbindung empfängt.

---

## Funktionsweise

Die Integration verbindet sich dauerhaft per **WebSocket** mit den DIVERA-Servern (`wss://ws.divera247.com`). Sobald DIVERA einen neuen Alarm meldet, wird einmalig die REST-API abgefragt und der Sensor in Home Assistant aktualisiert – ohne unnötiges Polling.

---

## Voraussetzungen

- Home Assistant OS, Supervised oder Core
- DIVERA 24/7 Account mit API-Zugang
- HACS installiert (für die empfohlene Installation)

---

## Installation über HACS (empfohlen)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=lassefactory&repository=divera-hacs)

1. HACS in Home Assistant öffnen
2. Oben rechts auf die **drei Punkte** klicken → **Benutzerdefinierte Repositories**
3. Folgendes eintragen:
   - **Repository:** `https://github.com/lassefactory/divera-hacs`
   - **Kategorie:** Integration
4. **Hinzufügen** klicken
5. In HACS nach **DIVERA 24/7** suchen und **Herunterladen** klicken
6. Home Assistant neu starten

---

## Manuelle Installation

1. Den Ordner `custom_components/divera/` aus diesem Repository herunterladen
2. In das Home Assistant Konfigurationsverzeichnis kopieren:
   ```
   config/custom_components/divera/
   ```
3. Home Assistant neu starten

Die fertige Verzeichnisstruktur sollte so aussehen:
```
config/
└── custom_components/
    └── divera/
        ├── activity.py
        ├── __init__.py
        ├── binary_sensor.py
        ├── config_flow.py
        ├── const.py
        ├── coordinator.py
        ├── entity.py
        ├── manifest.json
        ├── sensor.py
        ├── strings.json
        └── translations/
            ├── de.json
            └── en.json
```

---

## Einrichtung

1. In Home Assistant: **Einstellungen → Geräte & Dienste → Integration hinzufügen**
2. Nach **DIVERA** suchen und auswählen
3. **API-Schlüssel eingeben**
   - Den Accesskey aus DIVERA eintragen
   - DIVERA → Einstellungen → DEBUG → Accesskey kopieren
4. **Einheit auswählen** aus der Liste der verfügbaren Einheiten
5. **Einsatzdauer (Minuten)** festlegen (Standard: 60, mindestens 1 Minute)
6. Fertig – die Sensoren erscheinen automatisch am Gerät der Einheit

---

## Sensor

Nach der Einrichtung werden einzelne Sensoren für die Einsatzdaten erstellt.
Alle verwenden dieselbe WebSocket-/REST-Aktualisierung; zusätzliche Sensoren erzeugen keine zusätzlichen API-Abfragen.

| Sensor | Inhalt |
|---|---|
| Stichwort | Alarmstichwort |
| Beschreibung | Meldungstext, auf 255 Zeichen gekürzt; vollständiger Text im Attribut `full_description` |
| Adresse | Einsatzadresse (maximal 255 Zeichen) |
| Einsatz-ID | DIVERA Alarm-ID |
| Alarmiert am | Zeitpunkt als nativer Home-Assistant-Zeitstempel |
| Breitengrad / Längengrad | GPS-Koordinaten als Zahlen |
| Anzahl Fahrzeuge | Anzahl der Einträge in der Fahrzeugliste; vollständige Liste im Attribut `vehicles` |
| Sonderrechte (Binärsensor) | Wert des API-Felds `priority` |
| Geschlossen (Binärsensor) | Wert des API-Felds `closed` |
| Aktiver Einsatz (Binärsensor) | Zeitlich begrenzte Anzeige eines Einsatzes |

Die Namen werden auf Deutsch und Englisch übersetzt. Entity-IDs vergibt Home Assistant automatisch;
sie können in den Einstellungen angepasst werden. Fehlende oder ungültige Werte erscheinen als
`unknown`, bei einem fehlgeschlagenen Datenabruf werden die Sensoren `unavailable`.

### Aktiver Einsatz

Der Binärsensor schaltet ein, sobald eine neue, nicht geschlossene Einsatz-ID empfangen wird.
Nach der eingestellten Einsatzdauer schaltet er automatisch aus, auch ohne weitere API-Aktualisierung.
Wird der Einsatz geschlossen oder nicht mehr von der API geliefert, schaltet er früher aus.
Ein neuer Einsatz startet die Dauer neu; Änderungen desselben Einsatzes verlängern sie nicht.
Nach Ablauf bleibt derselbe Einsatz ausgeschaltet, selbst wenn er weiter von der API geliefert wird.
Die übrigen Sensoren zeigen weiterhin die gelieferten Einsatzdaten an.

Die Einsatzdauer lässt sich unter **Einstellungen → Geräte & Dienste → DIVERA → Konfigurieren** ändern.
Bestehende Installationen verwenden zunächst 60 Minuten. Änderungen werden ab dem ursprünglichen
Aktivierungszeitpunkt berechnet. Ein Neustart oder Neuladen setzt die Dauer nicht zurück;
Einsatz-ID und Ablaufzeit werden gespeichert. Beim erstmaligen Einrichten aktiviert auch ein
bereits vorhandener, nicht geschlossener Einsatz den Timer ab Empfang.
Die Attribute `alarm_id` und `expires_at` zeigen die zuletzt verarbeitete Einsatz-ID und Ablaufzeit.
Während einer API-Störung zeigt auch dieser Sensor `unavailable`; die Ablaufzeit läuft weiter.

### Bisheriger Sensor (weiterhin verfügbar)

Der bisherige Sensor bleibt mit seinem Zustand, seiner eindeutigen ID und allen Attributen erhalten,
damit bestehende Dashboards, Automationen und Blueprint-Instanzen weiter funktionieren:

**`sensor.divera_<einheitname>`**

| | |
|---|---|
| **State** | Stichwort des aktiven Alarms oder `Kein aktiver Einsatz` |

### Attribute

| Attribut | Beschreibung |
|---|---|
| `stichwort` | Alarmstichwort |
| `beschreibung` | Freitext / Meldungstext |
| `adresse` | Einsatzadresse |
| `einsatz_id` | Interne DIVERA Alarm-ID |
| `prioritaet` | Sonderrechte (true/false) |
| `alarmiert_am` | Alarmierungszeitpunkt (ISO 8601) |
| `geschlossen` | true wenn Einsatz abgeschlossen |
| `fahrzeuge` | Alarmierte Fahrzeuge |
| `latitude` / `longitude` | GPS-Koordinaten |
| + weitere | Alle weiteren Felder aus der DIVERA API |

---

## Blueprint – Alarm-Automation

Im Ordner `blueprints/` liegt ein fertiges Blueprint, mit dem du ganz einfach Automationen erstellen kannst.
Es reagiert auf Änderungen der Einsatz-ID und erkennt dadurch auch aufeinanderfolgende Einsätze
mit demselben Stichwort. Änderungen am Text desselben Einsatzes lösen keine neue Alarmierung aus.

### Blueprint installieren

[![Blueprint importieren](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fraw.githubusercontent.com%2Flassefactory%2Fdivera-hacs%2Fmain%2Fblueprints%2Fdivera_alarm.yaml)

Oder manuell: Datei `blueprints/divera_alarm.yaml` kopieren nach:
```
config/blueprints/automation/divera/divera_alarm.yaml
```
In HA: **Einstellungen → Automationen → Blueprints** – das Blueprint erscheint automatisch

### Blueprint verwenden

Das Blueprint bietet folgende Einstellungen:

| Einstellung | Beschreibung |
|---|---|
| **DIVERA Sensor** | Bisherigen DIVERA-Alarm-Sensor mit dem Attribut `einsatz_id` auswählen |
| **Stichwörter filtern** | Kommagetrennte Stichwörter die NICHT auslösen sollen (z. B. `THL, Übung`) |
| **Aktionen** | Frei definierbar – Benachrichtigung, Licht, TTS, etc. |

### Beispiel-Automation

```yaml
automation:
  - alias: "DIVERA Alarm – Benachrichtigung"
    use_blueprint:
      path: divera/divera_alarm.yaml
      input:
        sensor_entity: sensor.divera_meine_einheit
        filter_keywords: "THL, Übung, Feuer Klein"
        actions:
          - service: notify.mobile_app_mein_handy
            data:
              title: "Neuer Einsatz!"
              message: >
                {{ state_attr('sensor.divera_meine_einheit', 'stichwort') }}
                – {{ state_attr('sensor.divera_meine_einheit', 'adresse') }}
```

---

## Debugging

Debug-Logging in `configuration.yaml` aktivieren:

```yaml
logger:
  default: warning
  logs:
    custom_components.divera: debug
```

Logs einsehen unter: **Einstellungen → System → Protokolle**

---

## Fehlerbehebung

| Problem | Lösung |
|---|---|
| Integration erscheint nicht | HA vollständig neu starten, nicht nur neu laden |
| `Kein aktiver Einsatz` trotz Alarm | Debug-Logging aktivieren und Logs prüfen |
| Ungültiger API-Schlüssel | Neuen Accesskey in DIVERA unter Einstellungen → DEBUG generieren |
| Automation löst nicht aus | Prüfen ob Stichwort-Filter das Stichwort ausschließt |

---

## Lizenz

Dieses Projekt steht unter der **Creative Commons Attribution-NonCommercial 4.0 (CC BY-NC 4.0)** Lizenz.
Nutzung und Weitergabe erlaubt, jedoch **keine kommerzielle Nutzung** ohne ausdrückliche Genehmigung.

Dieses Projekt ist nicht offiziell mit DIVERA GmbH verbunden.
