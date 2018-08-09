# Standard Python imports
from __future__ import print_function
import numpy as np
import pandas as pd
import requests
import time
import os
import shutil
from tqdm import tqdm
import configparser

# Google Drive imports
from apiclient.discovery import build
from apiclient.http import MediaFileUpload
from httplib2 import Http
from oauth2client import file as oauth_file, client, tools
# If modifying these scopes, delete the file token.json.
SCOPES = 'https://www.googleapis.com/auth/drive'

# TfL Unified API endpoint
bikepoint_endpoint = 'https://api.tfl.gov.uk/BikePoint'

class BikePointCacher(object):
    """ A class for caching the TfL Cycle BikePoint data
    """
    
    def __init__(self, config_filepath, remote_folder_id):
        self.config_filepath = config_filepath
        self.remote_folder_id = remote_folder_id
        self.config = configparser.ConfigParser()
        self.config.read(config_filepath)
        api_id = self.config['TFL']['api_id']
        api_key = self.config['TFL']['api_key']
        if len(api_id) == 8:
            self.api_id = api_id
        else:
            raise Exception('app_id must be of length 8. Received {}'.format(app_id))
        if len(api_key) == 32:
            self.api_key = api_key
        else:
            raise Exception('app_key must be of length 32. Received {}'.format(app_key))

    def start(self):
        # Get parameters from config file
        upload_loop_wait_time = int(self.config['PARAMS']['upload_loop_wait_time'])
        download_loop_wait_time = int(self.config['PARAMS']['download_loop_wait_time'])
        units = self.config['PARAMS']['units']
        upload_loops = int(self.config['PARAMS']['upload_loops'])
        tmp_data_dir = self.config['PARAMS']['tmp_data_dir']
        zip_data_dir = self.config['PARAMS']['zip_data_dir']
        verbose = bool(self.config['PARAMS']['verbose'])
        
        _units, label = get_units(units)
        if upload_loops > 0: loop_desc = '{}'.format(upload_loops)
        else: loop_desc = 'infinite'
        
        if verbose==True:
            print(
                """Starting TfL BikePoint Cacher:
                \t Download from TfL: every {} {}
                \t Upload to Google Drive: every {} {}, {} time(s)
                \t Local temporary data directory: {}
                \t Local zipped data directory: {}
                """.format(download_loop_wait_time, label, upload_loop_wait_time, label, loop_desc,
                          tmp_data_dir, zip_data_dir))
        
        _upload_loop_wait_time = upload_loop_wait_time * _units
        _download_loop_wait_time  = download_loop_wait_time  * _units
        
        payload = {'app_id': self.api_id, 'app_key': self.api_key}

        ### Upload Loop Counter ###
        _upload_loops = upload_loops
        upload_loop_count = 0
        while not _upload_loops == 0:

            ### Upload Loop ###
            _upload_loops -= 1
            upload_loop_count += 1
            # Upload to Google Drive after X minute(s)
            _desc = 'Upload loop {}/{}'.format(upload_loop_count, loop_desc)
            pbar = tqdm(total=(_upload_loop_wait_time//_download_loop_wait_time), desc=_desc, disable=not(verbose))
            _upload_loop_start_time = time.time() # in secs
            while (time.time() - _upload_loop_start_time) <= _upload_loop_wait_time:
                # Start time
                _download_loop_start_time = time.time() # in secs

                # Request new bikepoint data
                bikepoints = requests.get(bikepoint_endpoint, params=payload).json()

                # Extract just data relating to bike availability
                bikepoint_dict = {}
                for bikepoint in bikepoints:
                    bikepoint_dict[bikepoint['id']] = {item['key']:item['value'] 
                                                       for item in bikepoint['additionalProperties'] 
                                                       if item['key'][:2]=='Nb'}
                bikepoint_df = pd.DataFrame(bikepoint_dict)

                # Save to file
                if not os.path.isdir(tmp_data_dir):
                    os.mkdir(tmp_data_dir)
                bikepoint_df.to_csv(
                    os.path.join(tmp_data_dir, 
                    '{}.csv'.format(time.strftime("%Y-%m-%d_%H:%M:%S")))
                )

                # Update progress bar
                pbar.update(1)

                ### Download Loop ###
                while (time.time() - _download_loop_start_time) <= _download_loop_wait_time:
                    time.sleep(0.1) #  check every 0.1 secs

            # Condense tmp csv files into gzip
            filename = csv_to_gzip(self.config_filepath, verbose=verbose)
            
            # Save to Google Drive
            local_filepath = os.path.join(zip_data_dir, filename)
            remote_filename = filename
            upload_GDrive(self.config_filepath, local_filepath, remote_filename, remote_folder_id=self.remote_folder_id, 
                          mimetype='application/zip', verbose=verbose)

def get_units(units):
    if units in ['d', 'day', 'days']:
        return (60*60*24, 'day(s)')
    elif units in ['h', 'hr', 'hrs', 'hour', 'hours']:
        return (60*60, 'hour(s)')
    elif units in ['m', 'min', 'mins', 'minute', 'minutes']:
        return (60, 'minute(s)')
    elif units in ['s', 'sec', 'secs', 'second', 'seconds']:
        return (1, 'second(s)')
    raise Exception('Units {} not valid.'.format(units))
            
def get_drive_service(config_filepath):
    config = configparser.ConfigParser()
    config.read(config_filepath)
    credentials_filepath = config['GOOGLE']['credentials_filepath']
    token_filepath = config['GOOGLE']['token_filepath']
    store = oauth_file.Storage(token_filepath)
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets(credentials_filepath, SCOPES)
        creds = tools.run_flow(flow, store)
    return build('drive', 'v3', http=creds.authorize(Http()))

def mkdir_GDrive(config_filepath, remote_folder_path, verbose=True):
    if verbose==True: print('Creating Google Drive directory: {} ...'.format(remote_folder_path))
    drive_service = get_drive_service(config_filepath)
    file_metadata = {
        'name': remote_folder_path,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    file = drive_service.files().create(body=file_metadata,
                                        fields='id').execute()
    return file.get('id')

def upload_GDrive(config_filepath, local_filepath, remote_filename, remote_folder_id=None, mimetype='application/zip', verbose=True):
    if verbose==True: print('Uploading {} to GDrive:{} ...'.format(local_filepath, remote_filename))
    drive_service = get_drive_service(config_filepath)
    file_metadata = {'name': remote_filename}
    if not remote_folder_id==None: file_metadata['parents'] = [remote_folder_id]
    media = MediaFileUpload(local_filepath, mimetype=mimetype, resumable=True)
    file = drive_service.files().create(body=file_metadata, media_body=media).execute()

def csv_to_gzip(config_filepath, verbose=True):
    config = configparser.ConfigParser()
    config.read(config_filepath)
    tmp_data_dir = config['PARAMS']['tmp_data_dir']
    zip_data_dir = config['PARAMS']['zip_data_dir']
    # Convert CSV files from tmp_data_dir into DataFrame in data_dir
    if verbose==True: print('Converting temporary CSV files into GZip file...')
    df=None
    timestamps = []
    for filename in os.listdir(tmp_data_dir):
        if filename[-4:] == '.csv':
            timestamps.append(filename[:-4])
            tmp_df = pd.read_csv(os.path.join(tmp_data_dir, filename), index_col=0)
            if df is None:
                df=tmp_df
            else:
                df = df.append(tmp_df, sort=False)

    # Convert to MultiIndex DataFrame
    index = [np.repeat(timestamps,3),
             np.array(df.index)]
    columns = np.array(df.columns)
    df = pd.DataFrame(df.values, index=index, columns=columns)

    # Save to .GZ file
    if not os.path.isdir(zip_data_dir):
        os.mkdir(zip_data_dir)
    filename = '{}.gz'.format(time.strftime("%Y-%m-%d_%H:%M:%S"))
    df.to_csv(os.path.join(zip_data_dir, filename), compression='gzip')

    # Delete tmp_data folder
    if os.path.isdir(tmp_data_dir):
        shutil.rmtree(tmp_data_dir)

    return filename