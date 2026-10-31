from turtle import position

from skyfield.api import load, wgs84
from zoneinfo import ZoneInfo


def load_satellites():
    """ Load the satellite TLE data from Celestrak and return the list of satellites.
    If the TLE data is already downloaded and is less than 1 day old, it will be loaded from the local file instead of downloading it again."""

    url = "https://celestrak.org/NORAD/elements/gp.php?GROUP=stations&FORMAT=tle"
    if load.exists("gp.php") == False or load.days_old("gp.php") > 1:
        satellites = load.tle_file(url, reload=True)
    else:
        satellites = load.tle_file("gp.php")
    return satellites

def find_satellite(satellites, name):
    """Find a satellite by name in the list of satellites."""
    for sat in satellites:
        if sat.name == name:
            return sat
    return None

def current_position(satellite, time):
    """Get the current position of a satellite."""
    position = satellite.at(time)
    lat, lon = wgs84.latlon_of(position)
    height = wgs84.height_of(position)
    return lat.degrees, lon.degrees, height.km

def find_passes(satellite, observer, start_time, end_time):
    """Find the passes of a satellite over an observer's location between start_time and end_time."""
    difference = satellite - observer
    times, events = satellite.find_events(observer, start_time, end_time, altitude_degrees=10.0)
    passes = []

    for ti, event in zip(times, events):
        event_name = event_names[event]
        local_time = ti.astimezone(eastern)

        altitude = None 
        if event == 1:
            alt, az, distance = difference.at(ti).altaz()
            altitude = alt.degrees

        entry = { 
            "time": local_time,
            "event": event_name,
            "altitude": altitude 
        }
        passes.append(entry)

    return passes



eastern = ZoneInfo("America/New_York")
iss = None
ts = load.timescale()
t = ts.now()


#Clemsons position
clemson = wgs84.latlon(34.6834, -82.8374, elevation_m=221)
times, events = iss.find_events(clemson, t, t + 1.0, altitude_degrees=10.0)
event_names = ("Rise", "Highest point", "Set")


 #this will return the distance from the surface of the Earth in au which is the distance from the earth to the sun.

height = height.km #convert to km
name = iss.name
difference = iss - clemson

for ti, event in zip(times, events):
    event_name = event_names[event]
    local_time = ti.astimezone(eastern)
    

    if event_name == "Highest point":
        topocentric = difference.at(ti)
        alt, az, distance = topocentric.altaz()
        print(f"{local_time.strftime('%Y-%m-%d %H:%M:%S')} {event_name} of {name} Alt: {alt.degrees:.2f} degrees and Az: {az.degrees:.2f} degrees.")
    else:
        print(f"{local_time.strftime('%Y-%m-%d %H:%M:%S')} {event_name} of {name}")
        if event_name == "Set":
            print()