TfL BikePoint Cacher
===============
TfL provides endpoints for data relating to the Santandar Cycles through their [Unified API](tfl.gov.uk/info-for/open-data-users/our-open-data#on-this-page-5). The available endpoints are,

- /BikePoint
- /Place
- /Journey
- /AccidentStats

You can also download historical [journey information](http://cycling.data.tfl.gov.uk/) which includes,

-   Journey ID
-   Bike ID
-   Start date
-   Start time
-   End date
-   End time
-   Start docking station
-   Start docking station ID
-   End docking station
-   End docking station ID 

However, you can't download historical information on the number of available bikes, and docking stations. This information is only available through the [Unified API](tfl.gov.uk/info-for/open-data-users/our-open-data#on-this-page-5) but provides only the current values. 

This library was created to be able to continuously call the TfL /BikePoint endpoint, and save the 'NbBikes', 'NbDocks', and 'NbEmptyDocks' values to a permanent cloud storage (in this case Google Drive).

I will be running this cacher on a Raspberry Pi, uploading the data to a dedicated Google Drive account, and making this data available through a link which will shortly be posted on this GitHub repository.

Install
-------

Install using setuptools,
```bash
git clone https://github.com/aa-morgan/tfl-bikepoint-cacher.git
cd tfl-bikepoint-cacher
python setup.py install
```

Basic usage
-------
Import libraries,
```python
from bikepointcacher import BikePointCacher, mkdir_GDrive
```
Define TfL credentials, ([TfL developer site](api.tfl.gov.uk))

```python
api_id = 'xxxxxxxx'
api_key = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
```

Make remote Google Drive folder,
```python
remote_folder_path = 'data'
remote_folder_id = mkdir_GDrive(remote_folder_path)
```

Instantiate BikePointCacher object,
```python
cacher = BikePointCacher(api_id, api_key)
```
Start BikePointCacher,
```python
upload_loop_wait_time = 60
download_loop_wait_time = 5
units = 'minutes'
upload_loops = -1 # -1 == Infinite
cacher.start(upload_loop_wait_time, download_loop_wait_time, units, upload_loops,
             remote_folder_id=remote_folder_id, verbose=True)
```

Version information
-------------------

| Library  | Version |
| ------------ | ------------ |
| Python  | 3.6.1 64bit [GCC 4.2.1 Compatible Apple LLVM 6.0 (clang-600.0.57)] |
| IPython | 5.3.0 |
| OS | Darwin 17.4.0 x86_64 i386 64bit |
| attr | 17.4.0 |
| matplotlib | 2.0.2 |
| numba | 0.35.0 |
| numpy | 1.14.3 |
| scipy | 1.00.0 |
| sympy | 1.0 |
| tqdm | 4.15.0 |
| version_information | 1.0.3 |