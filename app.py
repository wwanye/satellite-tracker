"""Streamlit web app: track a satellite live and predict its passes over any location."""

from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st
from skyfield.api import load, wgs84

from tracker import (
    MIN_ALTITUDE_DEG,
    current_position,
    find_passes,
    find_satellite,
    ground_track,
    load_satellites,
)

st.set_page_config(page_title="Satellite Pass Predictor", page_icon="🛰️", layout="wide")


@st.cache_resource(ttl=3600)  # reuse the loaded data for an hour between page visits
def get_satellites():
    return load_satellites()


@st.cache_resource
def get_timescale():
    return load.timescale()


st.title("🛰️ Satellite Pass Predictor")
st.caption("Live orbital data from CelesTrak, propagated with Skyfield's SGP4 model.")

satellites = get_satellites()
ts = get_timescale()
t = ts.now()  # one shared "now" for every calculation on the page

# ---------- Sidebar: user settings ----------
names = [sat.name for sat in satellites]
default_index = names.index("ISS (ZARYA)") if "ISS (ZARYA)" in names else 0

with st.sidebar:
    st.header("Settings")
    sat_name = st.selectbox("Satellite", names, index=default_index)

    st.subheader("Your location")
    obs_lat = st.number_input("Latitude (°)", -90.0, 90.0, 34.6834, format="%.4f")
    obs_lon = st.number_input("Longitude (°)", -180.0, 180.0, -82.8374, format="%.4f")
    obs_elev = st.number_input("Elevation (m)", -500.0, 9000.0, 221.0)
    tz_name = st.selectbox(
        "Time zone",
        ["America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles", "UTC"],
    )
    hours = st.slider("Look ahead (hours)", 6, 72, 24, step=6)

satellite = find_satellite(satellites, sat_name)
observer = wgs84.latlon(obs_lat, obs_lon, elevation_m=obs_elev)
tz = ZoneInfo(tz_name)

# ---------- Current position ----------
lat, lon, height = current_position(satellite, t)

col1, col2, col3 = st.columns(3)
col1.metric("Latitude", f"{lat:.2f}°")
col2.metric("Longitude", f"{lon:.2f}°")
col3.metric("Altitude", f"{height:,.0f} km")

data_age_days = t - satellite.epoch
st.caption(
    f"Orbital data epoch: {satellite.epoch.utc_strftime('%Y-%m-%d %H:%M UTC')} "
    f"({data_age_days:.1f} days old). Predictions are most accurate near the epoch."
)

# ---------- Map ----------
st.subheader("Where it is now")
track_lat, track_lon, _ = ground_track(satellite, ts, t, minutes=90)

map_points = pd.concat(
    [
        pd.DataFrame({"lat": track_lat, "lon": track_lon, "color": "#4c8bf5", "size": 20000}),
        pd.DataFrame({"lat": [lat], "lon": [lon], "color": "#ff4b4b", "size": 150000}),
        pd.DataFrame({"lat": [obs_lat], "lon": [obs_lon], "color": "#2ecc71", "size": 80000}),
    ],
    ignore_index=True,
)
st.map(map_points, color="color", size="size")
st.caption("Red: current position · Blue: path over the next 90 minutes · Green: your location")

# ---------- Pass predictions ----------
st.subheader(f"Upcoming passes (next {hours} hours, above {MIN_ALTITUDE_DEG:.0f}°)")
passes = find_passes(satellite, observer, t, t + hours / 24, tz)

if not passes:
    st.info("No passes in this window. Try a longer look-ahead.")
else:
    rows = []
    for p in passes:
        peak = ""
        if p["altitude"] is not None:
            peak = f"{p['altitude']:.0f}° high, azimuth {p['azimuth']:.0f}°"
        rows.append({
            "Time": p["time"].strftime("%a %b %d, %I:%M:%S %p"),
            "Event": p["event"],
            "Peak": peak,
        })
    st.dataframe(pd.DataFrame(rows), hide_index=True)
    st.caption("Azimuth is the compass direction to look: 0° north, 90° east, 180° south, 270° west.")
