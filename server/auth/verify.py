from fastapi import FastAPI, HTTPException, status, Request, Response
import jwt
from jwt import InvalidTokenError
import os, time
from cryptography.hazmat.primitives import serialization

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
        print("token is ", token)

    if not token:
        return Response(status_code=401)

    try:
        # Verify and Decode
        decoded_payload = jwt.decode(
            token, 
            public_key, 
            algorithms=["RS256"]
        )
    
        print("Token is valid!")
        print(f"User ID: {decoded_payload.get('sub')}")
        print(f"Role: {decoded_payload.get('role')}")

    except jwt.ExpiredSignatureError:
        print("Security Alert: The QR code/token has expired.")
        raise HTTPException(status_code=401, detail="Token is invalid")
    except jwt.InvalidTokenError:
        print("Security Alert: Invalid signature or corrupted token.")
        raise HTTPException(status_code=401, detail="Token is invalid")

    return Response(status_code=200)
