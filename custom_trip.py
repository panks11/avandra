from flask import Flask, render_template, request
import logging
import openai
import time
import re
import os
from nltk.tokenize import sent_tokenize

openai.api_key = os.environ.get('gpt_key')

# Configure logging
logging.basicConfig(filename='app.log', level=logging.DEBUG)

app = Flask(__name__)
questions = [
    "Hello! Welcome to the AI-based Trip Planner. I'm here to help you plan your dream trip. Please answer some questions so I can help you.",
    "What is your Current Location?",
    "Where are you planning your trip?",
    "What is your allocated budget for the trip?",
    "Number of days you are planning?",
    "Will you be travelling solo or in a group?"
]
responses = {}

def get_response(response):

    temp = f"""I have a dictionary of questions as keys and user response as values, based on user responses generate recommendation based on location where user wants to travel and not the current location, also do consider other responses too, don't write code just generate recommendations :
             {response}

              OUTPUT : Based on your preference here are some recommendations -   """

    response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
            {"role": "user", "content": temp}
        ],
    temperature = 0.3
    )
    chat_response = response["choices"][0]["message"]["content"]
    return chat_response

import requests

api_key = os.environ.get('weather_api')

def get_weather_data(city):
    """Makes an API request to a URL and returns the data as a Python object.

    Args:
        query_url (str): URL formatted for OpenWeather's city name endpoint

    Returns:
        dict: Weather information for a specific city
    """
    base_url = 'http://api.openweathermap.org/data/2.5/forecast'
    params = {
        'q': city,
        'appid': api_key,
        'cnt': 15
    }

    response = requests.get(base_url, params=params)
    query_url  = f"http://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&appid={api_key}"
    response = requests.post(query_url)
    #data = response.read()
    #return json.loads(data)
    return response.text

def chat(system, user_assistant):
    assert isinstance(system, str), "`system` should be a string"
    assert isinstance(user_assistant, list), "`user_assistant` should be a list"
    system_msg = [{"role": "system", "content": system}]
    user_assistant_msgs = [
        {"role": "assistant", "content": user_assistant[i]} if i % 2 else {"role": "user", "content": user_assistant[i]}
        for i in range(len(user_assistant))]

    msgs = system_msg + user_assistant_msgs
    response = openai.ChatCompletion.create(model="gpt-3.5-turbo",
                                            messages=msgs)
    status_code = response["choices"][0]["finish_reason"]
    assert status_code == "stop", f"The status code was {status_code}."
    return response["choices"][0]["message"]["content"]

@app.route('/')
def home():
    return render_template('q_index.html', question=questions[0])

@app.route('/answer', methods=['POST'])
def answer():
    question = request.form['question']
    response = request.form['response']
    responses[question] = response

    index = questions.index(question)
    if index + 1 < len(questions):
        next_question = questions[index + 1]
        return render_template('q_index.html', question=next_question)
    else:
        logging.info(responses)
        del responses["Hello! Welcome to the AI-based Trip Planner. I'm here to help you plan your dream trip. Please answer some questions so I can help you."]
        ai_response = get_response(responses)
        logging.info(ai_response)

        response_list = re.split(r'\d+\.\s+', ai_response)[1:]
        logging.info(response_list)
        # Create a prompt
        location = responses['Where are you planning your trip?']

        weather_data = eval(get_weather_data('mumbai'))

        user_msg_weather = f"In {location.lower()} at midday tomorrow, the temperature is forecast to be {weather_data['main']['temp']}°C, the wind speed is forecast to be {weather_data['wind']['speed']} m/s, and the value of visibility is forecast to be {weather_data['visibility']}. Give a detailed overview on the weather conditons based on given data."

        # Call GPT
        time.sleep(3)
        response_activities = chat("You are a travel guide.", [user_msg_weather])
        places_list = response_activities.split(". ")
        places_list = [place.strip() for place in places_list if place.strip()]

        return render_template('q_index.html', responses=[response_list, places_list])

if __name__ == '__main__':
    app.run(debug=True,port=5001)
