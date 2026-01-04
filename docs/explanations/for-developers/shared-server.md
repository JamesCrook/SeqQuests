# Shared Server

SeqQuests is designed to run its FastAPI web server on the user's machine. Its original design is not intended for shared use by multiple people.

It could be used in lab setting as a shared resource. It has no logins, no idea of user accounts. Anyone with access to the UI can start, inspect, pause and delete any of the batch jobs. 

The server cannot be run insider a docker environment because it uses metal (Apple Silicon) and there are no Linux drivers for that. Moreover, as any unauthenticated user can start a search job, it's easy for a denial of service attack to run - so this is never going to be a hardened solution without the addition of logins. I don't want to provide authentication support in the repo I make, since that creates barriers/inconvenience to shared use in the lab.

The recommended solution for a lab server (untested) is to set up a user on the Mac server, Mac Mini suggested, with restricted permisisons, and setup as described in the Setup instructions below. Feedback on improving the instructions welcome.

If an attacker exploits a path traversal bug or some other vulnerability, they can only:

- Read files that `labserver` can read (code, databases, results - which the app needs anyway)
- Write to the output directory
- **Cannot** read personal files, SSH keys, browser data, etc.
- **Cannot** modify the application code
- **Cannot** install software or escalate privileges

web_server.py does in any case attempt to protect against path traversal vulnerabilities. There is though potential risk that parameters passed as configuration parameters to features of the software could access data outside the intended directories.

**Admin (yourname) does:**
1. Clone repo
2. Install Python dependencies
3. Compile Metal executables (requires Xcode, metal-cpp)
4. Download databases
5. Create labserver user
6. Set permissions

**labserver does:**
1. Run the server (and nothing else)


## Prerequisites

Complete and try out the standard installation as your admin user first (see GETTING_STARTED.md):

```bash
# As your normal admin user
cd /Users/yourname
git clone <repo> seqquests
cd seqquests
pip install -e .
./compile.sh
./get_uniprot.sh
```

The restricted `labserver` user should not have Xcode, metal-cpp, or write access to the codebase — it only needs to *run* the pre-built executables.

## Setup

**1. Create a restricted user**
```bash
# Create user with no admin rights, no home directory or access to your stuff
sudo dscl . -create /Users/labserver
sudo dscl . -create /Users/labserver UserShell /bin/bash
sudo dscl . -create /Users/labserver UniqueID 401
sudo dscl . -create /Users/labserver PrimaryGroupID 20
sudo dscl . -create /Users/labserver NFSHomeDirectory /Users/labserver
sudo mkdir -p /Users/labserver
sudo chown labserver:staff /Users/labserver
```

**2. Set permissions on the project**
```bash
# Assuming your project is at /Users/yourname/seqquests

# Let labserver read the code and executables
chmod -R o+rX /Users/yourname/seqquests

# Create a dedicated output directory labserver can write to
mkdir /Users/yourname/seqquests/output
chown labserver:staff /Users/yourname/seqquests/output

# Ensure the data directory is readable (and read only):
chmod -R o+rX /Users/yourname/data/seqquests
```

The `.env` file in the project directory must use **absolute paths** (not `~`) since the server runs as `labserver`, not your admin user:

```bash
# .env - absolute paths for shared server
SEQQUESTS_DATA_DIR=/Users/yourname/data/seqquests
```

**3. Run the server as that user**
```bash
cd /Users/yourname/seqquests/
sudo -u labserver python py/web_server.py --host 192.168.1.50 --port 8006
```

## Extension to run at startup

```bash
# Find the right python that has all the dependencies 
which python3
# You will get a path like:
# /Users/yourname/seqquests/.venv/bin/python
# which you will use in the .plist file

# Create a launch daemon to start on boot
sudo nano /Library/LaunchDaemons/com.lab.seqquests.plist
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.lab.seqquests</string>
    <key>UserName</key>
    <string>labserver</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/yourname/seqquests/.venv/bin/python</string>
        <string>/Users/yourname/seqquests/py/web_server.py</string>
        <string>--host</string>
        <string>0.0.0.0</string>
        <string>--port</string>
        <string>8006</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
	<key>WorkingDirectory</key>
	<string>/Users/yourname/seqquests</string>
</dict>
</plist>
```

```bash
sudo launchctl load /Library/LaunchDaemons/com.lab.seqquests.plist
```

## Network binding note

- `--host 127.0.0.1` — localhost only (access via SSH tunnel)
- `--host 192.168.x.x` — specific lab network IP
- `--host 0.0.0.0` — all interfaces (use only if behind firewall)



