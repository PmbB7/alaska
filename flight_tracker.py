import requests
import time
import json
import pandas as pd
import os
import re
import sys

# --- 1. CREDENTIALS & CONFIG ---
LOKI_URL = "https://logs-prod3.grafana.net/loki/api/v1/push"
GRAFANA_USER = "12345"
GRAFANA_TOKEN = "glc_eyJ****"

CLIENT_ID = "username"
CLIENT_SECRET = "clientsecret***"

GITHUB_ROUTES_URL = "https://raw.githubusercontent.com/PmbB7/alaska/refs/heads/main/routes.json"

# --- 2. DATA LOADERS ---
def load_github_routes():
    try:
        r = requests.get(GITHUB_ROUTES_URL, timeout=10)
        return r.json()
    except:
        return {}

def load_aircraft_db():
    db_file = "aircraft_db.csv"
    if not os.path.exists(db_file):
        r = requests.get(
            "https://opensky-network.org/datasets/metadata/aircraftDatabase.csv",
            stream=True,
            timeout=30
        )
        with open(db_file, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)

    return (
        pd.read_csv(
            db_file,
            usecols=["icao24", "model", "typecode"],
            low_memory=False
        )
        .set_index("icao24")
    )

def get_opensky_token():
    try:
        r = requests.post(
            "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token",
            data={
                "grant_type": "client_credentials",
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
            },
            timeout=10,
        )
        return r.json().get("access_token")
    except:
        return None

# --- 3. INITIAL LOAD ---
ALASKA_KNOWLEDGE = load_github_routes()
aircraft_df = load_aircraft_db()

token = get_opensky_token()
headers = {"Authorization": f"Bearer {token}"}

last_route_sync = time.time()

# --- 4. MAIN LOOP ---
while True:
    try:
        # Refresh route knowledge hourly
        if time.time() - last_route_sync > 3600:
            ALASKA_KNOWLEDGE = load_github_routes()
            last_route_sync = time.time()

        r = requests.get(
            "https://opensky-network.org/api/states/all",
            headers=headers,
            timeout=(5, 20),
        )

        if r.status_code == 200:
            states = r.json().get("states", [])
            flights = []
            readable_time = time.strftime("%H:%M:%S")

            for s in states:
                call = (s[1] or "").strip()

                if (
                    (call.startswith("ASA") or call.startswith("HA")
                     or "HAWK" in call or "HAGAR" in call)
                    and s[5] and s[6]
                ):
                    # Flight number (forced int)
                    f_num_str = re.sub(r"[^0-9]", "", call)
                    f_num = int(f_num_str) if f_num_str else 0

                    brand = "Alaska"
                    if 800 <= f_num <= 1299:
                        brand = "Hawaiian"
                    if any(x in call for x in ["HAWK", "HAGAR", "HALO", "HAF"]):
                        brand = "SpecialOps"

                    # Route
                    route = ALASKA_KNOWLEDGE.get(call)
                    if not route and call.startswith("ASA"):
                        route = ALASKA_KNOWLEDGE.get(call.replace("ASA", "HA"))
                    route = route or "UNK ➔ UNK"
                    origin, dest = (
                        route.split(" ➔ ")
                        if " ➔ " in route
                        else ("UNK", "UNK")
                    )

                    # Aircraft
                    try:
                        info = aircraft_df.loc[s[0]]
                        ac_type = f"{info['model']} ({info['typecode']})"
                    except:
                        ac_type = "737-9 (B39M)"

                    # Telemetry (numeric)
                    alt_ft = int(s[7] * 3.28) if s[7] else 0
                    speed_kts = int((s[9] or 0) * 1.94)
                    speed_mph = int(speed_kts * 1.15078)
                    lat = float(round(s[6], 4))
                    lon = float(round(s[5], 4))
                    angle = float(round(s[10] or 0, 1))

                    flights.append(
                        {
                            "time": readable_time,
                            "call": call,
                            "f_num": f_num,
                            "brand": brand,
                            "type": ac_type,
                            "lat": lat,
                            "lon": lon,
                            "alt": alt_ft,
                            "speed_kts": speed_kts,
                            "speed_mph": speed_mph,
                            "origin": origin,
                            "dest": dest,
                            "angle": angle,
                        }
                    )

            if flights:
                now_ns = str(time.time_ns())
                payload = {
                    "streams": [
                        {
                            "stream": {"job": "flight_tracker"},
                            "values": [
                                [now_ns, json.dumps(p)] for p in flights
                            ],
                        }
                    ]
                }

                requests.post(
                    LOKI_URL,
                    json=payload,
                    auth=(GRAFANA_USER, GRAFANA_TOKEN),
                    timeout=10,
                )

                # ✅ SINGLE-LINE STATUS OUTPUT
                sys.stdout.write(
                    "\r" + f"[{readable_time}] Data pushed to Grafana".ljust(80)
                )
                sys.stdout.flush()

        elif r.status_code == 401:
            token = get_opensky_token()
            headers = {"Authorization": f"Bearer {token}"}

    except Exception as e:
        sys.stdout.write(
            "\r"
            + f"[{time.strftime('%H:%M:%S')}] ERROR: {str(e)[:60]}".ljust(80)
        )
        sys.stdout.flush()

    time.sleep(60)
