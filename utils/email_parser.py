"""Unpack a MIME message into a directory of files."""

import os
import email
import mimetypes
import tempfile
import logging

from email.policy import default
from argparse import ArgumentParser

def email_parser(**kwargs):
    content = kwargs["content"]
    temp_dir = tempfile.mkdtemp()

    logger = logging.getLogger('google-drive-mailer')

    attachments = []
    
    msg = email.message_from_bytes(content, policy=default)

    try:
        os.mkdir(temp_dir)
    except FileExistsError:
        pass

    counter = 1

    for part in msg.walk():
        # multipart/* are just containers
        if part.get_content_maintype() == 'multipart':
            continue
        
        # Applications should really sanitize the given filename so that an
        # email message can't be used to overwrite important files
        filename = part.get_filename()
        
        if filename:
            logger.debug("filename: {}".format(filename))

        content_type = part.get_content_type()
        logger.debug("content type: {}".format(content_type))

        if not filename:
            ext = mimetypes.guess_extension(content_type)
            logger.debug("extension: {}".format(ext))
            if not ext:
                # Use a generic bag-of-bits extension
                ext = '.bin'

            filename = 'part-%03d%s' % (counter, ext)

        counter += 1
        pathname = os.path.join(temp_dir, filename)

        if os.path.exists(pathname):
            logger.error("ERROR: file {} exists!".format(pathname))
        else:
            with open(os.path.join(temp_dir, filename), 'wb') as fp:
                fp.write(part.get_payload(decode=True))

                attachments.append({ "path": pathname, "name": filename, "content-type": content_type })

    return attachments

def main():
    parser = ArgumentParser(description="""
    Unpack a MIME message into a directory of files.
    """)
    parser.add_argument('-d', '--directory', required=True,
                        help="""Unpack the MIME message into the named
                        directory, which will be created if it doesn't already
                        exist.""")
    parser.add_argument('msgfile')
    args = parser.parse_args()


if __name__ == '__main__':
    main()
