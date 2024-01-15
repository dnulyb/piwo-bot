from config.settings import *
import requests
from requests.auth import HTTPBasicAuth

#TODO: implement .env saving/loading

ubi_url = "https://public-ubiservices.ubi.com/v3/profiles/sessions"
ubi_appid = "86263886-327a-4328-ac69-527f0d20a237"
nadeo_url = "https://prod.trackmania.core.nadeo.online/v2/authentication/token/ubiservices"
nadeo_refresh_url = "https://prod.trackmania.core.nadeo.online/v2/authentication/token/refresh"

def authenticate():

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

    return (access_token, refresh_token)

#not working atm
def refresh_access_token():

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

    return (access_token, refresh_token)