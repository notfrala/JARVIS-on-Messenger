import os

import requests

import config
from templates.text import TextTemplate

GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY', config.GOOGLE_MAPS_API_KEY)
OPEN_WEATHER_MAP_ACCESS_TOKEN = os.environ.get('OPEN_WEATHER_MAP_ACCESS_TOKEN', config.OPEN_WEATHER_MAP_ACCESS_TOKEN)


def process(input, entities):
    output = {}
    try:
        r = requests.get(
            'https://maps.googleapis.com/maps/api/geocode/json?address=' + entities['weather_location'][0][
                'value'] + '&key=' + GOOGLE_MAPS_API_KEY)
        location_data = r.json()
        r = requests.get('http://api.openweathermap.org/data/2.5/weather?lat=' + str(
            location_data['results'][0]['geometry']['location']['lat']) + '&lon=' + str(
            location_data['results'][0]['geometry']['location'][
                'lng']) + '&units=metric&appid=' + OPEN_WEATHER_MAP_ACCESS_TOKEN)
        weather_data = r.json()
        output['input'] = input
        temperature_in_fahrenheit = weather_data['main']['temp'] * 1.8 + 32
        degree_sign = u'\N{DEGREE SIGN}'
        headers = {"accept": "application/json"}
        r = requests.get('https://api.openaq.org/v2/measurements?limit=1&page=1&offset=0&sort=desc&unit=µg/m³&coordinates=' + str(
            location_data['results'][0]['geometry']['location']['lat']) + ',' + str(
            location_data['results'][0]['geometry']['location']['lng']) + '&radius=5000&order_by=datetime&sensorType=reference%20grade', headers=headers)
        aq_data = r.json()
        ppc = response['results'][0]['value']
        
        # EPA air quality index translation 
        # Based on Particle Pollution Concentration (µg/m3)
        qualities = {
            'Good': (0.0,12.0),
            'Moderate': (12.1,35.4),
            'Unhealthy for Sensitive Groups': (35.5,55.4),
            'Unhealthy': (55.5, 150.4),
            'Very Unhealthy': (150.5, 250.4)
        }
        
        for diag,vals in qualities.items():
            if ppc >= vals[0] and ppc <= vals[1]:
                quality = diag
                break
        else:
            quality = 'Error'
        
        aq = quality + ' ' + str(ppc) + ' ' + str(response['results'][0]['unit'])  
        
        output['output'] = TextTemplate(
            'Location: ' + location_data['results'][0]['formatted_address'] + '\nWeather: ' +
            weather_data['weather'][0][
                'description'] + '\nTemperature: ' + str(
                weather_data['main']['temp']) + ' ' + degree_sign + 'C / ' + str(
                temperature_in_fahrenheit) + ' ' + degree_sign + '\nAir Quality: ' + aq + 'F\n- Info provided by OpenWeatherMap').get_message()
        output['success'] = True
    except:
        error_message = 'I couldn\'t get the weather info you asked for.'
        error_message += '\nPlease ask me something else, like:'
        error_message += '\n  - tell me the weather in London'
        error_message += '\n  - weather Delhi'
        error_message += '\n  - What\'s the weather in Texas?'
        output['error_msg'] = TextTemplate(error_message).get_message()
        output['success'] = False
    return output
