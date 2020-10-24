# https://developers.google.com/drive/api/v3/quickstart/python

from utils.aws import *
from utils.google_drive import *

import io
import sys
import json
import os.path

def getCredentialFromFile(path):
    with open(path, "r") as fh:
        keyfile_dict = json.loads(fh.read())

    return keyfile_dict

def getCredentialsFromSSM(path):
    ssm = SSM_Parameters()
    parameter = ssm.get_parameter(name='/google/foo')
    if parameter:
        return json.loads(parameter["Value"])
    else:
        return None


# +-------------------------+
# | MAIN SCRIPT STARTS HERE |
# +-------------------------+

def main():
    keyfile_dict = getCredentialsFromSSM('/google/foo')
    service = authServiceAccount(scopes=['https://www.googleapis.com/auth/drive'],
                                     keyfile_dict=keyfile_dict)

    #files = listFiles(service=service)
    #files = listFiles(service=service, folder_name='211 Southgate')
    top_level = findSharedFolderId(folder_name = '211 Southgate', service=service)
    print(top_level)

    sub_folder_id = findSharedFolderId(folder_name='Insurance', parents=[top_level], service=service)
    print(sub_folder_id)

    files = listFiles(service=service, folder_id=sub_folder_id)

    for item in files:
        print("id: {}, name: {} mimeType: {}".format(item['id'], item['name'], item['mimeType']))

        if False:
            file_id = uploadFile(filename="foo", mimetype="text/plain", service=service, folder_name="211 Southgate")
            print("file id: {}".format(file_id))

if __name__ == "__main__":

    main()
