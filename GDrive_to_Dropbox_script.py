import time
import io
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.http import MediaIoBaseDownload
from dropbox import Dropbox, exceptions
from dropbox.files import WriteMode

# Authenticate with Google Drive using OAuth 2.0
SCOPES = ['https://www.googleapis.com/auth/drive']
flow = InstalledAppFlow.from_client_secrets_file(r'Your client secret path', SCOPES)    #Copy client secret path
credentials = flow.run_local_server()
drive_service = build('drive', 'v3', credentials=credentials)

# Authenticate with Dropbox using access token
dropbox_access_token = 'Dropbox access token'    #Copy your Dropbox access token
dbx = Dropbox(dropbox_access_token)

def copy_new_files():
    while True:
        # Check for new files in Google Drive folder
        folder_id = 'Google Drive folder ID'     #Copy your Google Drive folder ID
        results = drive_service.files().list(q=f"'{folder_id}' in parents and trashed=false",
                                              fields="files(id, name, mimeType)").execute()
        files = results.get('files', [])

        for file in files:
            file_id = file.get('id')
            file_name = file.get('name')
            mime_type = file.get('mimeType')

            # Append the correct extension to the filename for Google Docs and Google Sheets files
            if mime_type == "application/vnd.google-apps.document":
                file_name += ".docx"
            elif mime_type == "application/vnd.google-apps.spreadsheet":
                file_name += ".xlsx"

            # If the file doesn't exist, copy it from Google Drive to Dropbox
            try:
                print(f"Copying file '{file_name}' from Google Drive to Dropbox...")
                
                if mime_type == "application/vnd.google-apps.document":
                    request = drive_service.files().export_media(fileId=file_id, mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
                elif mime_type == "application/vnd.google-apps.spreadsheet":
                    request = drive_service.files().export_media(fileId=file_id, mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                else:
                    request = drive_service.files().get_media(fileId=file_id)

                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                fh.seek(0)
                dbx.files_upload(fh.read(), "/" + file_name, mode=WriteMode('overwrite'))
                print(f"File '{file_name}' copied to Dropbox.")
            except exceptions.ApiError as e:
                if isinstance(e.error.get_path(), dropbox.files.WriteError):
                    print(f"Conflict with file '{file_name}' in Dropbox.")
                else:
                    raise e

        # Check for new files every 5 minutes

        time.sleep(300)

if __name__ == "__main__":
    copy_new_files()
