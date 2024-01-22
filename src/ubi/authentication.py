import requests
from requests.auth import HTTPBasicAuth
from dotenv import find_dotenv, load_dotenv, set_key
import os
import base64
import json
from datetime import datetime

ubi_url = "https://public-ubiservices.ubi.com/v3/profiles/sessions"
ubi_appid = "86263886-327a-4328-ac69-527f0d20a237"
nadeo_url = "https://prod.trackmania.core.nadeo.online/v2/authentication/token/ubiservices"
nadeo_refresh_url = "https://prod.trackmania.core.nadeo.online/v2/authentication/token/refresh"

# Authenticates with Ubisoft and stores Nadeo access token
#   in .env
def authenticate():

    dotenv_path = find_dotenv()
    load_dotenv(dotenv_path)

    user_agent = os.getenv("USER_AGENT")
    login = os.getenv("UBI_LOGIN")
    password = os.getenv("UBI_PASSWORD")

    # Get ubisoft authentication ticket
    ubi_headers = {
        'Content-Type': 'application/json',
        'Ubi-AppId': ubi_appid,
        'User-Agent': user_agent
    }
    ubi_auth = HTTPBasicAuth(login, password)

    ubi_res = requests.post(ubi_url, headers=ubi_headers, auth=ubi_auth)
    ubi_res = ubi_res.json()

    # Now we have a ticket to use for authentication to Nadeo services
    ticket = ubi_res['ticket']

    # Get nadeo access token
    
    nadeo_headers = {
        'Content-Type': 'application/json',
        'Authorization': 'ubi_v1 t=' + ticket,
        'User-Agent': user_agent
    }
    # audience NadeoServices is used by default, so no need to specify audience in request body

    nadeo_res = requests.post(nadeo_url, headers=nadeo_headers)
    nadeo_res = nadeo_res.json()

    access_token = nadeo_res['accessToken']
    refresh_token = nadeo_res['refreshToken']
    set_key(dotenv_path, "NADEO_ACCESS_TOKEN", str(access_token))
    set_key(dotenv_path, "NADEO_REFRESH_TOKEN", str(refresh_token))


# Updates the nadeo access token in .env
def refresh_access_token():

    dotenv_path = find_dotenv()
    load_dotenv(dotenv_path)

    refresh_token = os.getenv("NADEO_REFRESH_TOKEN")
    user_agent = os.getenv("USER_AGENT")

    nadeo_headers = {
        'Content-Type': 'application/json',
        'Authorization': 'nadeo_v1 t=' + refresh_token,
        'User-Agent': user_agent
    }
    # audience NadeoServices is used by default, so no need to specify audience in request body

    nadeo_res = requests.post(nadeo_refresh_url, headers=nadeo_headers)
    nadeo_res = nadeo_res.json()

    access_token = nadeo_res['accessToken']
    refresh_token = nadeo_res['refreshToken']
    set_key(dotenv_path, "NADEO_ACCESS_TOKEN", str(access_token))
    set_key(dotenv_path, "NADEO_REFRESH_TOKEN", str(refresh_token))


# Decodes the stored nadeo access token,
#   and refreshes it if needed.
def check_token_refresh():

    token = get_nadeo_access_token()

    [_, payload, _] = token.split(".")

    # payload might need padding to be able to be decoded
    if len(payload) % 4:
        payload += '=' * (4 - len(payload) % 4) 

    # decode
    decodedPayload = base64.b64decode(payload)
    jsonPayload = json.loads(decodedPayload)

    current_time = int(datetime.now().timestamp())
    expiration = jsonPayload['exp']
    #print("current: ", current_time)
    #print("expiration: ", expiration)

    refresh_possible_after = jsonPayload['rat']

    if(current_time > expiration):
        #Authentication required
        authenticate()
        print("check_token_refresh: Authenticated")
    elif(current_time > refresh_possible_after):
        #Just refresh the token
        refresh_access_token()
        print("check_token_refresh: Token refreshed")
    else:
        print("check_token_refresh: No token refresh needed")


def get_nadeo_access_token():

    dotenv_path = find_dotenv()
    load_dotenv(dotenv_path)
    return os.getenv("NADEO_ACCESS_TOKEN")