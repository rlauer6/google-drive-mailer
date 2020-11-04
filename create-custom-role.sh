#!/bin/bash
# -*- mode: sh -*-

# Example script to create a role for the Lambda to assume that allows
# access to the mail bucket, creation of CloudWatch logs and the SSM
# key that holds credentials

# create-role.sh policy-name role-name bucket ssm-key region
# Example:
#          create-role.sh google-drive-mailer-policy google-drive-mailer-role google-drive-mailer /google/google-drive-mailer us-east-1


function usage() {
    cat <<EOF
usage $0 options

EOF
    exit 0;
}

function create_policy() {

    POLICY=$(mktemp)

    cat >$POLICY <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject"
            ],
            "Resource": [
                "arn:aws:s3:::$BUCKET_NAME/*"
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
                "arn:aws:ssm:us-east-1:$ACCOUNT:parameter$SSM_KEY"
            ]
        },
        {
            "Effect": "Allow",
            "Action": "kms:Decrypt",
            "Resource": "arn:aws:kms:us-east-1:$ACCOUNT:key/*"
        }
    ]
}
EOF

    ASSUME_ROLE_POLICY=$(mktemp)

    cat >$ASSUME_ROLE_POLICY <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
EOF

    cat $POLICY

    $DRYRUN aws iam create-policy --policy-name=$POLICY_NAME \
        --policy-document=file://$POLICY

    rm $POLICY
    rm $ASSUME_ROLE_POLICY
}

function attach_policy() {
    $DRYRUN aws iam attach-role-policy --role-name $ROLE_NAME \
        --policy-arn arn:aws:iam::$ACCOUNT:policy/$POLICY_NAME
}

function create_role() {
    create_policy

    $DRYRUN aws iam create-role --role-name $ROLE_NAME \
        --assume-role-policy file://$ASSUME_ROLE_POLICY

    attach_policy
}


# +-------------------------+
# | MAIN SCRIPT STARTS HERE |
# +-------------------------+

OPTS=$(getopt -o hvr:p:R:a:b:s:d -- "$@")

# set defaults
ACCOUNT=$(aws sts get-caller-identity | jq -r .Account)
POLICY_NAME="google-drive-mailer-policy"
ROLE_NAME="google-drive-mailer-role"

SSM_KEY="/google-drive-mailer/credentials"
REGION="us-east-1"

DEFAULT_COMMAND="create"
AWS_REGION=${AWS_REGION:-us-east-1}

if [ $? -ne 0 ]; then
    echo "could not parse options"
    exit $?
fi

eval set -- "$OPTS"

while [ $# -gt 0 ]; do
    case "$1" in
        -b)
            BUCKET_NAME="$2";
            shift;
            shift;
            ;;
	-h)
	    usage;
	    ;;
	-R)
	    AWS_REGION="$2"
	    shift;
            shift;
	    ;;
        -r)
            ROLE_NAME="$2";
            shift;
            shift;
            ;;
        -a)
            ACCOUNT="$2";
            shift;
            shift;
            ;;
        -p)
            POLICY_NAME="$2";
            shift;
            shift;
            ;;
	-v)
	    VERBOSE="-x"
	    shift;
	    ;;
	-d)
	    DRYRUN="echo"
	    shift;
	    ;;
	--)
	    break;
	    ;;
	*)
	    break;
	    ;;
    esac
done

test -n $VERBOSE && set -e $VERBOSE

shift;
command="$1"
command=${command:-$DEFAULT_COMMAND}

if [ "$command" = "create" ]; then
    create_role
fi
