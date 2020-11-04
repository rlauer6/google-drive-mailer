# README

This is this is the README file for the `google-drive-mailer` project.

This is currently a wip...

# Overview

This project implements an AWS Lambda function that will store an
attachment sent to email address with a domain serviced by the Amazon Simple Email
Service to a Google Drive folder.

# Prerequisities

* A Google service acccount that you create in the Google console.
* A Google account with access to Google Drive
* A shared folder on the Google Drive that you shared with the service
  account

# CLI

You can use the cli version of the script to perform various actions
on your shared drive.

See `gdrive-mailer.py --help` for more info on currently implemented
actions.

# Requirements

See `requirements.txt` for a list of required Python modules.

# Setup

## Lambda Role

Create a policy that allows access to the mail bucket, SSM as well as
KMS if you are encrypting your credentials. You should also grant the
role the ability to create CloudWatch logs.

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject"
            ],
            "Resource": [
                "arn:aws:s3:::my-bucket-name/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": [
                "arn:aws:logs:*:*:*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": "ssm:Get*",
            "Resource": [
                "arn:aws:ssm:us-east-1::parameter/google-drive-mailer/credentials"
            ]
        },
        {
            "Effect": "Allow",
            "Action": "kms:Decrypt",
            "Resource": "arn:aws:kms:us-east-1::key/*"
        }
    ]
}
```

## Environment Variables

### `GOOGLE_DRIVE_CREDENTIALS`

Enum: ssm, file

`GOOGLE_DRIVE_CREDENTIALS_KEY`

*Value:* _path to SSM key_
*Example:* `/google/my-service-account-creds`

`GOOGLE_DRIVE_CREDENTIAL_FILE`

*Value:* _relative path to JSON credentials file for service account_
*Example:* `credentials.json`

If you are uploading these as part of your Lambda zip file the path
should be relative to the Lambda. It is recommended that you store
your credentials as a SecureString in SSM.

`GOOGLE_DRIVE_FOLDER_NAME`

*Value:* _name of the Google Drive folder shared with the service
account_
*Example:* My Files

`GOOGLE_DRIVE_SES_BUCKET_NAME`

*Value:* _AWS bucket name that will receive email with attachments_
*Example:* `my-bucket-name`

`GOOGLE_DRIVE_SES_BUCKET_PREFIX`

*Value:* _Prefix for bucket if any where email is placed_
*Example:* `mail`

## Amazon SES

* verify a domain to use
* setup a rule to store mail to S3 bucket that also invokes a Lambda
 

# Installation


  
  
