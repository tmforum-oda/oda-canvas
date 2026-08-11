# OAuth2 Authentifizierung für Component Registry

## Übersicht

Die Component Registry API unterstützt nun OAuth2-Authentifizierung mit JWT-Tokens für alle Endpunkte.

## Features

- ✅ OAuth2 Password Flow (Bearer Token)
- ✅ JWT Token-basierte Authentifizierung
- ✅ Konfigurierbares Token-Ablaufdatum
- ✅ Optional aktivierbar/deaktivierbar
- ✅ Alle Resource- und Hub-Endpunkte geschützt
- ✅ Health- und Dashboard-Endpunkte bleiben öffentlich

## Konfiguration

### Umgebungsvariablen

Erstellen oder aktualisieren Sie die `.env` Datei:

```env
# OAuth2 aktivieren/deaktivieren
OAUTH2_ENABLED=false

# Secret Key für JWT-Token-Signierung
# Generieren Sie einen sicheren Schlüssel mit: openssl rand -hex 32
OAUTH2_SECRET_KEY=09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7

# JWT-Algorithmus
OAUTH2_ALGORITHM=HS256

# Token-Gültigkeit in Minuten
OAUTH2_ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Sicheren Secret Key generieren

```bash
openssl rand -hex 32
```

## Standard-Benutzer

Für Testzwecke ist ein Standard-Benutzer vorkonfiguriert:

- **Username**: `admin`
- **Password**: `secret`
- **Hashed Password**: `$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW`

> ⚠️ **WICHTIG**: Ändern Sie diese Credentials in Produktion!

## Verwendung

### 1. Authentifizierung aktivieren

```bash
# In .env Datei
OAUTH2_ENABLED=true
```

### 2. Token abrufen

**HTTP Request:**
```http
POST /token HTTP/1.1
Host: localhost:8080
Content-Type: application/x-www-form-urlencoded

username=admin&password=secret
```

**cURL Beispiel:**
```bash
curl -X POST "http://localhost:8080/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=secret"
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTcwMDAwMDAwMH0.signature",
  "token_type": "bearer"
}
```

### 3. API mit Token aufrufen

**HTTP Request:**
```http
GET /resource HTTP/1.1
Host: localhost:8080
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**cURL Beispiel:**
```bash
# Token in Variable speichern
TOKEN=$(curl -s -X POST "http://localhost:8080/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=secret" | jq -r '.access_token')

# API aufrufen
curl -X GET "http://localhost:8080/resource" \
  -H "Authorization: Bearer $TOKEN"
```

**Python Beispiel:**
```python
import requests

# Token abrufen
token_response = requests.post(
    "http://localhost:8080/token",
    data={"username": "admin", "password": "secret"}
)
token = token_response.json()["access_token"]

# API mit Token aufrufen
headers = {"Authorization": f"Bearer {token}"}
response = requests.get("http://localhost:8080/resource", headers=headers)
print(response.json())
```

## Geschützte Endpunkte

Folgende Endpunkte benötigen Authentifizierung (wenn `OAUTH2_ENABLED=true`):

### Resource-Endpunkte
- `GET /resource` - Liste aller Ressourcen
- `POST /resource` - Ressource erstellen
- `GET /resource/{id}` - Ressource abrufen
- `PATCH /resource/{id}` - Ressource aktualisieren
- `DELETE /resource/{id}` - Ressource löschen

### Hub-Endpunkte (Event Subscriptions)
- `POST /hub` - Hub registrieren
- `GET /hub` - Alle Hubs auflisten
- `GET /hub/{id}` - Hub abrufen
- `DELETE /hub/{id}` - Hub löschen

## Öffentliche Endpunkte

Diese Endpunkte sind immer ohne Authentifizierung zugänglich:

- `GET /health` - Health Check
- `GET /` - Dashboard (HTML)
- `POST /sync` - Synchronisations-Callback
- `GET /docs` - Swagger UI
- `GET /redoc` - ReDoc API-Dokumentation

## Swagger UI Integration

Die Swagger UI unter `/docs` unterstützt OAuth2-Authentifizierung:

1. Öffnen Sie `http://localhost:8080/docs`
2. Klicken Sie auf den "Authorize" Button
3. Geben Sie Username und Password ein
4. Klicken Sie auf "Authorize"
5. Alle API-Aufrufe verwenden nun automatisch den Token

## Fehlerbehandlung

### 401 Unauthorized

```json
{
  "detail": "Not authenticated"
}
```

**Ursachen:**
- Kein Token im Authorization-Header
- Token ist abgelaufen
- Token ist ungültig

**Lösung:** Neuen Token abrufen

### 403 Forbidden

```json
{
  "detail": "Inactive user"
}
```

**Ursachen:**
- Benutzer ist deaktiviert

## Benutzer verwalten

Aktuell werden Benutzer in der `auth.py` Datei in einem Dictionary gespeichert:

```python
fake_users_db = {
    "admin": {
        "username": "admin",
        "full_name": "Administrator",
        "email": "admin@example.com",
        "hashed_password": "$2b$12$...",
        "disabled": False,
    }
}
```

### Neues Passwort hashen

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
hashed = pwd_context.hash("your-password")
print(hashed)
```

### Neuen Benutzer hinzufügen

```python
"newuser": {
    "username": "newuser",
    "full_name": "New User",
    "email": "newuser@example.com",
    "hashed_password": "$2b$12$...",  # Generiertes Hash
    "disabled": False,
}
```

## Produktionsempfehlungen

1. **Sicheren Secret Key verwenden**
   ```bash
   OAUTH2_SECRET_KEY=$(openssl rand -hex 32)
   ```

2. **HTTPS verwenden**
   - Tokens sollten nur über HTTPS übertragen werden
   - Verwenden Sie einen Reverse Proxy (nginx, traefik)

3. **Token-Ablaufzeit anpassen**
   ```bash
   OAUTH2_ACCESS_TOKEN_EXPIRE_MINUTES=15
   ```

4. **Echte Datenbank verwenden**
   - Ersetzen Sie `fake_users_db` durch eine echte Datenbank
   - Speichern Sie Benutzer in PostgreSQL, MySQL, etc.

5. **Rate Limiting hinzufügen**
   - Beschränken Sie Token-Anfragen pro IP
   - Verwenden Sie Tools wie `slowapi`

6. **Logging aktivieren**
   - Loggen Sie fehlgeschlagene Authentifizierungsversuche
   - Überwachen Sie verdächtige Aktivitäten

## Deaktivierung für Entwicklung

Für lokale Entwicklung können Sie OAuth2 deaktivieren:

```bash
# In .env
OAUTH2_ENABLED=false
```

Alle Endpunkte sind dann ohne Authentifizierung zugänglich.

## Troubleshooting

### Token wird nicht akzeptiert

1. Prüfen Sie, ob `OAUTH2_ENABLED=true` gesetzt ist
2. Stellen Sie sicher, dass der Token nicht abgelaufen ist
3. Überprüfen Sie den Authorization-Header: `Authorization: Bearer <token>`

### "Module not found: jose"

```bash
pip install python-jose[cryptography]==3.3.0 bcrypt
```

### Secret Key geändert, alte Tokens ungültig

Wenn Sie den `OAUTH2_SECRET_KEY` ändern, werden alle bestehenden Tokens ungültig. Benutzer müssen sich neu authentifizieren.

## Technische Details

- **Framework**: FastAPI OAuth2PasswordBearer
- **Token-Typ**: JWT (JSON Web Tokens)
- **Algorithmus**: HS256 (HMAC with SHA-256)
- **Passwort-Hashing**: bcrypt
- **Token-Speicherung**: Client-seitig (kein Server-State)

## Weitere Informationen

- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
- [OAuth2 Specification](https://oauth.net/2/)
- [JWT Introduction](https://jwt.io/introduction)
