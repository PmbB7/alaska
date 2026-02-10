# ✈️ Alaska Airlines Live Flight Tracker

![Dashboard Screenshot](https://github.com/PmbB7/alaska/raw/main/image001-4.png)

This project builds a real-time flight tracking dashboard for **Alaska Airlines** (and Hawaiian Airlines) using **Grafana Cloud** and the **OpenSky Network API**.

It visualizes live flight telemetry—including location, altitude, heading, and speed—on an interactive world map, alongside live status counters and aircraft details.

---

## ☁️ Prerequisites: Setting Up Your Environment

Before touching any code, you need to spin up a Grafana Cloud instance and get the "Keys" that allow us to push data into it.

### 1. Spin up Grafana Cloud (Free)

1. Go to **[Grafana.com](https://grafana.com/)** and click **"Create Free Account"**.
2. Follow the prompts to set up your organization (you can name it anything, e.g., "Flight Tracker").
3. Once logged in, you will land on the **Grafana Cloud Portal**.

### 2. Get Data Ingestion Credentials (Loki)

We need to tell our Python script *where* to send the flight logs. Grafana uses a service called **Loki** for log data.

1. In your Grafana Cloud Portal, look for the **"Loki"** box (sometimes labeled **"Logs"**).
2. Click **"Send Logs"** (or "Details").
3. Look for "Generating an API Token" or "Access Policies". Create a new token with **`logs:write`** permissions.
4. **Save these 3 values** (we will need them for the script):
* **URL:** (e.g., `https://logs-prod3.grafana.net/loki/api/v1/push`)
* **User / Username:** (This will be a number, e.g., `123456`)
* **Password / API Token:** (The long string you just generated)



### 3. Get Flight Data Access (OpenSky)

1. Go to **[OpenSky Network](https://opensky-network.org/)**.
2. Click **Register** (top right) and create a free account.
3. **Save your Username and Password**.
> *Why?* You can access the API anonymously, but it is very slow. A registered account allows us to update the map every 60 seconds reliably.



---

## 🛠️ Step 1: Set Up the Data Injector

Now that your environment is ready, we configure the Python script to act as the bridge: it pulls from OpenSky and pushes to Grafana.

### 1. Clone & Install

Clone the repository and install the required libraries:

```bash
git clone https://github.com/YOUR_USERNAME/alaska-flight-tracker.git
cd alaska-flight-tracker
pip install requests pandas

```

### 2. Configure the Script

Open `flight_tracker.py` in any text editor. Find the section at the top marked **CREDENTIALS & CONFIG** and paste in the values you saved in the "Prerequisites" step.

```python
# --- 1. CREDENTIALS & CONFIG ---
LOKI_URL = "https://logs-prod3.grafana.net/loki/api/v1/push"   # From Grafana Portal
GRAFANA_USER = "123456"                                      # From Grafana Portal (Number)
GRAFANA_TOKEN = "glc_eyJ..."                                 # From Grafana Portal
CLIENT_ID = "my_opensky_user"                                # Your OpenSky Username
CLIENT_SECRET = "my_opensky_pass"                            # Your OpenSky Password

```

### 3. Run the Script

Start the script to begin fetching data:

```bash
python flight_tracker.py

```

> **Note:** Keep this terminal window open! As long as this script is running, your dashboard is live.

---

## 📊 Step 2: Build the Dashboard

Here is the step-by-step guide to manually building each panel. This assumes your script is running and pushing data.

### 🟢 1. Create Dashboard Variables

Before building panels, set up the variables (filters) at the top of the dashboard.

1. Go to **Dashboard Settings (Gear Icon)** > **Variables**.
2. **Variable 1:**
* **Name:** `Flight`
* **Type:** Query
* **Query:** `label_values({job="flight_tracker"}, call)`
* **Sort:** Alphabetical (asc)


3. **Click Apply.**

### 🗺️ 2. Build "Live Flight Map" (Geomap)

This is the centerpiece of the dashboard.

1. **Add Visualization** > Select **Geomap**.
2. **Datasource:** Select the Loki datasource you created.
3. **Query (Loki):** Enter this LogQL query. It extracts JSON fields and aggregates the last known position over 2 minutes.
```logql
sum by (call, lat, lon, origin, dest, angle, alt) (
  last_over_time({job="flight_tracker"} | json | unwrap alt [2m])
)

```


4. **Query Options:** Set Type to **Instant**.
5. **Run Query**.
6. **Transformations (Tab):**
* **Group By:** Group by `call` → Calculate `Count`. For all other fields, select `Last` (ignore nulls).
* **Organize fields:** Rename `call` -> `Flight Number`, `angle` -> `Ang`, `dest` -> `Destination`, `lat` -> `Lat`, `lon` -> `Lon`, `origin` -> `Origin`, `Value #A` -> `Alt`.
* **Convert field type:** Set `Lat`, `Lon`, `Ang`, and `Alt` to **Number**.


7. **Panel Settings (Right Sidebar):**
* **Map View (View):** North America
* **Data Layer (Markers):**
* **Location Mode:** `Coordinates` (`Latitude`: `Lat`, `Longitude`: `Lon`)
* **Styles:**
* **Size:** Fixed (e.g., 10px).
* **Symbol:** Plane icon (`img/icons/marker/plane.svg` or standard triangle).
* **Color:** Select `Alt`.
* **Rotation:** Select the `Ang` field. *(Crucial for flight direction!)*
* **Text Label:** Select the `Flight Number` field. (Y offset -15)





### 🔢 3. Build "In The Air" & "On Ground" (Stat Panels)

These panels count how many planes are flying vs. taxiing.

1. **Add Visualization** > Select **Stat**.
2. **Datasource:** Select your Loki datasource.
3. **Query (Loki):** Same as the Geomap query above.
```logql
sum by (call, lat, lon, origin, dest, angle, alt) (
  last_over_time({job="flight_tracker"} | json | unwrap alt [2m])
)

```


4. **Query Options:** Set Type to **Instant**.
5. **Run Query**.
6. **Transformations:**
* **Group By:** Group by `call` → Calculate `Count`. All others Calculate 'Last'.
* **Filter by value:**
* *For "In The Air":* Filter `Alt` **Greater than 0**.
* *For "On Ground":* Filter `Alt` **Equal to 0**.




7. **Panel Settings:**
* **Title:** `🛬 On Ground` (or `✈️ In The Air`).
* **Calculation:** `Count`.
* **Color Mode:** Value.



### 📋 4. Build "Flight Manifest" (Table)

This lists the details of every active flight.

1. **Add Visualization** > Select **Table**.
2. **Datasource:** Select your Loki datasource.
3. **Query (Loki):**
```logql
sum by (call, lat, lon, origin, dest, angle, alt) (
  last_over_time({job="flight_tracker"} | json | unwrap alt [2m])
)

```


4. **Query Options:** Set Type to **Instant**.
5. **Transformations:**
* **Group By:** Group by `call` → Calculate `Count`. All others Calculate 'Last'.
* **Organize fields:** Select `Flight Number`, `Origin`, `Destination`, `Alt`.


6. **Panel Settings:**
* **Cell Options:** Enable "Cell value mapped colors".
* **Value Mappings:**
* `Alt` = 0 → "🛬 On Ground" (Color: Yellow)
* `Alt` > 0 → "✈️ In Flight" (Color: Green)


* **Add Field Override:**
* Select Field: "Flight Number"
* Add property **Data links**: `https://YOUR_GRAFANA_URL/d/YOUR_DASHBOARD_UID?var-Flight=${__data.fields.call}` (This allows clicking a flight to filter the dashboard).





### 🖼️ 5. Build Aircraft Image (Optional)

*Note: This requires the **Dalvany Image** plugin.*
[Plugin Link](https://grafana.com/grafana/plugins/dalvany-image-panel/)

1. **Add Visualization** > Select **Image**.
2. **Datasource:** Select your Loki datasource.
3. **Query (Loki):** Same query as above.
4. **Query Options:** Set Type to **Instant**.
5. **Transformations:**
* **Filter by value:** Filter `call` Match 'Is equal' to variable **${Flight}**.
* **Limit:** 1


6. **Panel Settings:**
* **Image URL:** Point to a public repo of aircraft images, dynamically inserting the `${type}` variable.
* **Example:** `https://github.com/YourRepo/images/blob/main/${type}.jpg?raw=true`
* **Metric Field:** Select `type` (e.g., B739).
* **Suffix:** .jpg?raw=true



### 🎨 6. Build the Header (Text Panel)

1. **Add Visualization** > Select **Text**.
2. **Mode:** HTML.
3. **Content:**
```html
<div style="background-color: #01426A; padding: 20px; text-align: center; border-radius: 5px;">
  <h2 style="color: white; margin: 0;">✈️ Alaska Airlines Flight Tracker</h2>
  <p style="color: #00B4D8; margin: 0;">Live Telemetry via OpenSky Network</p>
</div>

```



**Final Step:** Drag and resize the panels on your grid to match the layout. Save the dashboard!
