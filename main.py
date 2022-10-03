import sys
import dropbox
from dropbox.files import WriteMode
from dropbox.exceptions import ApiError, AuthError
import datetime
import os
from dotenv import load_dotenv
import shutil
import subprocess


dt = datetime.datetime.today()
LOCAL_FILE = '/home/franciscodadone/Dev/sistema_de_gestion/README.md'
BACKUP_PATH = f"/{dt.day}-{dt.month}-{dt.year}"


def backup(local_file, backup_path):
    with open(local_file, 'rb') as f:
        print("Uploading " + local_file + " to Dropbox as " + backup_path + "...")
        try:
            dbx.files_upload(
                f.read(), backup_path,
                mode=WriteMode('overwrite')
            )
        except ApiError as err:
            if (err.error.is_path() and
                    err.error.get_path().reason.is_insufficient_space()):
                sys.exit("ERROR: Cannot back up; insufficient space.")
            elif err.user_message_text:
                print(err.user_message_text)
                sys.exit()
            else:
                print(err)
                sys.exit()


def local_backup():
    subprocess.run()


if __name__ == '__main__':
    load_dotenv()



    print("Creating a Dropbox object...")
    dbx = dropbox.Dropbox(os.getenv("ACCESS_TOKEN"))
    try:
        dbx.users_get_current_account()
    except AuthError:
        sys.exit("ERROR: Invalid access token; try re-generating an access token from the app console on the web.")
    backup(LOCAL_FILE, BACKUP_PATH)
print("Done!")
