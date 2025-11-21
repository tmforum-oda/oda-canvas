"""
Manuelle Anleitung: OAuth2-Authentifizierung zu main.py hinzufügen

SCHRITT 1: Token-Endpunkt hinzufügen
-------------------------------------
Fügen Sie diesen Code NACH der notify_hubs Funktion und VOR @app.get("/resource") ein:

"""

TOKEN_ENDPOINT = '''
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
'''

"""
SCHRITT 2: Authentifizierung zu Endpunkten hinzufügen
------------------------------------------------------
Fügen Sie zu JEDEM dieser Endpunkte den Parameter hinzu:
    current_user: User = Depends(get_current_active_user)

Betroffene Endpunkte:
"""

ENDPOINTS_TO_UPDATE = [
    "async def list_resources(...)",
    "async def create_resource(...)",
    "async def retrieve_resource(...)",
    "async def patch_resource(...)",
    "async def delete_resource(...)",
    "async def create_hub(...)",
    "async def delete_hub(...)",
]

"""
BEISPIEL - VORHER:
-----------------
async def list_resources(
    offset: Optional[int] = 0,
    limit: Optional[int] = 100,
    fields: Optional[str] = None,
    filter: Optional[str] = None,
    request: Request = None,
    response: Response = None,
    db: Session = Depends(get_db)
):

BEISPIEL - NACHHER:
------------------
async def list_resources(
    offset: Optional[int] = 0,
    limit: Optional[int] = 100,
    fields: Optional[str] = None,
    filter: Optional[str] = None,
    request: Request = None,
    response: Response = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)  # <-- NEU
):
"""

print(__doc__)
print("\nToken-Endpunkt Code:")
print(TOKEN_ENDPOINT)
print("\n" + "="*70)
print("Zu aktualisierende Endpunkte:")
for endpoint in ENDPOINTS_TO_UPDATE:
    print(f"  - {endpoint}")
