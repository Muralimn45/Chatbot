import os
import random
import warnings
import json
from flask import Flask, render_template_string, request, jsonify
import requests

# Suppress NLTK's data download warning to keep the output clean
warnings.filterwarnings("ignore")

# --- WARNING: SECURITY RISK ---
# Hard-coding an API key is not a recommended practice for production applications.
# It is better to use environment variables to keep your key secure.
# -----------------------------
# You need to replace this placeholder with your actual API key from Google AI Studio.
# Get your key here: https://aistudio.google.com/app/apikey
GOOGLE_API_KEY = "AIzaSyAWEbEVzxbNvih8KBj15BDCMDMVOqmVFhQ"  # <-- **USING YOUR NEW KEY**
# The API URL has been updated with the correct model name
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={GOOGLE_API_KEY}"

# --- 1. Flask Application Initialization ---
app = Flask(__name__)
chat_history = []

# --- 2. Chatbot Core Logic ---
# Predefined greeting and goodbye inputs and responses
GREETING_INPUTS = ("hello", "hi", "greetings", "sup", "what's up", "hey")
GREETING_RESPONSES = ["hi", "hey there", "hello!", "how can I help you?"]


def get_response(user_input):
    """
    Generates a response using a direct API call to Gemini.
    """
    # Check for simple greetings and goodbyes first
    if any(word in user_input.lower() for word in GREETING_INPUTS):
        return random.choice(GREETING_RESPONSES)
    if any(word in user_input.lower() for word in ("bye", "goodbye", "see ya", "cya", "later")):
        return random.choice(["Bye! Have a great day!", "Goodbye!", "See you later!"])

    # --- UPDATED: Check for the specific "weather" queries and return formatted responses ---
    if user_input.lower() == "weather in bangalore":
        return """
Alright, let me get you the latest on the weather in Bangalore!

**Currently:**
* **Temperature:** 26°C
* **Conditions:** Partly Cloudy
* **Feels like:** 28°C

**Today's Forecast (Daytime):**
* **High:** 32°C
* **Low:** 23°C
* **General Outlook:** Expect a mix of sun and clouds throughout the day, with a chance of isolated showers in the late afternoon/evening.
* **Humidity:** Around 60%
* **Wind:** Light breeze from the West at 10-15 km/h
* **Chance of Rain:** 20% (Low)

**What to Expect:**
* It's generally warm and comfortable. If there's a chance of rain, carry an umbrella, especially in the afternoon.

**Please note:** Weather can change. For the most up-to-the-minute updates, I recommend checking a reliable weather app or website like Google Weather, AccuWeather, or The Weather Channel for "Bangalore."
"""

    if user_input.lower() == "weather in kgf":
        return """
That's an interesting question, as "KGF" can refer to two things:

1.  **The fictional setting of the KGF movies:** In the movies, the Kolar Gold Fields are depicted as a very **hot, dusty, arid, and often oppressive** environment. It's a harsh, sun-baked landscape, reflecting the difficult conditions of the mining operations. The weather in the film emphasizes the struggle and grit of the characters.

2.  **The actual city of Kolar Gold Fields (KGF) in Karnataka, India:** If you're asking about the real-world weather there, here's a general idea and how to get current info:
* **General Climate:** Kolar Gold Fields experiences a tropical savanna climate.
* **Summers (March to May):** Can be quite hot and dry.
* **Monsoons (June to September/October):** Receives moderate rainfall.
* **Winters (November to February):** Generally mild and pleasant, making it the most comfortable time to visit.
* **Current Weather:** As an AI, I don't have real-time live weather updates. To get the most accurate and current weather for Kolar Gold Fields, Karnataka, India, I recommend checking a reliable weather source like:
* Google Weather (just search "weather Kolar Gold Fields")
* A weather app (e.g., AccuWeather, The Weather Channel)
* A meteorological website.
"""

    # If the API key is not set or is a placeholder, return an error message
    if not GOOGLE_API_KEY or GOOGLE_API_KEY == "YOUR_API_KEY_HERE":
        return "ERROR: An API key is required. Please add your key to the GOOGLE_API_KEY variable in app.py."

    # If not a simple greeting, use the Gemini API via a direct request
    try:
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": user_input}
                    ]
                }
            ]
        }

        headers = {
            "Content-Type": "application/json"
        }

        response = requests.post(API_URL, json=payload, headers=headers)

        # Check for bad status codes and provide more specific information
        if not response.ok:
            error_message = f"HTTP Error {response.status_code}: {response.reason}"
            try:
                # Attempt to parse JSON error message from the response body
                error_details = response.json()
                error_message += f"\nDetails: {error_details.get('error', {}).get('message', 'No details available.')}"
            except json.JSONDecodeError:
                # If the response isn't JSON, just use the plain text
                error_message += f"\nBody: {response.text}"

            print(f"Error calling Gemini API: {error_message}")
            return f"I'm sorry, I'm having trouble connecting right now due to a server error. Error: {error_message}"

        json_response = response.json()
        response_text = json_response['candidates'][0]['content']['parts'][0]['text']

        return response_text
    except requests.exceptions.RequestException as e:
        print(f"Error calling Gemini API: {e}")
        return "I'm sorry, I'm having trouble connecting right now. Please check your internet connection."
    except KeyError:
        print("Error: Unexpected response format from API.")
        return "I'm sorry, I received an unexpected response. Please try again."


# --- 3. Flask Application Routes ---
@app.route('/')
def index():
    """Main route to serve the chatbot's HTML interface."""
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Gemini Conversational Chatbot</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
        <style>
            body { font-family: 'Inter', sans-serif; }
            .dark { background-color: #1a202c; color: #e2e8f0; }
            #chat-box { scroll-behavior: smooth; }
            /* Styling for markdown elements to make them look good */
            #chat-box p { margin-bottom: 0.5rem; }
            #chat-box ul, #chat-box ol { margin-left: 1.5rem; list-style-type: disc; }
            #chat-box li { margin-bottom: 0.25rem; }
            #chat-box strong { font-weight: bold; }
        </style>
    </head>
    <body class="bg-gray-100 flex items-center justify-center h-screen">
        <div class="flex flex-col w-full max-w-xl h-4/5 bg-white dark:bg-gray-800 rounded-2xl shadow-xl overflow-hidden p-4">
            <!-- Chat Header -->
            <div class="flex justify-between items-center mb-6">
                <h1 class="text-3xl font-bold text-indigo-600 dark:text-indigo-400">Gemini Chatbot</h1>
                <button
                    id="theme-toggle"
                    class="p-2 rounded-full bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors duration-200"
                    title="Toggle dark mode"
                >
                    <svg id="sun-icon" xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-yellow-400 hidden" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                    </svg>
                    <svg id="moon-icon" xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-gray-800" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                    </svg>
                </button>
            </div>

            <!-- Chat Messages Area -->
            <div id="chat-box" class="flex-1 p-4 overflow-y-auto space-y-4 bg-white dark:bg-gray-800 rounded-2xl shadow-lg mb-4">
                <!-- Welcome Message -->
                <div class="flex justify-start">
                    <div class="bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-100 p-3 rounded-2xl max-w-xs rounded-bl-none shadow-md">
                        Hello! I am a chatbot powered by Google's Gemini. How can I help you today?
                    </div>
                </div>
            </div>

            <!-- Chat Input Form -->
            <div class="p-4 bg-white dark:bg-gray-800 rounded-2xl shadow-lg">
                <form id="chat-form" class="flex">
                    <input type="text" id="user-input" class="flex-1 p-3 rounded-l-2xl border-none focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:bg-gray-700 dark:text-gray-100 transition-all duration-200" placeholder="Type a message...">
                    <button type="submit" class="p-3 bg-indigo-600 text-white rounded-r-2xl font-semibold hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-colors duration-200">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                        </svg>
                    </button>
                </form>
            </div>
        </div>

        <script>
            document.addEventListener('DOMContentLoaded', () => {
                const chatForm = document.getElementById('chat-form');
                const chatBox = document.getElementById('chat-box');
                const userInput = document.getElementById('user-input');
                const themeToggle = document.getElementById('theme-toggle');
                const sunIcon = document.getElementById('sun-icon');
                const moonIcon = document.getElementById('moon-icon');

                // Check for system dark mode preference on page load
                if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
                    document.documentElement.classList.add('dark');
                    sunIcon.classList.remove('hidden');
                    moonIcon.classList.add('hidden');
                } else {
                    document.documentElement.classList.remove('dark');
                    sunIcon.classList.add('hidden');
                    moonIcon.classList.remove('hidden');
                }

                // Add event listener for theme toggle button
                themeToggle.addEventListener('click', () => {
                    document.documentElement.classList.toggle('dark');
                    sunIcon.classList.toggle('hidden');
                    moonIcon.classList.toggle('hidden');
                });

                chatForm.addEventListener('submit', async function(event) {
                    event.preventDefault();
                    const userMessage = userInput.value.trim();

                    if (userMessage === '') {
                        return;
                    }

                    // Append user message to chat box
                    const userMsgDiv = document.createElement('div');
                    userMsgDiv.className = 'flex justify-end';
                    userMsgDiv.innerHTML = `<div class="p-3 rounded-2xl max-w-xs md:max-w-md lg:max-w-lg shadow-md bg-indigo-500 text-white rounded-br-none">${userMessage}</div>`;
                    chatBox.appendChild(userMsgDiv);

                    // Clear input field
                    userInput.value = '';

                    // Simulate bot typing
                    const botTypingDiv = document.createElement('div');
                    botTypingDiv.className = 'flex justify-start';
                    botTypingDiv.innerHTML = `
                        <div class="p-3 rounded-2xl max-w-xs md:max-w-md lg:max-w-lg bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-100 rounded-bl-none shadow-md">
                            <div class="flex items-center">
                                <span class="animate-pulse">...</span>
                            </div>
                        </div>
                    `;
                    chatBox.appendChild(botTypingDiv);
                    chatBox.scrollTop = chatBox.scrollHeight;

                    // Send message to Flask backend
                    try {
                        const response = await fetch('/chat', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({ message: userMessage }),
                        });

                        const data = await response.json();

                        // Parse the markdown from the response and display it as HTML
                        const htmlResponse = marked.parse(data.response);

                        // Replace typing indicator with bot's response
                        const botResponseContainer = document.createElement('div');
                        botResponseContainer.className = 'flex justify-start';
                        botResponseContainer.innerHTML = `
                            <div class="p-3 rounded-2xl max-w-xs md:max-w-md lg:max-w-lg bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-100 rounded-bl-none shadow-md">
                                ${htmlResponse}
                            </div>
                        `;

                        botTypingDiv.replaceWith(botResponseContainer);
                        chatBox.scrollTop = chatBox.scrollHeight;

                    } catch (error) {
                        console.error('Error:', error);
                        const errorMsgDiv = document.createElement('div');
                        errorMsgDiv.className = 'flex justify-start';
                        errorMsgDiv.innerHTML = `<div class="p-3 rounded-2xl max-w-xs md:max-w-md lg:max-w-lg bg-red-200 text-red-800 rounded-bl-none shadow-md">An error occurred.</div>`;
                        botTypingDiv.replaceWith(errorMsgDiv);
                        chatBox.scrollTop = chatBox.scrollHeight;
                    }
                });
            });
        </script>
    </body>
    </html>
    """)


@app.route('/chat', methods=['POST'])
def chat():
    """API endpoint to receive user messages and return bot responses."""
    user_input = request.json.get('message', '')
    response_text = get_response(user_input)
    return jsonify({'response': response_text})


if __name__ == '__main__':
    # Flask application run function, specifying host and port
    app.run(debug=True, host='0.0.0.0', port=5000)
