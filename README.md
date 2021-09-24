# sxapi_legacy

smaXtec API Client

:warning: **The API of this package is deprecated and will be changed with version 1.x** :warning:

[![Build Status](https://travis-ci.org/wuttem/sxapi.svg?branch=develop)](https://travis-ci.org/wuttem/sxapi)

Python wrapper for the smaXtec public API

## Usage

To use the API smaXtec user credentials (smaXtec Messenger Account) are needed.

```python
from sxapi import API

a = API(email="myuser@smaxtec.com", password="mypassword")

# Get organisations
orgas = a.organisations
print orgas

# Get Animals in an organisation
animals = orgas[0].animals
print animals
# Get Sensordata for an animal
data = animals[0].get_frame(["temp", "act"], days_back=10)
print(data)

# Get Events for an animal
events = animals[0].get_events()
print(events.to_series())

# Get by id
print a.get_organisation("5721e3f8a80a5f54c6315131").devices
print a.get_animal("572209c1a80a5f54c631513f").name
print a.get_animal("572209c1a80a5f54c631513f").heats
print a.get_animal("572209c1a80a5f54c631513f").lactations
print a.get_animal("572209c1a80a5f54c631513f").current_dim
print a.get_animal("572209c1a80a5f54c631513f").dim_range(datetime.datetime(2018,1,1), datetime.datetime.now(), interval=12*60*60)

# Show request stats
a.print_stats()
```

### Timezone Awareness

By default the API Client tries to make all datetimes timezone aware with pendulum datetime instances.
See: https://pendulum.eustace.io/docs/

To deactivate this behaviour create API Clients with _tz_aware=False_

```python
from sxapi import API

a = API(email="myuser@smaxtec.com", password="mypassword", tz_aware=False)
```

## Low Level Usage

```python
from sxapi import LowLevelAPI

a = LowLevelAPI(email="user@smaxtec.com", password="mypassword")

# Get by id
print a.get_organisation_by_id("5721e3f8a80a5f54c6315131")
print a.get_animal_by_id("572209c1a80a5f54c631513f")
print a.getAnimal("dsdsd") # from internal works only with api key
```

## Flask Usage

The API Client includes a Flask Extension Module for usage of the LowLevel API.
Usage is only possible with a permanent API Token and an internal endpoint.

```python
from flask import Flask, jsonify
from sxapi.ext import FlaskSX

class MYCONFIG(object):
    DEBUG = True
    TESTING = True
    SMAXTEC_API_PUBLIC_ENDPOINT = "http://mypublicapi.smaxtec.com/api/v1"
    SMAXTEC_API_PRIVATE_ENDPOINT = "http://127.0.0.1:8787/internapi/v0"
    SMAXTEC_API_KEY = "...JWT..."

app = Flask(__name__)
app.config.from_object(MYCONFIG)
api = FlaskSX()
api.init_app(app)

# Example Id: 0700003445
@app.route('/device/<string:device_id>')
def show_device(device_id):
    return jsonify(api.get_device_by_id(device_id))

# Example Id: 59f0743b093ed5cab7a1fb18
@app.route('/animal/<string:animal_id>')
def show_animal(animal_id):
    return jsonify(api.get_animal_by_id(animal_id))

@app.route('/')
def show_home():
    public = api.get_public_status()
    private = api.get_private_status()
    return jsonify({"public": public, "private": private})

if __name__ == "__main__":
    app.run()
```

## Development

To build a new pip version increase version and tag with git tag -a "vX.X".
Build artifacts and push to pip

```
python setup.py sdist bdist_wheel
twine upload dist/*
```
