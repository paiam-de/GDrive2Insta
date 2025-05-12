import os
import time
import json
import logging
from instagrapi import Client
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from instagrapi.exceptions import LoginRequired
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Constants
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
FOLDER_NAME = os.getenv("FOLDER_NAME", "Nikon")
LOG_FILE = os.getenv("LOG_FILE", "uploaded_files.json")
SESSION_FILE = os.getenv("SESSION_FILE", "insta_session.json")
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "client_secret.json")

INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME")
INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD")

# Configure the logging system
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def authenticate():
    """Authenticate and return Google Drive API credentials."""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    else:
        flow = InstalledAppFlow.from_client_secrets_file(GOOGLE_CREDENTIALS_PATH, SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def get_folder_id(service, folder_name):
    response = service.files().list(
        q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'",
        spaces='drive',
        fields='files(id, name)',
    ).execute()
    folders = response.get('files', [])
    if not folders:
        raise Exception(f"Folder '{folder_name}' not found.")
    return folders[0]['id']

def list_files_in_folder(service, folder_id):
    results = service.files().list(
        q=f"'{folder_id}' in parents and mimeType contains 'image/'",
        fields="files(id, name)"
    ).execute()
    return results.get('files', [])

def load_uploaded_log():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r') as f:
            return set(json.load(f))
    return set()

def save_uploaded_log(file_ids):
    with open(LOG_FILE, 'w') as f:
        json.dump(list(file_ids), f)

def initialize_instagram_session():
    client = Client()
    if os.path.exists(SESSION_FILE):
        client.load_settings(SESSION_FILE)
        try:
            client.get_user_info(client.user_id)
            logging.info("Loaded session and logged in successfully.")
        except Exception:
            logging.warning("Session expired, logging in again.")
            client.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
    else:
        logging.info("Logging in to Instagram for the first time.")
        client.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
    client.dump_settings(SESSION_FILE)
    return client

def upload_to_instagram(client, image_path):
    try:
        client.photo_upload(image_path, caption="Uploaded from Google Drive folder!")
        logging.info(f"Uploaded {image_path} to Instagram.")
    except Exception as e:
        logging.error(f"Upload failed: {e}")
        raise

def retry_with_backoff(func, retries=5):
    delay = 1
    for attempt in range(retries):
        try:
            return func()
        except Exception as e:
            logging.error(f"Retry {attempt+1}: {e}, retrying in {delay}s...")
            time.sleep(delay)
            delay *= 2
            if attempt == retries - 1:
                raise

def main_loop():
    creds = authenticate()
    service = build('drive', 'v3', credentials=creds)
    folder_id = get_folder_id(service, FOLDER_NAME)
    uploaded_ids = load_uploaded_log()
    instagram_client = initialize_instagram_session()

    while True:
        try:
            logging.info("Checking for new photos...")
            files = list_files_in_folder(service, folder_id)
            new_files = [f for f in files if f['id'] not in uploaded_ids]

            for file in new_files:
                file_id = file['id']
                file_name = file['name']
                try:
                    request = service.files().get_media(fileId=file_id)
                    file_path = f"./{file_name}"
                    with open(file_path, 'wb') as f:
                        downloader = service._http.request
                        resp, content = downloader(request.uri)
                        f.write(content)

                    logging.info(f"Downloaded {file_name}")
                    retry_with_backoff(lambda: upload_to_instagram(instagram_client, file_path))
                    uploaded_ids.add(file_id)
                    save_uploaded_log(uploaded_ids)

                except Exception as e:
                    logging.error(f"Failed {file_name}: {e}")
                    continue

            time.sleep(300)  # Check every 5 minutes

        except LoginRequired:
            logging.warning("Re-authenticating Instagram session...")
            instagram_client.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
            instagram_client.dump_settings(SESSION_FILE)
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            time.sleep(60)

if __name__ == '__main__':
    main_loop()
