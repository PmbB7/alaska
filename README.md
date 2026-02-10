✈️ Alaska Airlines Live Flight Tracker
This project builds a real-time flight tracking dashboard for Alaska Airlines (and Hawaiian Airlines) using Grafana Cloud and the OpenSky Network API.

It visualizes live flight telemetry—including location, altitude, heading, and speed—on an interactive world map, alongside live status counters and aircraft details.

☁️ Prerequisites: Setting Up Your Environment
Before touching any code, you need to spin up a Grafana Cloud instance and get the "Keys" that allow us to push data into it.

1. Spin up Grafana Cloud (Free)
Go to Grafana.com and click "Create Free Account".

Follow the prompts to set up your organization (you can name it anything, e.g., "Flight Tracker").

Once logged in, you will land on the Grafana Cloud Portal.

2. Get Data Ingestion Credentials (Loki)
We need to tell our Python script where to send the flight logs. Grafana uses a service called Loki for log data.

In your Grafana Cloud Portal, look for the "Loki" box (sometimes labeled "Logs").

Click "Send Logs" (or "Details").

Look for "Generating an API Token" or "Access Policies". Create a new token with logs:write permissions.

Save these 3 values (we will need them for the script):

URL: (e.g., https://logs-prod3.grafana.net/loki/api/v1/push)

User / Username: (This will be a number, e.g., 123456)

Password / API Token: (The long string you just generated)

3. Get Flight Data Access (OpenSky)
Go to OpenSky Network.

Click Register (top right) and create a free account.

Save your Username and Password.

Why? You can access the API anonymously, but it is very slow. A registered account allows us to update the map every 60 seconds reliably.

🛠️ Step 1: Set Up the Data Injector
Now that your environment is ready, we configure the Python script to act as the bridge: it pulls from OpenSky and pushes to Grafana.

Clone the repository:

Bash
git clone https://github.com/YOUR_USERNAME/alaska-flight-tracker.git
cd alaska-flight-tracker
Install Python requirements:

Bash
pip install requests pandas
Configure the Script: Open flight_tracker.py in any text editor. Find the section at the top marked CREDENTIALS & CONFIG and paste in the values you saved in the "Prerequisites" step.

Python
# --- 1. CREDENTIALS & CONFIG ---
LOKI_URL = "https://logs-prod3.grafana.net/loki/api/v1/push"  # From Grafana Portal
GRAFANA_USER = "123456"                                      # From Grafana Portal (Number)
GRAFANA_TOKEN = "glc_eyJ..."                                 # From Grafana Portal
CLIENT_ID = "my_opensky_user"                                # Your OpenSky Username
CLIENT_SECRET = "my_opensky_pass"                            # Your OpenSky Password
Run the Script:

Bash
python flight_tracker.py
Keep this terminal window open! As long as this script is running, your dashboard is live.
