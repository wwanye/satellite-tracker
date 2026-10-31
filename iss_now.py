from skyfield.api import load, wgs84

url = "https://celestrak.org/NORAD/elements/gp.php?GROUP=stations&FORMAT=tle"
satellites = load.tle_file(url)
iss = None

for sat in satellites:
    if sat.name == "ISS (ZARYA)":
        iss = sat
        break

ts = load.timescale()
t = ts.now()
position = iss.at(t)

lat, lon = wgs84.latlon_of(position)
height = wgs84.height_of(position) #this will return the distance from the surface of the Earth in au which is the distance from the earth to the sun.

height = height.km #convert to km
name = iss.name

print(f"Tracking the {name}")
print(f"Latitude: {lat.degrees:.2f}°")
print(f"Longitude: {lon.degrees:.2f}°")
print(f"Height: {height:.0f} km")