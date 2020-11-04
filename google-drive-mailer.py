#!/bin/env python

from utils.aws import *
from utils.google_drive import *
from utils.email_parser import *

import argparse
import io
import json
import os.path
import sys
import logging
import tempfile

def get_files(path):
    all_files = []
    files = glob.iglob('{}/*'.format(path))
    for f in files:
        if os.path.isdir(f):
            all_files = all_files + get_files(f)
        else:
            if not ".pyc" in f:
                all_files.append(f)

    return all_files

def upload_email(**kwargs):
    message_id = kwargs.get("message_id")
    bucket = kwargs.get("bucket")
    bucket_prefix = kwargs.get("bucket_prefix")
    folder_name = kwargs.get("folder_name")
    service = kwargs.get("service")

    # read raw data from bucket (TBD: chunks)
    key = "{}/{}".format(bucket_prefix, message_id)
    logger.debug("key: {}".format(key))

    s3_obj = s3.get_object(Bucket=bucket, Key=key)
    email_body = s3_obj["Body"].read()

    files = email_parser(content=email_body)

    logger.debug(json.dumps(files))

    for f in files:
      if f["content-type"] == "application/pdf":
          file_id = uploadFile(folder_name=folder_name,
                              path=f["path"], name=f["name"], mimetype="application/pdf",
                              service=service)

          logger.debug("uploaded: {} id: {}".format(f["path"], file_id))

    return files

def getCredentialsFromFile(path):
    with open(path, "r") as fh:
        keyfile_dict = json.loads(fh.read())

    return keyfile_dict

def getCredentialsFromSSM(path):
    ssm = SSM_Parameters()
    parameter = ssm.get_parameter(name=path)
    if parameter:
        return json.loads(parameter["Value"])
    else:
        return None

def initCredentials():

    keyfile_dict = None

    if GOOGLE_DRIVE_CREDENTIALS == 'file':
        path = GOOGLE_DRIVE_CREDENTIALS
        keyfile_dict = getCredentialsFromFile(path)
    elif GOOGLE_DRIVE_CREDENTIALS == 'ssm':
        path = GOOGLE_DRIVE_CREDENTIALS_KEY
        keyfile_dict = getCredentialsFromSSM(path)
    else:
        logger.error("ERROR: no credentials provided.  Use -s or -c to specify credential path.")

    logger.debug(json.dumps(keyfile_dict))

    return keyfile_dict

def initLogger(name):

    if name == None:
        name = '__main__'

    logger = logging.getLogger(name)
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s:%(name)s:%(message)s", "%Y-%m-%d %H:%M:%S")
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(ch)

    #log_handler = logger.handlers[0]
    #log_handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s:%(name)s:%(message)s", "%Y-%m-%d %H:%M:%S"))

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
    parser.add_argument("action", type=str, help="action (list)")
    parser.add_argument('-p', "--path", type=str, dest="path", help="path to file")
    parser.add_argument('-s', "--ssm", type=str, dest="ssm", help="SSM key for credentials")
    parser.add_argument('-f', "--folder", type=str, dest="folder", help="folder name")
    parser.add_argument('-n', "--name", type=str, dest="name", help="file name")
    parser.add_argument('-c', "--credentials", type=str, dest="credentials", help="path to credentials file")
    parser.add_argument('-i', "--id", type=str, dest="id", help="folder or file id")

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

logger = initLogger('google-drive-mailer')

GOOGLE_DRIVE_CREDENTIALS = os.environ.get('GOOGLE_DRIVE_CREDENTIALS', '')
GOOGLE_DRIVE_CREDENTIALS_KEY = os.environ.get('GOOGLE_DRIVE_CREDENTIALS_KEY', '')
GOOGLE_DRIVE_FOLDER_NAME = os.environ.get('GOOGLE_DRIVE_FOLDER_NAME', '')
GOOGLE_DRIVE_SES_BUCKET_NAME = os.environ.get('GOOGLE_DRIVE_SES_BUCKET_NAME')
GOOGLE_DRIVE_SES_BUCKET_PREFIX = os.environ.get('GOOGLE_DRIVE_SES_BUCKET_PREFIX')

logger.debug("GOOGLE_DRIVE_CREDENTIALS:{}".format(GOOGLE_DRIVE_CREDENTIALS))
logger.debug("GOOGLE_DRIVE_CREDENTIALS_KEY:{}".format(GOOGLE_DRIVE_CREDENTIALS_KEY))
logger.debug("GOOGLE_DRIVE_FOLDER_NAME:{}".format(GOOGLE_DRIVE_FOLDER_NAME))
logger.debug("GOOGLE_DRIVE_SES_BUCKET_NAME:{}".format(GOOGLE_DRIVE_SES_BUCKET_NAME))
logger.debug("GOOGLE_DRIVE_SES_BUCKET_PREFIX:{}".format(GOOGLE_DRIVE_SES_BUCKET_PREFIX))

KEYFILE_DICT = initCredentials()

s3 = boto3.client('s3')

def handler(event, context):

    logger.debug(json.dumps(event))

    if KEYFILE_DICT == None:
        logger.error("ERROR: KEYFILE_DICT not available")
        return

    service = authServiceAccount(scopes=['https://www.googleapis.com/auth/drive'],
                                     keyfile_dict=KEYFILE_DICT)

    # may want to just list all files in bucket and upload each one, this way
    # if an error occurs no files get stranded.

    record = event["Records"][0]
    mail = record["ses"]["mail"]
    message_id = mail["messageId"]

    logger.debug("message id: {}".format(message_id))

    upload_email(bucket=GOOGLE_DRIVE_SES_BUCKET_NAME,
                     bucket_prefix=GOOGLE_DRIVE_SES_BUCKET_PREFIX,
                     message_id = message_id,
                     folder_name=GOOGLE_DRIVE_FOLDER_NAME,
                     service=service)

def main():
    options = getOptions()

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

    print(json.dumps(getFolders(service=service)))

    sys.exit(0)

    if options.action == 'list':
        folder_name = options.folder

        service = authServiceAccount(scopes=['https://www.googleapis.com/auth/drive.readonly'],
                                     keyfile_dict=keyfile_dict)
        del keyfile_dict

        files = listFiles(service=service, folder_name=folder_name, folder_id=options.id)

        for item in files:
            print("id: {}, name: {} mimeType: {}".format(item['id'], item['name'], item['mimeType']))

    elif options.action == 'upload':
        folder_name = options.folder
        path = options.path

        service = authServiceAccount(scopes=['https://www.googleapis.com/auth/drive'],
                                     keyfile_dict=keyfile_dict)
        del keyfile_dict

        # tbd - parse path for just filename
        file_id = uploadFile(path=path, name=path, service=service, folder_name=folder_name)
        if file_id:
            print(file_id)

    elif options.action == 'delete':
        service = authServiceAccount(scopes=['https://www.googleapis.com/auth/drive'],
                                     keyfile_dict=keyfile_dict)
        del keyfile_dict

        deleteFile(service=service, name=options.name, folder_id=options.id, folder_name=options.folder)

    elif options.action == 'rename':
        print("NOT IMPLEMENTED")

    elif options.action == 'locate':
        folder_list = options.folder.split("/")
        if len(folder_list):
            print(folder_list)

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
