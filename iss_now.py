from skyfield.api import load, wgs84
from zoneinfo import ZoneInfo

eastern = ZoneInfo("America/New_York")
url = "https://celestrak.org/NORAD/elements/gp.php?GROUP=stations&FORMAT=tle"

if load.exists("gp.php") == False or load.days_old("gp.php") > 1:
    satellites = load.tle_file(url, reload=True)
else:
    satellites = load.tle_file("gp.php")



iss = None

for sat in satellites:
    if sat.name == "ISS (ZARYA)":
        iss = sat
        break

ts = load.timescale()
t = ts.now()
position = iss.at(t)

#Clemsons position
clemson = wgs84.latlon(34.6834, -82.8374, elevation_m=221)
times, events = iss.find_events(clemson, t, t + 1.0, altitude_degrees=10.0)
event_names = ("Rise", "Highest point", "Set")


lat, lon = wgs84.latlon_of(position)
height = wgs84.height_of(position) #this will return the distance from the surface of the Earth in au which is the distance from the earth to the sun.

height = height.km #convert to km
name = iss.name

for ti, event in zip(times, events):
    name = event_names[event]
    local_time = ti.astimezone(eastern)
    print(local_time.strftime('%Y-%m-%d %H:%M:%S'), name)