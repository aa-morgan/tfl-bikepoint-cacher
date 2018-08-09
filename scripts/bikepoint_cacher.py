from bikepointcacher import BikePointCacher, mkdir_GDrive

# Define configuration filepath
config_filepath = '../config/config.txt'

# Create remote directory on Google Drive
remote_folder_path = 'TfL_bikepoint_cache'
remote_folder_id = mkdir_GDrive(config_filepath, remote_folder_path)
print('Folder ID: {}'.format(remote_folder_id))

# Instantiate BikePointCacher
cacher = BikePointCacher(config_filepath, remote_folder_id)

# Start BikePointCacher
cacher.start()