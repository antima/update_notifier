# update notifier


## Run

### As a docker container (recommended)

```shell
docker run --name update-notifier --env telegram_token=<yout bot token> -d
```

### As a script
```shell
git clone https://github.com/antima/update_notifier
cd update_notifier
virtualenv venv
pip install -r requirements.txt
export telegram_token=<your bot token>
python app.py
```

### As a systemd service

You can find a systemd service template in the **config/systemd** directory, that can be used as 
a base to build a service file to use this app as a systemd service.
You will have to set up a file with the environment variable for the token.

```shell
sudo cp config/systemd/telegram-updater.service /etc/systemd/system/ 
sudo systemctl enable telegram-updater
sudo systemctl start telegram-updater
```

## Usage 

- **/help** -> show this message
- **/add** [_name_] [_url_] [_interval_]-> start monitoring for the passed url identified by name, interval default is 15 mins
- **/remove** [_name_] -> remove an url under monitoring, identified by its name
- **/list** -> list all the urls under monitoring
- **/timer** [_name_] -> return the current interval for the url identified by name
- **/set_timer** [_name_] [_interval_] -> reset the monitor for the url with the new interval
- **/end** -> stop monitoring every url