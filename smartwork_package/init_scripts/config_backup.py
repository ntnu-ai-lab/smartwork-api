# set this to your Dropbox project folder
# CLOUD_DIR = "c:/Dropbox/selfBACK EU project/"
# education and exercise dir
# STATIC_PATH = "./data/"
# comment this to load files from "./data/" dir
# STATIC_PATH = DROPBOX_DIR + "selfBACK-DSS/backend/content/"
# SELFBACK_ROOT = "c:/Dropbox/selfBACK EU project/"

STATIC_PATH = "./smartwork_package/init_scripts/static_files/"
# WEB_PATH = BACKUP_ROOT + "Webpage_content/"


TAILORING_DIR = STATIC_PATH + "tailoring/"
ACHIEVEMENT_DIR = STATIC_PATH + "achievements/"
CODEBOOK_PATH = STATIC_PATH + "SmaRTWork-codebook_updated_11052023.xlsx"
# OUTPUT_DIR = "./json/"
OUTPUT_DIR = "./temp/"
BACKEND_STATIC_DIR= "./smartwork_package/init_scripts/backend_static_data/"

# also copy files to backend_static_dir. Make it None to skip copying to the backend source dir.
# BACKEND_STATIC_DIR = None
# BACKEND_RESOURCES_DIR = "c:/OneDrive/OneDrive - NTNU/Java/selfback-dss/dss-core/src/main/resources/"
# BACKEND_STATIC_DIR = BACKEND_RESOURCES_DIR + "static_data/"
# BACKEND_STATIC_BACKUP_DIR = BACKEND_RESOURCES_DIR + "static_data_backup/"