import openai
import os
from datetime import datetime
from dotenv import load_dotenv
import sys

sys.stdout.reconfigure(encoding="utf-8")


# Load environment variables from .env file
load_dotenv()

directory = "error"
success_directory = "logs"

gpt_secret_key = os.getenv("CHAT_GPT_SECRET")

gpt_model = "gpt-3.5-turbo"


def create_success_log(data):
    # Get the current date and time
    current_date = datetime.now()

    # Format the date as a string to use in the filename (e.g., "2023-09-13.txt")
    formatted_date = current_date.strftime("%Y-%m-%d")
    log_timestamp = current_date.strftime("%Y-%m-%d %H:%M:%S")

    # Define the filename with the formatted date
    file_name = f"{success_directory}/{formatted_date}.txt"

    if not os.path.exists(success_directory):
        os.makedirs(success_directory)

    # Check if the file already exists, if not, create it
    if not os.path.exists(file_name):
        with open(file_name, "w", encoding="utf-8") as file:
            pass  # Creates an empty file

    # Append the data to the file
    with open(file_name, "a", encoding="utf-8") as file:
        file.write(f"{log_timestamp} SUCCESS {data}\n")


def create_error(data):
    # Get the current date and time
    current_date = datetime.now()

    # Format the date as a string to use in the filename (e.g., "2023-09-13.txt")
    formatted_date = current_date.strftime("%Y-%m-%d")
    log_timestamp = current_date.strftime("%Y-%m-%d %H:%M:%S")

    # Define the filename with the formatted date
    file_name = f"{directory}/{formatted_date}.txt"

    if not os.path.exists(directory):
        os.makedirs(directory)

    # Check if the file already exists, if not, create it
    if not os.path.exists(file_name):
        with open(file_name, "w", encoding="utf-8") as file:
            pass  # Creates an empty file

    # Append the data to the file
    with open(file_name, "a", encoding="utf-8") as file:
        file.write(f"{log_timestamp} ERROR {data}\n")


def sentiment_analysis(text):
    try:
        create_success_log("Sending data to chat-gpt server for sentiment score...")
        openai.api_key = gpt_secret_key
        prompt = text
        completion = openai.ChatCompletion.create(
            model=gpt_model,
            timeout=10,
            messages=[
                {
                    "role": "system",
                    "content": "As a commercial property & casualty underwriter, provide sentiment scores on a scale of 1 to 10 where 1 is the most negative and 10 is the most positive.",
                },
                {
                    "role": "system",
                    "content": "give response in json format with keys score",
                },
                {"role": "user", "content": prompt},
            ],
        )

        response = completion.choices[0].message.content  # type: ignore
        return response
    except Exception as e:
        create_error(e)
        return "error"


def sentiment_analysis_summary(text):
    try:
        create_success_log("Sending data to chat-gpt server for summary...")
        openai.api_key = gpt_secret_key
        prompt = text
        completion = openai.ChatCompletion.create(model=gpt_model, messages=prompt)

        response = completion.choices[0].message.content  # type: ignore
        return response
    except Exception as e:
        create_error(e)
        return "error"
