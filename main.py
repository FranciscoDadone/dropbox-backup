import sys
import dropbox
from dropbox.files import WriteMode
from dropbox.exceptions import ApiError, AuthError
import os
from dotenv import load_dotenv
import shutil
import datetime


dt = datetime.datetime.today()
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


def local_purge():
    backup_path_list = os.listdir(backup_path)
    while len(backup_path_list) >= int(os.getenv('HOLD_BACKUPS')):
        oldest = datetime.datetime.now()
        oldest_str = ''
        for file in backup_path_list:
            str_date = file.replace('.zip', '')
            date = datetime.datetime.strptime(str_date, "%d-%m-%Y_%H:%M:%S")
            if oldest > date:
                oldest = date
                oldest_str = file
        os.remove(backup_path + '/' + oldest_str)
        backup_path_list.remove(oldest_str)


def remote_purge():
    dropbox_path = os.getenv('DROPBOX_PATH')
    backup_path_list = dbx.files_list_folder(dropbox_path).entries
    while len(backup_path_list) >= int(os.getenv('HOLD_BACKUPS')):
        oldest = datetime.datetime.now()
        oldest_str = ''
        for file in backup_path_list:
            str_date = file.name.replace('.zip', '')
            date = datetime.datetime.strptime(str_date, "%d-%m-%Y_%H:%M:%S")
            if oldest > date:
                oldest = date
                oldest_str = file
        dbx.files_delete_v2(dropbox_path + '/' + oldest_str.name)
        backup_path_list.remove(oldest_str)


if __name__ == '__main__':
    load_dotenv()
    backup_path = os.getenv('BACKUP_PATH').replace('TEMP_FOLDER', os.getenv('TEMP_FOLDER'))
    temp_path = os.getenv('TEMP_FOLDER').replace('BACKUP_PATH', backup_path)
    pre_backup_cmds = os.getenv('PRE_BACKUP_CMDS').replace('BACKUP_PATH', backup_path).replace('TEMP_FOLDER', temp_path).split(',')

    if not os.path.isdir(backup_path):
        os.mkdir(backup_path)

    local_purge()

    if not os.path.isdir(temp_path):
        os.mkdir(temp_path)

    for cmd in pre_backup_cmds:
        os.system(cmd)

    compressed_path = backup_path + '/' + datetime.datetime.now().strftime("%d-%m-%Y_%H:%M:%S")
    shutil.make_archive(compressed_path, 'zip', temp_path)
    shutil.rmtree(temp_path)

    dbx = dropbox.Dropbox(app_key=os.getenv('APP_KEY'), app_secret=os.getenv('APP_SECRET'), oauth2_refresh_token=os.getenv('REFRESH_TOKEN'))
    try:
        dbx.users_get_current_account()
    except AuthError:
        sys.exit("ERROR: Invalid access token; try re-generating an access token from the app console on the web.")
    remote_purge()
    backup(compressed_path + '.zip', os.getenv('DROPBOX_PATH') + '/' + compressed_path.split('/')[-1] + '.zip')
print("Done!")
