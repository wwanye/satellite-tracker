"""Core satellite tracking logic: load orbital data, find satellites, and predict passes."""

from zoneinfo import ZoneInfo

import numpy as np
from skyfield.api import load, wgs84

TLE_URL = "https://celestrak.org/NORAD/elements/gp.php?GROUP=stations&FORMAT=tle"
TLE_FILE = "gp.php"
EVENT_NAMES = ("Rise", "Highest point", "Set")
MIN_ALTITUDE_DEG = 10.0  # elevation mask: ignore anything lower in the sky than this


def load_satellites():
    """Load satellite TLE data from CelesTrak and return a list of satellites.

    Downloads fresh data only if the local file is missing or more than a day old,
    to keep predictions accurate without overloading CelesTrak's free service.
    """
    if not load.exists(TLE_FILE) or load.days_old(TLE_FILE) > 1:
        return load.tle_file(TLE_URL, filename=TLE_FILE, reload=True)
    return load.tle_file(TLE_FILE)


def find_satellite(satellites, name):
    """Find a satellite by name in the list of satellites. Returns None if not found."""
    for sat in satellites:
        if sat.name == name:
            return sat
    return None


def current_position(satellite, t):
    """Return the satellite's latitude (deg), longitude (deg), and altitude (km) at time t.

    Works with a single time or an array of times.
    """
    position = satellite.at(t)
    lat, lon = wgs84.latlon_of(position)
    height = wgs84.height_of(position)
    return lat.degrees, lon.degrees, height.km


def ground_track(satellite, ts, start_time, minutes=90):
    """Return arrays of latitude, longitude, and altitude for each minute of the next `minutes` minutes."""
    offsets_in_days = np.arange(0, minutes + 1) / 1440.0  # 1440 minutes in a day
    times = ts.tt_jd(start_time.tt + offsets_in_days)
    return current_position(satellite, times)


def find_passes(satellite, observer, start_time, end_time, tz):
    """Find passes of a satellite over an observer between start_time and end_time.

    Returns a list of dictionaries, one per event (rise, highest point, set),
    with the time converted to the given time zone. Highest-point events also
    include the peak altitude and azimuth in degrees.
    """
    difference = satellite - observer  # vector from the observer to the satellite
    times, events = satellite.find_events(
        observer, start_time, end_time, altitude_degrees=MIN_ALTITUDE_DEG
    )
    passes = []

    for ti, event in zip(times, events):
        altitude = None
        azimuth = None
        if event == 1:  # highest point
            alt, az, distance = difference.at(ti).altaz()
            altitude = alt.degrees
            azimuth = az.degrees

        passes.append({
            "time": ti.astimezone(tz),
            "event": EVENT_NAMES[event],
            "altitude": altitude,
            "azimuth": azimuth,
        })

    return passes


def main():
    """Print the ISS's current position and its passes over Clemson for the next 24 hours."""
    eastern = ZoneInfo("America/New_York")
    ts = load.timescale()
    t = ts.now()

    satellites = load_satellites()
    iss = find_satellite(satellites, "ISS (ZARYA)")
    if iss is None:
        print("ISS not found in the TLE data.")
        return

    lat, lon, height = current_position(iss, t)
    print(f"{iss.name} is above {lat:.2f}°, {lon:.2f}° at {height:.0f} km\n")

    clemson = wgs84.latlon(34.6834, -82.8374, elevation_m=221)
    for entry in find_passes(iss, clemson, t, t + 1.0, eastern):
        line = f"{entry['time'].strftime('%a %b %d, %I:%M:%S %p')}  {entry['event']}"
        if entry["altitude"] is not None:
            line += f" (altitude {entry['altitude']:.0f}°, azimuth {entry['azimuth']:.0f}°)"
        print(line)
        if entry["event"] == "Set":
            print()


if __name__ == "__main__":
    main()
