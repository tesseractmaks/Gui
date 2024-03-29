## GUI chat client on python asyncio.
Chat client with GUI interface for minechat.dvmn.org.
It's a lesson of the [Async Python Course](https://dvmn.org/modules/async-python/) by the Devman. 

---
## Install

1. Create [virtualenv](https://docs.python.org/3/library/venv.html) of Python > 3.11 and activate it:

```bash
python3 -m virtualenv venv
source venv/bin/activate
```

2. Install requirements

```bash
pip install -r requirements.txt
```

3. You also can create `.env` file to save ENVIRONMENT variables and use it instead of CLI args.

```bash
ACCOUNT_TOKEN=some_token  # you can get token within registration.
HOST=minechat.dvmn.org  # host of server.
PORT_READ=5000  # port to read messages form server.
PORT_WRITE=5050  # port to send messages to server.
FILEPATH=chat.history  # path to file with a chat history.
```
---
## How to start

### Register new account
Run script and enter your username.<br>
After successful registration you can get token in `credentials.json`. 
```bash
python register.py
```

### Run chat 
```bash
python main.py
```
You'll see a graphical interface of a chat after you run script.

### You can use args instead of `.env` file:


* `--host` hostname, default is `minechat.dvmn.org`
* `--port_read` read port number, default is `5050`
* `--port_write` write port number, default is `5050`
* `--token` if token, tries to log in and send message from current account.
* `--path` file path to save chat history.

```bash
python main.py --host minechat.prod.org --token token_uuid
```
