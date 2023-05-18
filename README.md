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

* Install poetry
* Install poetry dependencies
* Run poetry "start" task

After first run program create 'data' folder with tokens.json file. Insert telegram and openai token for correctly work