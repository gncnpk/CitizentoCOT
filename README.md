# Citizen to CoT
### A PyTAK application that pulls incidents from Citizen's API and pushes it to TAK as a CoT Event.


## Installation

1. Install `pipenv` using `python -m pip install pipenv`
2. Run `python -m pipenv install` to install the prerequisites.
3. Create a `config.ini` and adjust the settings to your use-case.

## Usage/Setup

### Running (as a standalone application)

Run `python -m pipenv run python main.py` to start the application.

### Running (as a service)

1. Modify `citizentocot.service` to the correct working directory, user, and shell script directory.
2. Copy it to the right directory using `cp citizentocot.service /etc/systemd/system/`
3. Run `sudo systemctl daemon-reload`
4. Run `sudo systemctl enable citizentocot` (if you want to run it at boot, otherwise skip this step)
5. Run `sudo systemctl start citizentocot` to start the service

### Example Config
This config connects to a TAK server instance via TLS (using a self-signed cert), pulls data and pushes CoT events every 30 minutes.

`config.ini`
```ini
[citizentocot]
COT_URL = tls://XX.XX.XX.XX:8089
PYTAK_TLS_CLIENT_CERT = private_key.pem
PYTAK_TLS_CLIENT_KEY = private_key.pem
PYTAK_TLS_DONT_VERIFY = true
CITIZEN_API_URL = https://citizen.com/api/incident/trending?lowerLatitude=XX&lowerLongitude=XX&upperLatitude=XX&upperLongitude=XX&fullResponse=true&limit=200
POLL_INTERVAL = 1800
```