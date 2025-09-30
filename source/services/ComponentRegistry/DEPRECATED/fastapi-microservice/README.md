# FastAPI E-Commerce Microservice

Ein umfassender Python-Microservice mit FastAPI, der CRUD-Operationen für ein E-Commerce-System bereitstellt. Das System verwaltet Benutzer, Produkte und Bestellungen mit vollständigen Relationen in einer eingebetteten SQLite-Datenbank.

## Features

- **Vollständige CRUD-Operationen** für alle Entitäten
- **Relationale Datenbank** mit SQLAlchemy ORM
- **Eingebettete SQLite-Datenbank** (keine externe Datenbank erforderlich)
- **Pydantic Schemas** für Validierung und Serialisierung
- **Automatische API-Dokumentation** mit Swagger UI
- **Paginierung** für Listen-Endpunkte
- **Suchfunktionalität** für Produkte
- **Bestandsverwaltung** mit automatischen Updates
- **Fehlerbehandlung** mit aussagekräftigen HTTP-Status-Codes

## Datenmodell

### Entitäten und Relationen


## Installation und Setup

### Voraussetzungen
- Python 3.8+
- pip

### Installation

1. **Abhängigkeiten installieren:**
```bash
pip install -r requirements.txt
```

2. **Datenbank initialisieren und Testdaten laden:**
```bash
python seed_data.py
```

3. **Server starten:**
```bash
python main.py
```

Der Server läuft standardmäßig auf `http://localhost:8000`

## API-Dokumentation

Nach dem Start des Servers ist die automatische API-Dokumentation verfügbar unter:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API-Endpunkte


### Weitere Endpunkte
- `GET /health` - Health Check
- `GET /stats` - Systemstatistiken

## Beispiel-Requests


## Projektstruktur

```
fastapi-microservice/
├── main.py              # FastAPI-Anwendung mit REST-Endpunkten
├── models.py            # SQLAlchemy-Datenbankmodelle
├── schemas.py           # Pydantic-Schemas für Validierung
├── crud.py              # CRUD-Operationen für alle Entitäten
├── database.py          # Datenbankkonfiguration und Session-Management
├── seed_data.py         # Testdaten-Generator
├── requirements.txt     # Python-Abhängigkeiten
└── README.md           # Dokumentation
```

## Features im Detail

### Validierung und Fehlerbehandlung
- Automatische Validierung aller Eingabedaten
- Eindeutigkeitsprüfung für Benutzernamen und E-Mails
- Bestandsprüfung bei Bestellungen
- Konsistente HTTP-Status-Codes und Fehlermeldungen

### Datenbankrelationen
- Automatisches Laden verwandter Daten (Eager Loading)
- Kaskadierendes Löschen bei Bestellungen
- Fremdschlüssel-Constraints für Datenintegrität

### Performance-Optimierungen
- Paginierung für große Datenmengen
- Datenbankindizes für häufige Abfragen
- Effiziente JOIN-Operationen

## Entwicklung und Erweiterung

Das Projekt folgt bewährten Praktiken:
- **Separation of Concerns**: Klare Trennung von Modellen, Schemas, CRUD und API-Logic
- **Dependency Injection**: Verwendung von FastAPI's Dependency-System
- **Type Hints**: Vollständige Typisierung für bessere IDE-Unterstützung
- **Dokumentation**: Automatische API-Dokumentation und Docstrings

### Neue Entitäten hinzufügen
1. Modell in `models.py` definieren
2. Schemas in `schemas.py` erstellen
3. CRUD-Operationen in `crud.py` implementieren
4. API-Endpunkte in `main.py` hinzufügen

## Lizenz

Dieses Projekt ist ein Beispiel-Microservice für Demonstrationszwecke.