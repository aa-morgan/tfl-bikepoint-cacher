
`TfL BikePoint Cacher`
===============
TfL provides endpoints for data feeds relating to the Santandar Cycles through their [`Unified API`](https://tfl.gov.uk/info-for/open-data-users/our-open-data#on-this-page-5). The available endpoints are,

	/BikePoint
	/Place
	/Journey
	/AccidentStats

You can also download historical [`journey information`](http://cycling.data.tfl.gov.uk/) which includes,

	- Journey ID
	- Bike ID
	- Start date
	- Start time
	- End date
	- End time
	- Start docking station
	- Start docking station ID
	- End docking station
	- End docking station ID 

However, you can't download historical information on the number of available bikes, and docking stations. This information is only available through the [`Unified API`](https://tfl.gov.uk/info-for/open-data-users/our-open-data#on-this-page-5) but provides only the current values. 

This library was created to be able to continuously call the TfL `/BikePoint` endpoint, and save the `NbBikes`, `NbDocks`, and `NbEmptyDocks` values to a permanent cloud storage (in this case Google Drive).

I will be running this cacher on a Raspberry Pi, uploading the data to a dedicated Google Drive account, and making this data available through a link which will shortly be posted on this GitHub repository.

Install
-------

1. Install using `setuptools`,
```bash
git clone https://github.com/aa-morgan/tfl-bikepoint-cacher.git
cd tfl-bikepoint-cacher
python setup.py install
```

2. Setup authorisation for Google Drive,

    * Go to [credentials page](https://console.developers.google.com/apis/credentials)
    * Click `Create credentials` of type `OAuth client ID` with application type `Other`
    * Under `OAuth 2.0 client IDs` download the credentials file
    * Rename credentials file to `credentials.json`
    * Place `credentials.json` in the working directory of the `bikepoint_cacher.py` script (or `bikepoint_cacher.ipynb` notebook)

3. Obtain an `api_id` and `api_key` from the ([`TfL developer site`](https://api.tfl.gov.uk)), and copy them into the `config/config.txt` configuration file.

4. The first time you run this code you will be prompted to grant access to your Google Drive. Once granted, a `token.json` file will appear in the `config/` directory. This step fails if you run the code through a Jupyter notebook, therefore in order to obtain the `token.json` you must run the Python script,

```bash
python bikepoint_cacher.py
```

5. You will also be required to enable the `Drive API`. The first time you run `bikepoint_cacher.py` an error message will appear containing a URL to enable this API. Wait 1-2 minutes then run the code again and it should work.

Basic usage
-------
Import libraries,
```python
from bikepointcacher import BikePointCacher, mkdir_GDrive
```
Define `config.txt` filepath,
```python
config_filepath = '../config/config.txt'
```

Make remote Google Drive folder,
```python
remote_folder_path = 'TfL_bikepoint_cache'
remote_folder_id = mkdir_GDrive(remote_folder_path)
```

Instantiate `BikePointCacher` object,
```python
cacher = BikePointCacher(config_filepath, remote_folder_id)
```

Start `BikePointCacher`,
```python
cacher.start()
```

Version information
-------------------

| Library  | Version |
| ------------ | ------------ |
| `Python`  | 3.6.1 64bit [GCC 4.2.1 Compatible Apple LLVM 6.0 (clang-600.0.57)] |
| `IPython` | 5.3.0 |
| `OS` | Darwin 17.4.0 x86_64 i386 64bit |
| `attr` | 17.4.0 |
| `matplotlib` | 2.0.2 |
| `numba` | 0.35.0 |
| `numpy` | 1.14.3 |
| `scipy` | 1.00.0 |
| `sympy` | 1.0 |
| `tqdm` | 4.15.0 |
| `version_information` | 1.0.3 |