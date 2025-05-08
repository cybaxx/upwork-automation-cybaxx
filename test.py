from configobj import ConfigObj
import requests
import time
from datetime import datetime, timedelta


class UpworkAuth:
    def __init__(self, config_path='config.ini'):
        self.config_path = config_path
        self.config = ConfigObj(config_path)
        self.client_id = self.config['upwork']['client_id']
        self.client_secret = self.config['upwork']['client_secret']
        self.redirect_uri = self.config['upwork']['redirect_uri']
        self.auth_code = self.config['upwork'].get('auth_code')
        self.access_token = self.config['upwork'].get('access_token')
        self.refresh_token = self.config['upwork'].get('refresh_token')
        self.expires_at = float(self.config['upwork'].get('expires_at', 0))
        self.token_url = 'https://www.upwork.com/api/v3/oauth2/token'

    def save_tokens(self, access_token, refresh_token, expires_in):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expires_at = time.time() + expires_in  # Store as UNIX timestamp

        self.config['upwork']['access_token'] = access_token
        self.config['upwork']['refresh_token'] = refresh_token
        self.config['upwork']['expires_at'] = str(self.expires_at)
        self.config.write()

    def get_authorization_url(self):
        return (
            f"https://www.upwork.com/ab/account-security/oauth2/authorize"
            f"?client_id={self.client_id}&response_type=code&redirect_uri={self.redirect_uri}"
        )

    def login_with_credentials(self):
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

        self.save_tokens(
            tokens['access_token'],
            tokens['refresh_token'],
            tokens.get('expires_in', 3600)
        )

        print("Login successful. Access token obtained.")

    def refresh_access_token(self):
        if not self.refresh_token:
            raise ValueError("No refresh token available. Please login again.")

        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }

        response = requests.post(self.token_url, data=data)
        response.raise_for_status()
        tokens = response.json()

        self.save_tokens(
            tokens['access_token'],
            tokens.get('refresh_token', self.refresh_token),
            tokens.get('expires_in', 3600)
        )

        print("Access token refreshed.")

    def is_token_expired(self, buffer_seconds=60):
        return time.time() > (self.expires_at - buffer_seconds)

    def ensure_token_valid(self):
        if not self.access_token or self.is_token_expired():
            print("Access token expired or about to expire. Refreshing...")
            self.refresh_access_token()

    def search_jobs(self, query="DevOps"):
        self.ensure_token_valid()

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
        self.ensure_token_valid()

        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }

        api_url = 'https://www.upwork.com/api/v3/profile/clients/me'
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        return response.json()
