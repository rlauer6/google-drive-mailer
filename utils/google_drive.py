from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload

# https://developers.google.com/analytics/devguides/config/mgmt/v3/quickstart/service-py
from apiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials

def authServiceAccount(**kwargs):
    scopes = kwargs.get('scopes')
    keyfile_dict = kwargs.get('keyfile_dict')

    credentials = ServiceAccountCredentials.from_json_keyfile_dict(
        keyfile_dict, scopes=scopes)

    # https://developers.google.com/drive/api/v3/quickstart/python
    return build('drive', 'v3', credentials=credentials)

def findSharedFolderId(**kwargs):
    folder_name = kwargs.get('folder_name')
    service = kwargs.get('service')
    parents = kwargs.get('parents')

    query="name=\"{}\" and mimeType=\"application/vnd.google-apps.folder\"".format(folder_name)
    if parents and len(parents):
        query = query + " and parents in \"" + "\",\"".join(parents) + '"'

    print(query)
    results = service.files().list(q=query).execute()

    folder_id = None
    for item in results.get('files', []):
        folder_id = item.get('id')

    return folder_id

def uploadFile(**kwargs):

    file_id = kwargs.get('id')
    service = kwargs.get('service')
    filename = kwargs.get('filename')
    folder_name = kwargs.get('folder_name')

    mimetype = kwargs.get('mimetype')

    folder_id = findSharedFolderId(service=service, folder_name=folder_name)

    if folder_id:
        file_metadata = { 'name': filename, "parents":[folder_id] }
    else:
        raise Exception

    media = MediaFileUpload(filename, mimetype=mimetype)

    file = service.files().create(body=file_metadata,
                                        media_body=media,
                                        fields='id').execute()


    # For consumer (gmail) accounts it is not possible to transfer ownership
    # for a non-Google mimeType from the service account to the user.

    # https://developers.google.com/drive/api/v3/shared-drives-diffs
    # ... Files within a shared drive are owned by the shared drive, not individual users.
    #
    # no need for file to be owned by folder owner then

    return file.get('id')

def downloadFile(**kwargs):
    file_id = kwargs.get('id')
    service = kwargs.get('service')
    filename = kwargs.get('filename')

    request = service.files().get_media(fileId=file_id)
    fh = io.FileIO(filename, mode='wb')

    downloader = MediaIoBaseDownload(fh, request, chunksize=1024*512)

    done = False

    while done is False:
        status, done = downloader.next_chunk()
        print("Download {}%%.", int(status.progress() * 100))

def listFiles(**kwargs):
    service = kwargs.get('service')
    folder_name = kwargs.get('folder_name')
    folder_id = kwargs.get('folder_id')

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
        page_token = results.get('nextPageToken')

        items = results.get('files', [])
        if len(items):
            all_files.extend(items)

        if page_token == None:
            break

    return all_files
