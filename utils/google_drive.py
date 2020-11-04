from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload, MediaFileUpload

# https://developers.google.com/analytics/devguides/config/mgmt/v3/quickstart/service-py
from apiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
import io

def authServiceAccount(**kwargs):
    scopes = kwargs.get('scopes')
    keyfile_dict = kwargs.get('keyfile_dict')

    credentials = ServiceAccountCredentials.from_json_keyfile_dict(
        keyfile_dict, scopes=scopes)

    # https://developers.google.com/drive/api/v3/quickstart/python
    return build('drive', 'v3', credentials=credentials, cache_discovery=False)

def deleteFile(**kwargs):
    file_id = kwargs.get('file_id')
    service = kwargs.get('service')
    name = kwargs.get('name')
    folder_name = kwargs.get('folder_name')

    folder_id = kwargs.get('folder_id')
    if folder_id == None and folder_name:
        folder_id = findSharedFolderId(folder_name=folder_name, service=service)

    query="name=\"{}\" and parents in \"{}\"".format(name, folder_id)

    results = service.files().list(q=query).execute()
    file_id = None

    for item in results.get('files', []):
        file_id = item.get('id')

    print(file_id)
    # service.files().delete(fileId=file_id)

def findSharedFolderId(**kwargs):
    folder_name = kwargs.get('folder_name')
    service = kwargs.get('service')
    parents = kwargs.get('parents')

    query="name=\"{}\" and mimeType=\"application/vnd.google-apps.folder\"".format(folder_name)
    if parents and len(parents):
        query = query + " and parents in \"" + "\",\"".join(parents) + '"'

    results = service.files().list(q=query).execute()

    folder_id = None
    for item in results.get('files', []):
        folder_id = item.get('id')

    return folder_id

def uploadBytes(**kwargs):
    content = kwargs.get("content")
    filename = kwargs.get("filename")
    folder_name = kwargs.get("folder_name")
    service = kwargs["service"]

    folder_id = findSharedFolderId(folder_name=folder_name, service=service)

    meta_data = { "name": filename, "parents": [folder_id] }

    fh = io.BytesIO(content)
    media_body = MediaIoBaseUpload(fh, mimetype="", chunksize=1024*1024, resumable=True)
    return service.files().create(body=meta_data, media_body=media_body).execute()

def uploadFile(**kwargs):

    service = kwargs.get("service")
    path = kwargs.get("path")
    name = kwargs.get("name")
    folder_name = kwargs.get("folder_name")
    mimetype = kwargs.get("mimetype")

    folder_id = findSharedFolderId(service=service, folder_name=folder_name)

    if folder_id:
        file_metadata = { "name": name, "parents":[folder_id] }
    else:
        raise Exception

    media = MediaFileUpload(path, mimetype=mimetype)

    file = service.files().create(body=file_metadata,
                                        media_body=media,
                                        fields="id").execute()


    # For consumer (gmail) accounts it is not possible to transfer ownership
    # for a non-Google mimeType from the service account to the user.

    # https://developers.google.com/drive/api/v3/shared-drives-diffs
    # ... Files within a shared drive are owned by the shared drive, not individual users.
    #
    # no need for file to be owned by folder owner then

    return file.get("id")

def getFolders(**kwargs):
    service = kwargs.get("service")

    query="mimeType=\"application/vnd.google-apps.folder\" and trashed=false"
    results = service.files().list(q=query, fields="files(id,name,parents)").execute()

    return results.get("files", [])

def downloadFile(**kwargs):
    file_id = kwargs.get("id")
    service = kwargs.get("service")
    filename = kwargs.get("filename")
    verbose = kwargs.get("verbose")

    request = service.files().get_media(fileId=file_id)
    fh = io.FileIO(filename, mode="wb")

    downloader = MediaIoBaseDownload(fh, request, chunksize=1024*512)

    done = False

    while done is False:
        status, done = downloader.next_chunk()
        if verbose:
            print("Download {}%%.", int(status.progress() * 100))

def listFiles(**kwargs):
    service = kwargs.get("service")
    folder_name = kwargs.get("folder_name")
    folder_id = kwargs.get("folder_id")

    query = ""
    if folder_name:
        query = "parents in \"{}\"".format(findSharedFolderId(folder_name=folder_name, service=service))
    else:
        if folder_id:
            query = "parents in \"{}\"".format(folder_id)

    # Call the Drive v3 API
    page_token = None
    all_files = []
    while True:
        results = service.files().list(q=query, pageSize=5, fields="nextPageToken, files(id,name,mimeType)", pageToken=page_token).execute()
        page_token = results.get("nextPageToken")

        items = results.get("files", [])
        if len(items):
            all_files.extend(items)

        if page_token == None:
            break

    return all_files
