import json
import requests
from datetime import datetime
import pytz
import time
import re


def web_request(url, params):
    try:
        res = requests.get(url=url, params=params)
        return res.json()
    except:
        return False


class Location:

    def __init__(self, location, keys):
        self.google_api_key = keys["google_api_key"]
        self.here_api_key = keys["here_api_key"]
        self.ipgeo_api_key = keys["ipgeo_api_key"]

        # TODO Break off if statement
        # re_pattern = "^[-+]?(?:[1-8]?\d(?:\.\d+)?|90(?:\.0+)?),\s*[-+]?(?:180(?:\.0+)?|(?:(?:1[0-7]\d)|(?:[1-9]?\d))(?:\.\d+)?)$"
        # isLatLng = re.search(re_pattern, location)

        geo_url = "https://maps.googleapis.com/maps/api/geocode/json"
        geo_params = {
            "address": location,
            "key": self.google_api_key,
        }

        geo_res_json = web_request(url=geo_url, params=geo_params)
        # ! Add error handling in the event of failure of web request
        if not geo_res_json:
            print("service unavailble")
            exit(1)

        self.lat = geo_res_json["results"][0]["geometry"]["location"]["lat"]
        self.lng = geo_res_json["results"][0]["geometry"]["location"]["lng"]
        self.formatted_address = geo_res_json["results"][0]["formatted_address"]

        tz_url = "https://maps.googleapis.com/maps/api/timezone/json"
        tz_params = {
            "location": str(self.lat) + "," + str(self.lng),
            "key": self.google_api_key,
            "timestamp": time.time(),
        }

        tz_res_json = web_request(tz_url, tz_params)
        # ! Add error handling in the event of failure of web request
        if not geo_res_json:
            print("service unavailble")
            exit(1)

        self.time_zone_id = tz_res_json["timeZoneId"]
        self.dst_offset = tz_res_json["dstOffset"]
        self.raw_offset = tz_res_json["rawOffset"]

    def __str__(self):
        return json.dumps(
            {
                "lat": self.lat,
                "lng": self.lng,
                "formatted_address": self.formatted_address,
                "time_zone_id": self.time_zone_id,
                "dst_offset": self.dst_offset,
                "raw_offset": self.raw_offset,
            }
        )

    def solar(self):
        # The API endpoint
        solar_url = "https://api.sunrise-sunset.org/json"
        payload = {
            "lat": self.lat,
            "lng": self.lng,
            "date": "today",
            "formatted": 0,
        }
        response_json = web_request(solar_url, params=payload)

        solar_astronomy_url = "https://api.ipgeolocation.io/astronomy"
        ip_geo_payload = {
            "lat": self.lat,
            "long": self.lng,
            "apiKey": "03d85e52656f4ba19085aeee8c72d759",
        }
        solar_astro_res_json = web_request(solar_astronomy_url, ip_geo_payload)

        return {
            "astro_twilight_begin": self.utc_to_local(
                response_json["results"]["astronomical_twilight_begin"],
                self.time_zone_id,
            ),
            "nautical_twilight_begin": self.utc_to_local(
                response_json["results"]["nautical_twilight_begin"], self.time_zone_id
            ),
            "civil_twilight_begin": self.utc_to_local(
                response_json["results"]["civil_twilight_begin"], self.time_zone_id
            ),
            "sunrise": self.utc_to_local(
                response_json["results"]["sunrise"], self.time_zone_id
            ),
            "solar_noon": self.utc_to_local(
                response_json["results"]["solar_noon"], self.time_zone_id
            ),
            "sunset": self.utc_to_local(
                response_json["results"]["sunset"], self.time_zone_id
            ),
            "civil_twilight_end": self.utc_to_local(
                response_json["results"]["civil_twilight_end"], self.time_zone_id
            ),
            "nautical_twilight_end": self.utc_to_local(
                response_json["results"]["nautical_twilight_end"], self.time_zone_id
            ),
            "astronomical_twilight_end": self.utc_to_local(
                response_json["results"]["astronomical_twilight_end"], self.time_zone_id
            ),
            "day_length": response_json["results"]["day_length"],
            "sun_altitude": round(solar_astro_res_json["sun_altitude"], 2),
            "sun_azimuth": round(solar_astro_res_json["sun_azimuth"], 2),
            "sun_distance_km": round(solar_astro_res_json["sun_distance"]),
            "sun_distance_miles": round(
                self.km_to_miles(solar_astro_res_json["sun_distance"])
            ),
            "sun_distance_au": round(
                self.km_to_au(solar_astro_res_json["sun_distance"]), 6
            ),
            "observation_time": datetime.now(pytz.timezone(self.time_zone_id)).strftime(
                "%c %z"
            ),
        }

    def lunar(self):
        lunar_here_res = web_request(
            "https://weather.cc.api.here.com/weather/1.0/report.json",
            {
                "product": "forecast_astronomy",
                "name": self.formatted_address,
                "apiKey": self.here_api_key,
            },
        )
        lunar_here = lunar_here_res["astronomy"]["astronomy"][0]

        lunar_ipgeo_res = web_request(
            "https://api.ipgeolocation.io/astronomy",
            {
                "lat": self.lat,
                "long": self.lng,
                "apiKey": self.ipgeo_api_key,
            },
        )

        return {
            "moonrise": lunar_ipgeo_res["moonrise"] + ":00",
            "moonset": lunar_ipgeo_res["moonset"] + ":00",
            "moon_phase": lunar_here["moonPhase"],
            "moon_phase_desc": lunar_here["moonPhaseDesc"],
            "altitude": round(lunar_ipgeo_res["moon_altitude"], 2),
            "azimuth": round(lunar_ipgeo_res["moon_azimuth"], 2),
            "parallactic_angle": round(lunar_ipgeo_res["moon_parallactic_angle"], 2),
            "distance_km": round(lunar_ipgeo_res["moon_distance"]),
            "distance_mi": round(self.km_to_miles(lunar_ipgeo_res["moon_distance"])),
            "observation_time": datetime.now(pytz.timezone(self.time_zone_id)).strftime(
                "%c %z"
            ),
        }

    def km_to_miles(self, km):
        return km * 0.62137119

    def km_to_au(self, km):
        return km * 6.6846e-9

    def utc_to_local(self, timestamp, timezone):
        format = "%Y-%m-%dT%H:%M:%S+00:00"
        utc_date = datetime.strptime(timestamp, format)
        local_tz = pytz.timezone(timezone)  # Specify your local timezone
        local_dt = utc_date.replace(tzinfo=pytz.utc).astimezone(local_tz)
        return local_dt.strftime("%H:%M:%S")
