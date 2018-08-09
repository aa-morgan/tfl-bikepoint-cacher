from bikepointcacher import BikePointCacher, mkdir_GDrive
import configparser

# Load TfL API credentials from config file
config = configparser.ConfigParser()
config.read('../config.txt')
api_id = config['TFL']['api_id']
api_key = config['TFL']['api_key']

# Create remote directory on Google Drive
remote_folder_path = 'TfL_bikepoint_cache'
remote_folder_id = mkdir_GDrive(remote_folder_path)
print('Folder ID: {}'.format(remote_folder_id))

# Instantiate BikePointCacher
cacher = BikePointCacher(api_id, api_key)

# Load parameters from config file
upload_loop_wait_time = int(config['PARAMS']['upload_loop_wait_time'])
download_loop_wait_time = int(config['PARAMS']['download_loop_wait_time'])
units = config['PARAMS']['units']
upload_loops = int(config['PARAMS']['upload_loops'])
# Start BikePointCacher
cacher.start(upload_loop_wait_time, download_loop_wait_time, units, upload_loops,
             remote_folder_id=remote_folder_id, verbose=True)