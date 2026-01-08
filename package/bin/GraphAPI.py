import requests
import json

class EntraIDAuth:
    def __init__(self, ClientID, ClientSecret, TenantID):
        self.ClientID = ClientID
        self.ClientSecret = ClientSecret
        self.TenantID = TenantID
        self.scope = "https://graph.microsoft.com/.default"
        self.url = "https://graph.microsoft.com/"

    def getAuthToken(self):
        payload = {
            "client_id": self.ClientID,
            "client_secret": self.ClientSecret,
            "scope": self.scope,
            "grant_type": "client_credentials"
        }
        url = f"https://login.microsoftonline.com/{self.TenantID}/oauth2/v2.0/token"
        try:
            response = requests.post(url, data=payload)
            data = response.json()
        except Exception as e:
            print(e)
        
        self.token = data["access_token"]

    def listInfo(self, endpoint_version, endpoint, filter, query):
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        self.url = f"{self.url}/{endpoint_version}{endpoint}"
        try:
            response = requests.get(self.url, headers=headers)
        except Exception as e:
            print(e)
        return response



if __name__ == "__main__":

    #filter = "$select=extensionAttributes"
    filter = ""
    #filter = "$select=displayName,id,lastPasswordChangeDateTime,signInActivity"
    endpoint = "/security/secureScores"
    query = ""
    endpoint_version = "v1.0"

    test = EntraIDAuth(ClientID, ClientSecret, TenantID)
    test.getAuthToken()
    data = test.getInfo(endpoint_version, endpoint, filter, query)
    '''endpoint = "/security/secureScores/7092f324-5b8d-44e1-bb7a-4c14c647727c"
    data = test.getInfo(endpoint_version, endpoint, filter, query)'''
    data = data.json()
    with open("./test.json", 'w', encoding='utf-8') as f:
        json.dump(data['value'][0], f, ensure_ascii=False, indent=4)