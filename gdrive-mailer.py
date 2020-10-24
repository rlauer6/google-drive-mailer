#!/bin/env python

from utils.aws import *
from utils.google_drive import *

import argparse
import io
import json
import os.path
import sys
import logging

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

def initLogger():
    logging.basicConfig()
    logger = logging.getLogger()

    if "LOG_LEVEL" in os.environ:
        if os.environ["LOG_LEVEL"] == "DEBUG":
            logger.setLevel(logging.DEBUG)
        elif os.environ["LOG_LEVEL"] == "INFO":
            logger.setLevel(logging.INFO)
        else:
            logger.setLevel(logging.WARNING)
                
    return logger
    
def getOptions():
    parser = argparse.ArgumentParser(description='Google Drive Mailer - email files to your Google Drive',
                                     allow_abbrev=True)
    parser.add_argument('-s', "--ssm", type=str, dest="ssm", help="SSM key for credentials")
    parser.add_argument("action", type=str, help="action (list)")
    parser.add_argument('-f', "--folder", type=str, dest="folder", help="folder name")
    parser.add_argument('-c', "--credentials", type=str, dest="credentials", help="path to credentials file")

    options = parser.parse_args()

    return options

# Google Drive Scopes
# https://www.googleapis.com/auth/drive
# https://www.googleapis.com/auth/drive.file
# https://www.googleapis.com/auth/drive.readonly
# https://www.googleapis.com/auth/drive.metadata.readonly
# https://www.googleapis.com/auth/drive.metadata
# https://www.googleapis.com/auth/drive.photos.readonly

# +-------------------------+
# | MAIN SCRIPT STARTS HERE |
# +-------------------------+

def main():
    options = getOptions()
    
    if options.action == 'list':
        folder_name = options.folder
        
        if options.credentials:
            path = options.credentials
            keyfile_dict = getCredentialsFromFile(path)
        elif options.ssm:
            path = options.ssm
            keyfile_dict = getCredentialsFromSSM(path)
        else:
            print("ERROR: no credentials provided.  Use -s or -c to specify credential path.")
            sys.exit(-1)

        service = authServiceAccount(scopes=['https://www.googleapis.com/auth/drive.readonly'],
                                     keyfile_dict=keyfile_dict)
        del keyfile_dict
        
        files = listFiles(service=service, folder_name=folder_name)

        for item in files:
            print("id: {}, name: {} mimeType: {}".format(item['id'], item['name'], item['mimeType']))

# files = listFiles(service=service)
#     top_level = findSharedFolderId(folder_name=folder_name, service=service)
#     print(top_level)
# 
#     sub_folder_id = findSharedFolderId(folder_name='Insurance', parents=[top_level], service=service)
#     print(sub_folder_id)
#    files = listFiles(service=service, folder_id=sub_folder_id)

# file_id = uploadFile(filename="foo", mimetype="text/plain", service=service, folder_name="211 Southgate")
# print("file id: {}".format(file_id))

if __name__ == "__main__":

    main()
