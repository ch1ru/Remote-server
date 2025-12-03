from fastapi import FastAPI, Request, Response
import jwt
from jwt import InvalidTokenError
import os, time

app = FastAPI()

PUBLIC_KEY_PATH = "/public_keys/device_public.pem"  # mount your public key here
with open(PUBLIC_KEY_PATH, "rb") as f:
    public_key = f.read()

@app.get("/verify")
async def verify(request: Request):
    token = None
    # Prefer Authorization header
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth.split(None, 1)[1]
    else:
        # fallback to query param
        token = request.query_params.get("token")

    if not token:
        return Response(status_code=401)

    try:
        SECRET = os.getenv('JWS_SECRET').encode("utf-8")
        payload = jwt.decode(token, SECRET, algorithms=["HS256"], audience="igv-access")
    except InvalidTokenError:
        return Response(status_code=401)

    # Optional: Check expiry, issuer, scope, etc.
    if payload.get("exp", 0) < time.time():
        return Response(status_code=401)

    return Response(status_code=200)
