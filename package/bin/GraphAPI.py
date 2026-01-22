import requests
import json

class GraphAPI:
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

    def getInfo(self, endpoint):
        headers = {
            "Authorization": f"Bearer {self.token}"
        }

        base_url = f"{self.url}{endpoint}"
        url = base_url

        all_data = []

        while url:
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()

                if 'value' in data:
                    all_data.extend(data['value'])
                else: #In case it does not have a 'value', only an object
                    all_data.append(data)
                    break

                url = data.get('@odata.nextLink')

                if not url:
                    break

            except requests.exceptions.RequestException as e:
                print(f"Error al realizar solicitud a Microsoft Graph: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    print(f"Detalle del error: {e.response.text}")
                break
            except ValueError as e:
                print("Error: Respuesta JSON inválida")
                print(response.text)
                break
            except Exception as e:
                print(f"Error inesperado: {e}")
                break

        return all_data, response.status_code