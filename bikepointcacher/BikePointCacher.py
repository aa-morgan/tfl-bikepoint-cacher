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
        self.num_upload_loops = int(self.config['PARAMS']['num_upload_loops'])
        self.upload_loop_wait_time = int(self.config['PARAMS']['upload_loop_wait_time'])
        self.download_loop_wait_time = int(self.config['PARAMS']['download_loop_wait_time'])
        self.units = self.config['PARAMS']['units']
        self.tmp_data_dir = self.config['PARAMS']['tmp_data_dir']
        self.zip_data_dir = self.config['PARAMS']['zip_data_dir']
        self.verbose = bool(self.config['PARAMS']['verbose'])
        
        units_mul, unit_label = get_units(self.units)
        if self.num_upload_loops > 0: self.upload_loop_max = '{}'.format(self.upload_loops)
        else: self.upload_loop_max = 'infinite'
            
        self.upload_loop_wait_time = self.upload_loop_wait_time * units_mul
        self.download_loop_wait_time  = self.download_loop_wait_time  * units_mul
        
        if self.verbose==True:
            print(
                """Starting TfL BikePoint Cacher:
                \t Download from TfL: every {} {}
                \t Upload to Google Drive: every {} {}, {} time(s)
                \t Local temporary data directory: {}
                \t Local zipped data directory: {}
                """.format(self.download_loop_wait_time, unit_label, 
                           self.upload_loop_wait_time, unit_label, 
                           self.upload_loop_max, self.tmp_data_dir, self.zip_data_dir))
        
        self.payload = {'app_id': self.api_id, 'app_key': self.api_key}

        ### Upload Loops ###
        self.upload_loops()
            
    def upload_loops(self):
        """
        """
        self.upload_loop_remaining = self.num_upload_loops
        self.upload_loop_count = 0
        while not self.upload_loop_remaining == 0:
            self.upload_loop_start_time = time.time() # in secs
            self.upload_loop_remaining -= 1
            self.upload_loop_count += 1

            ### Download Loops ###
            self.download_loops()

            # Condense tmp csv files into gzip
            filename = csv_to_gzip(self.config_filepath, verbose=self.verbose)

            # Save to Google Drive
            local_filepath = os.path.join(self.zip_data_dir, filename)
            remote_filename = filename
            upload_GDrive(self.config_filepath, local_filepath, remote_filename, 
                          remote_folder_id=self.remote_folder_id, 
                          mimetype='application/zip', verbose=self.verbose)

    def download_loops(self):
        """
        """
        # Upload to Google Drive after X minute(s)
        tqdm_desc = 'Upload loop {}/{}'.format(self.upload_loop_count, self.upload_loop_max)
        pbar = tqdm(total=(self.upload_loop_wait_time//self.download_loop_wait_time), 
                    desc=tqdm_desc, disable=not(self.verbose))
        while (time.time() - self.upload_loop_start_time) <= self.upload_loop_wait_time:
            self.download_loop_start_time = time.time() # in secs

            # Request new bikepoint data
            bikepoints = requests.get(bikepoint_endpoint, params=self.payload).json()

            # Extract just data relating to bike availability
            try:
                bikepoint_dict = {}
                for bikepoint in bikepoints:
                    bikepoint_dict[bikepoint['id']] = {item['key']:item['value'] 
                                                       for item in bikepoint['additionalProperties'] 
                                                       if item['key'][:2]=='Nb'}
                bikepoint_df = pd.DataFrame(bikepoint_dict)

                # Save to file
                if not os.path.isdir(self.tmp_data_dir):
                    os.mkdir(self.tmp_data_dir)
                bikepoint_df.to_csv(
                    os.path.join(self.tmp_data_dir, 
                    '{}.csv'.format(time.strftime("%Y-%m-%d_%H:%M:%S")))
                )

                # Update progress bar
                pbar.update(1)

                # Wait for next Download Loop iteration
                while (time.time() - self.download_loop_start_time) <= self.download_loop_wait_time:
                    time.sleep(0.1) #  check every 0.1 secs
                    
            except:
                # If failed then wait 10 sec and retry.
                time.sleep(10)
                
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