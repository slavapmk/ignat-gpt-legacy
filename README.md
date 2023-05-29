# Ignat GPT Telegram Bot

### Docker mode

Default running scripts made for run in docker mode:

* Install script - bash script for installing docker in Debian based systems
* Run script

For "cold install and start" run next command:

```shell
./install && ./run
```

### Manual mode

* Install poetry (instructions [here](https://python-poetry.org/docs/))
```shell
curl -sSL https://install.python-poetry.org | python3 -
```
* Install poetry dependencies
```shell
poetry install
```
* Run poetry "start" task
```shell
poetry run start
```

After first run program create 'data' folder with tokens.json file. Insert telegram and openai token for correctly work