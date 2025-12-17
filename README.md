# CloudCookbook API

## Autoren  | **Team 2 - Cloud Engineering Weiterbildung** 
| Name | Rolle | GitHub |
| :--- | :--- | :--- |
| **Auren Appelt** | Cloud Architect & Backend | [Patch & Potion](https://github.com/Scarred95) |
| **Tobias Hoppen** | Database & Infrastructure | [Izo1991](https://github.com/Izo1991) |
| **Tommy Nguyen** | Backend & Logic | [HoodedHenry](https://github.com/HoodedHenry) |
## Projektbeschreibung
![Project Status](https://img.shields.io/badge/Project_Status-V1_Released-success)
![Build Status](https://img.shields.io/badge/Phase-Development-blueviolet)
![Python](https://img.shields.io/badge/python-3.10+-blue)

Die **CloudCookbook API** ist eine RESTful-Schnittstelle zur intelligenten Verwaltung von Kochrezepten, Benutzerprofilen und digitalen Vorratsschränken (Pantries). 
Entwickelt vom **Team 2 (Appelt, Nguyen, Hoppen)**, dient diese Anwendung als Backend-Layer für das Cloud Engineering Projekt.

Die Architektur folgt dem Prinzip der **"Separation of Concerns"**:
* **API-Layer:** FastAPI (Routing & Request Handling)
* **Data Validation:** Pydantic (Strikte Typisierung & Constraints)
* **Business Logic:** Helper-Module (Transaktionen, Matchmaking)
* **Persistence:** SQLite (Relationale Datenhaltung)

Ein besonderer Fokus liegt auf **Datenintegrität** (Transaktionen, Foreign Keys), **Observability** (umfassendes Logging) und **User Experience** (Smart Matchmaking Algorithmus).


### Database Schema

![Database Diagram](assets/db_schema.png)

*[View interactive version on dbdiagram.io](https://dbdiagram.io/d/db_schema_CCB-69427877e4bb1dd3a96a5559)*


## Ordnerstruktur

Die Struktur ist modular aufgebaut, um Skalierbarkeit zu gewährleisten:
```text
CloudCookbook/
├── main.py                  # Entry Point (FastAPI App & Lifespan)
├── README.md                # Dokumentation
├── .gitignore
├── helper/                  # Datenbank- & Business-Logik
│   ├── __init__.py
│   ├── actionhelper.py      # Logik für Matchmaking & Kochen
│   ├── db_item.py           # CRUD für globale Zutaten
│   ├── db_pantry.py         # CRUD für Vorratsschränke
│   ├── db_recipe.py         # CRUD für Rezepte & Schritte
│   ├── db_user.py           # CRUD für User
│   └── logger.py            # Zentrales Logging-Modul
├── models/                  # Datenmodelle
│   ├── __init__.py
│   └── pydantic_models.py   # Request/Response Schemas & Validierung
├── sql_setup/               # Initialisierung
│   ├── db_setup.py          # Erstellung der Tabellenstruktur
│   └── db_init.py           # Seeding-Skript (Testdaten & Zutaten)
└── logs/                    # Automatisch generierte Logs
│   ├── api_access.log
│   ├── cloud_cookbook.log
│   └── sql_audit.log
└── assets/                  # Assets für die Readme
```
## Features

* **Smart Matchmaking:** Der Algorithmus (actionhelper.py) analysiert den Vorratsschrank eines Benutzers und zeigt in Echtzeit an, welche Rezepte sofort gekocht werden können ("Was kann ich heute essen?").
* **"Cook It" Transaktion:** Wenn ein Nutzer ein Rezept kocht, werden die benötigten Zutaten automatisch und atomar aus dem Vorratsschrank abgezogen.
* **Rezept-Management:** Erstellen, Abrufen und Aktualisieren von Rezepten inklusive detaillierter Schritt-für-Schritt-Anleitungen und Zutatenlisten.
* **Pantry-Management:** Verwaltung des persönlichen Vorratsschranks eines Benutzers. Zutaten können hinzugefügt oder entfernt werden; Bestände werden automatisch bereinigt (Löschung bei Menge <= 0).
* **Globale Zutaten:** Zentrales Verzeichnis aller verfügbaren Zutaten zur Vermeidung von Redundanzen.
* **Benutzerverwaltung:** Registrierung und Profilverwaltung.
* **3-Level Logging::**
    * Application Log: Allgemeine Anwendungsereignisse und Fehler.
    * SQL Audit Log: Protokollierung aller ausgeführten SQL-Befehle zur Nachverfolgbarkeit.
    * API Access Log: Tracking von Request-Methoden, Pfaden, Statuscodes und Antwortzeiten.
* **Persistente Speicherung:** Einsatz relationaler Datenmodellierung zur dauerhaften Sicherung von Zuständen.
* **Infrastructure as Code:** Vollständige Abbildung des Deployments mittels AWS-Services.

## Technologien

* **Sprache:** Python 3.10+
* **Framework:** FastAPI
* **Server:** Uvicorn
* **Datenbank:** SQLite3
* **Validierung:** Pydantic V2

## Installation und Start

Voraussetzung ist eine installierte Python-Umgebung.

1.  **Repository klonen:**
  ```bash
  git clone <repository-url>
  cd CloudCookbook
  ```

2.  **Abhängigkeiten installieren:**

Es wird empfohlen, ein virtuelles Environment zu nutzen.

    ```bash
    pip install fastapi uvicorn
    ```

3.  **Server starten:**
  Starten Sie den Uvicorn-Server im Terminal:
  ```bash
  uvicorn main:app --reload
  ```
  Der Server läuft standardmäßig unter `http://127.0.0.1:8000`.
  
## API Dokumentation
Nach dem Start des Servers ist die automatisch generierte Swagger-UI unter folgender URL erreichbar:
`http://127.0.0.1:8000/docs`

### Endpunkte Übersicht

#### 1. Rezepte (Recipes)

| Methode | Pfad | Beschreibung |
| :--- | :--- | :--- |
| `POST` | `/recipes` | Erstellt ein neues Rezept inkl. Zutaten und Schritten. |
| `GET` | `/recipes` | Ruft eine Liste aller Rezepte (Zusammenfassung) ab. |
| `GET` | `/recipes/{recipe_id}` | Ruft ein einzelnes Rezept mit allen Details ab. |
| `PUT` | `/recipes/{recipe_id}` | Aktualisiert ein bestehendes Rezept vollständig. |

#### 2. Vorratsschrank (Pantry)

| Methode | Pfad | Beschreibung |
| :--- | :--- | :--- |
| `GET` | `/pantry/{uid}` | Zeigt den aktuellen Inhalt des Vorratsschranks eines Benutzers. |
| `POST` | `/pantry/{uid}` | Fügt Zutaten hinzu oder entfernt sie (Action: add/remove). |
| `DELETE`| `/pantry/{uid}` | Löscht eine Zutat vollständig, oder nur menge X, aus dem Vorratsschrank. |

#### 3. Zutaten (Items)

| Methode | Pfad | Beschreibung |
| :--- | :--- | :--- |
| `GET` | `/items/{item_id}` | Gibt den Namen einer Zutat anhand der ID zurück. |
| `GET` | `/items/search/{name}` | Sucht die ID einer Zutat anhand des Namens. |
| `POST` | `/items` | Erstellt eine neue globale Zutat. |

#### 4. Benutzer (Users)

| Methode | Pfad | Beschreibung |
| :--- | :--- | :--- |
| `POST` | `/users` | Registriert einen neuen Benutzer. |
| `GET` | `/users/{uid}` | Ruft Benutzerdaten anhand der ID ab. |
| `GET` | `/users/search/{username}` | Sucht einen Benutzer anhand des Namens. |
| `PUT` | `/users/{uid}` | Aktualisiert Benutzerdaten. |

#### 5. Matchmaking
| Methode | Pfad | Beschreibung |
| :--- | :--- | :--- |
| `GET` | `/matchmaking/{uid}` | Zeigt alle Rezepte an, für die der User alle Zutaten besitzt. |
| `POST` | `/cook/{uid}/{recipe_id}` | "Kocht" das Rezept: Prüft Bestand und bucht Zutaten vom Vorrat ab |
---

## Beispiel Requests

### Prüfen, was UID 1 kochen kann

**Endpoint:** `GET /matchmaking/1`

| Beispiel Schema | Ausgefülltes Schema für UID 1 |
| :--- | :--- |
|**"recipe_id":** 0,<br> **"recipe_name":** "string",<br> **"description":** "string",<br> **"recipe_creator":** 0,<br> **"time_needed":** 0|**"recipe_id":** 4,<br> **"recipe_name":** "caprese salad",<br> **"description":** "Fresh Italian summer salad.",<br> **"recipe_creator":** 1,<br> **"time_needed":** 10<br>|

```
**Response Body(JSON):** 
```json
[
  {
    "recipe_id": 1,
    "recipe_name": "classic pancakes",
    "description": "Fluffy sunday breakfast pancakes. (Single Portion)",
    "recipe_creator": 2,
    "time_needed": 20
  }
]
```

### Ein neues Rezept erstellen
**Endpoint:** `POST /recipes`

**Request Body (JSON):**
| Beispiel Schema | Ausgefülltes Schema (Mushroom Stew) |
| :--- | :--- |
|**"recipe_name":** "string",<br> **"description":** "string",<br> **"recipe_creator":** 0,<br> **"time_needed":** 0,<br> **"recipe_ingredients"**: {<br> **"ingredient_name":** 0<br> },<br> **"instructions":** [<br> "string"]|**"recipe_name":** "Mushroom Stew",<br> **"description":** "Ein deftiger Eintopf für kalte Tage.",<br> **"recipe_creator":** 1,<br> **"time_needed":** 45,<br> **"recipe_ingredients":** {<br> "mushrooms": 500,<br> "heavy cream": 200,<br> "onion": 1},<br> **"instructions":** [<br> "Slice the vegetables",<br> "Sauté onions and mushrooms",<br> "Add cream and simmer" ]|

**Request Body (JSON):**
```json
{
  "message": "Recipe created",
  "recipe_id": 5
}
```

### Vorratsschrank aktualisieren

**Endpoint:** `POST /pantry/1`

**Request Body (JSON):**
| Beispiel Schema | Ausgefülltes Schema (Add Rice) |
| :--- | :--- |
|**"ingredient_name":** "string",<br> **"amount":** 500,<br> **"action":** "add" | **"ingredient_name":** "Rice",<br> **"amount":** 1000,<br> **"action":** "add" |

**Response (200 OK):**
```json
{
  "message": "Pantry updated: add 1000 Rice"
}
```

## Logging

Das System erstellt automatisch Protokolldateien im Root-Verzeichnis der Anwendung, um den Betrieb zu überwachen:
 * **cloud_cookbook.log:**<br>Enthält Debug-Informationen und allgemeine Ablaufprotokolle.
 * **sql_audit.log:**<br>Enthält die Raw-SQL Queries und Parameter für Auditing-Zwecke.
 * **api_access.log:**<br>Enthält Performance-Metriken (Dauer, Status, Pfad) aller HTTP-Requests.
