# OAuth2 Authentication Setup für ComponentRegistry

## Änderungen an main.py

Die folgenden Änderungen müssen an der Datei `app/main.py` vorgenommen werden:

### 1. Token-Endpunkt hinzufügen (nach der `notify_hubs` Funktion, vor den Resource-Endpunkten):

```python
@app.post("/token", response_model=Token, tags=["authentication"])
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token login, get an access token for future requests.
    
    Use this endpoint to authenticate and receive a JWT token.
    Default credentials: username=admin, password=secret
    
    Set OAUTH2_ENABLED=true in environment to enable authentication.
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
```

### 2. Authentifizierung zu allen Endpunkten hinzufügen:

Füge zu jedem Endpunkt den Parameter hinzu:
```python
current_user: User = Depends(get_current_active_user)
```

Oder für optionale Authentifizierung:
```python
current_user: User = Depends(optional_auth)
```

#### Beispiel für list_resources:
```python
async def list_resources(
    offset: Optional[int] = 0,
    limit: Optional[int] = 100,
    fields: Optional[str] = None,
    filter: Optional[str] = None,
    request: Request = None,
    response: Response = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)  # NEU
):
```

### 3. Umgebungsvariablen

Erstelle oder aktualisiere die `.env` Datei:

```
# OAuth2 Configuration
OAUTH2_ENABLED=false
OAUTH2_SECRET_KEY=your-secret-key-change-in-production-use-openssl-rand-hex-32
OAUTH2_ALGORITHM=HS256
OAUTH2_ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Verwendung

### Authentifizierung deaktiviert (Standard):
```bash
OAUTH2_ENABLED=false
```
Alle Endpunkte sind ohne Authentifizierung zugänglich.

### Authentifizierung aktiviert:
```bash
OAUTH2_ENABLED=true
```

1. Token abrufen:
```bash
curl -X POST "http://localhost:8080/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=secret"
```

Antwort:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

2. API mit Token aufrufen:
```bash
curl -X GET "http://localhost:8080/resource" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

## Standard-Benutzer

- Username: `admin`
- Password: `secret`

Ändern Sie das Passwort in Produktion!
