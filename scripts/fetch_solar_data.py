import requests
import json

def fetch_noaa_solar_data(lat, lon, api_key, output_path):
    """
    Fetch solar data from NOAA API for the given latitude and longitude.

    Args:
        lat (float): Latitude of the location.
        lon (float): Longitude of the location.
        api_key (str): Your NOAA API key.
        output_path (str): The file path to save the solar data.
    """
    # NOAA API endpoint
    api_url = "https://www.ncdc.noaa.gov/cdo-web/api/v2/datasets"

    # Set headers with API key
    headers = {
        "token": api_key
    }

    # Request parameters
    params = {
        "lat": lat,
        "lon": lon
    }

    # Send GET request
    response = requests.get(api_url, headers=headers, params=params)

    # Handle the response
    if response.status_code == 200:
        solar_data = response.json()

        # Save the data to a file
        with open(output_path, "w") as f:
            json.dump(solar_data, f, indent=4)
        print(f"Solar data saved at {output_path}")
    else:
        print(f"Failed to fetch solar data: {response.status_code}, {response.text}")

if __name__ == "__main__":
    # Vancouver, BC coordinates
    lat = 49.2827
    lon = -123.1207
    api_key = "dUHDgsgQknUuPgHHgZEYKAhCUiPsvpLj"
    output_path = "../data/solar_data.json"
    fetch_noaa_solar_data(lat, lon, api_key, output_path)
