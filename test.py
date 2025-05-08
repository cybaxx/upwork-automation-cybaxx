from configobj import ConfigObj
import requests


class UpworkAuth:
    def __init__(self, config_path='config.ini'):
        self.config = ConfigObj(config_path)
        self.client_id = self.config['upwork']['client_id']
        self.client_secret = self.config['upwork']['client_secret']
        self.redirect_uri = self.config['upwork']['redirect_uri']
        self.auth_code = self.config['upwork'].get('auth_code')
        self.token_url = 'https://www.upwork.com/api/v3/oauth2/token'
        self.access_token = None
        self.refresh_token = None

    def get_authorization_url(self):
        auth_url = (
            f"https://www.upwork.com/ab/account-security/oauth2/authorize"
            f"?client_id={self.client_id}&response_type=code&redirect_uri={self.redirect_uri}"
        )
        return auth_url

    def login_with_credentials(self):
        """
        Simulates logging in by using stored OAuth credentials from the config file.
        This assumes the user has already obtained an authorization code manually.
        """
        if not self.auth_code:
            raise ValueError("No auth_code found in config. Visit this URL to get it:\n"
                             f"{self.get_authorization_url()}")

        data = {
            'grant_type': 'authorization_code',
            'code': self.auth_code,
            'redirect_uri': self.redirect_uri,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }

        response = requests.post(self.token_url, data=data)
        response.raise_for_status()
        tokens = response.json()
        self.access_token = tokens['access_token']
        self.refresh_token = tokens['refresh_token']
        print("Login successful. Access token obtained.")

    def search_jobs(self, query="DevOps"):
        if not self.access_token:
            raise ValueError("You must login first.")

        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }

        params = {
            'q': query
        }

        search_url = 'https://www.upwork.com/api/v3/search/jobs'
        response = requests.get(search_url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()

    def get_profile(self):
        if not self.access_token:
            raise ValueError("Access token not available. Authenticate first.")

        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }

        api_url = 'https://www.upwork.com/api/v3/profile/clients/me'
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        return response.json()

