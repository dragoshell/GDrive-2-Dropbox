import time
import io
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.http import MediaIoBaseDownload
from dropbox import Dropbox, exceptions
from dropbox.files import WriteMode

# Authenticate with Google Drive using OAuth 2.0
SCOPES = ['https://www.googleapis.com/auth/drive']
flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
credentials = flow.run_local_server()
drive_service = build('drive', 'v3', credentials=credentials)

# Authenticate with Dropbox using access token
dropbox_access_token = "your_dropbox_access_token"  # Replace with your actual access token
dbx = Dropbox(dropbox_access_token)

def copy_new_files():
    while True:
        # Check for new files in Google Drive folder
        folder_id = 'your_folder_id'  # Replace with the actual folder ID
        results = drive_service.files().list(q=f"'{folder_id}' in parents and trashed=false",
                                              fields="files(id, name, mimeType)").execute()
        files = results.get('files', [])

        for file in files:
            file_id = file.get('id')
            file_name = file.get('name')
            mime_type = file.get('mimeType')

            # Check if the file exists in Dropbox
            try:
                dbx.files_get_metadata("/Apps/" + file_name)
                print(f"File '{file_name}' already exists in Dropbox.")
            except exceptions.ApiError as e:
                print(f"Error fetching metadata for file '{file_name}': {e}")
                # If the file doesn't exist, copy it from Google Drive to Dropbox
                print(f"Copying file '{file_name}' from Google Drive to Dropbox...")
                
                if mime_type == "application/vnd.google-apps.document":
                    request = drive_service.files().export_media(fileId=file_id, mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
                    file_name += ".docx"
                elif mime_type == "application/vnd.google-apps.spreadsheet":
                    request = drive_service.files().export_media(fileId=file_id, mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                    file_name += ".xlsx"
                else:
                    request = drive_service.files().get_media(fileId=file_id)

                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                fh.seek(0)
                dbx.files_upload(fh.read(), "/" + file_name, mode=WriteMode.add)
                print(f"File '{file_name}' copied to Dropbox.")

        # Check for new files every 5 minutes
        time.sleep(300)

if __name__ == "__main__":
    copy_new_files()
