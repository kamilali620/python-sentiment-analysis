import mysql.connector
import json
from review import (
    sentiment_analysis,
    sentiment_analysis_summary,
    create_success_log,
    create_error,
)
from counter import counter, remove_file
import time
from datetime import datetime
from dotenv import load_dotenv
import os
import re

# Load environment variables from .env file
load_dotenv()


def filter_prompt(text):
    cleaned_text = re.sub(r"[@#]\w+\b", "", text)
    cleaned_text = re.sub(
        r"[@#]\w+|[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U0001FB00-\U0001FBFF\U0001FC00-\U0001FCFF\U0001FD00-\U0001FDFF\U0001FE00-\U0001FEFF\U0001FF00-\U0001FFFF\U00020000-\U0002FFFF]",
        "",
        text,
        flags=re.UNICODE,
    )
    return cleaned_text


def extract_value(text):
    try:
        parsed_json = json.loads(text)
        # If parsing is successful, 'parsed_json' contains the parsed JSON object
        return parsed_json["score"]
    except Exception:
        # If parsing fails, handle the exception by returning -1
        return -1


def get_first_record(mydb):
    cursor = mydb.cursor()
    cursor.execute(f"SELECT ResponseID FROM usi.vw_content_filter_chatgpt LIMIT 1")
    myresult = cursor.fetchall()

    if myresult:
        return myresult[0][0]
    else:
        return None


def create_service_summary(
    mydb, ResponseID, ResponseService, SentimentJSON, SentimentSummary
):
    cursor = mydb.cursor()
    sql = "INSERT INTO usi.results_sentiment (ResponseID, ContentID, ResponseService, SentimentJSON, SentimentSummary,SentimentTier, AddDate, isActive) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"

    val = (
        ResponseID,
        0,
        ResponseService,
        SentimentJSON,
        SentimentSummary,
        "service",
        datetime.now(),
        1,
    )

    cursor.execute(sql, val)

    # create_success_log(
    #   f"inserting data into database for response id: {ResponseID} as a service")
    mydb.commit()


def create_company_summary(mydb, ResponseID, SentimentJSON, SentimentSummary):
    cursor = mydb.cursor()
    sql = "INSERT INTO usi.results_sentiment (ResponseID,ContentID, SentimentJSON, SentimentSummary,SentimentTier, AddDate, isActive) VALUES (%s, %s, %s, %s, %s, %s, %s)"

    val = (ResponseID, 0, SentimentJSON, SentimentSummary, "company", datetime.now(), 1)

    cursor.execute(sql, val)

    create_success_log(
        f"inserting data into database for response id: {ResponseID} as a company"
    )
    mydb.commit()


def process_reviews(mydb, pagination):
    source = ("facebook", "instagram", "twitter", "google", "yelp")
    cursor = mydb.cursor()
    company_json = []
    company_reviews = [
        {
            "role": "system",
            "content": "As a commercial property & casualty underwriter, provide a 3 to 4 sentence summary of the reviews. in 150 letters",
        }
    ]
    summary = ""

    for ContentService in source:
        cursor.execute(
            f"SELECT * FROM usi.vw_content_filter_chatgpt WHERE ResponseID = {pagination['responseID']} AND ContentService ='{ContentService}' AND (ContentText != NULL OR ContentText != '?') LIMIT {pagination['limit']} OFFSET 0"
        )
        myresult = cursor.fetchall()
        create_success_log(
            f"fetching data from database for response id: {pagination['responseID']} ContentService: {ContentService}"
        )
        if len(myresult) > 0:
            service_json = []

            service_reviews = [
                {
                    "role": "system",
                    "content": "As a commercial property & casualty underwriter, provide a 3 to 4 sentence summary of the reviews. in 150 letters",
                }
            ]

            for x in myresult:
                (
                    ResponseID,
                    ContentID,
                    ContentService,
                    ContentSource,
                    ContentDate,
                    ContentText,
                    ReviewRank,
                ) = x
                cleaned_text = filter_prompt(ContentText)
                if cleaned_text != "":
                    service_json.append({"review": str(ContentText)})

            service_reviews.append(
                {"role": "user", "content": json.dumps(service_json)}
            )

            summary = sentiment_analysis_summary(service_reviews)

            service_json = json.dumps(service_json)

            for x in myresult:
                (
                    ResponseID,
                    ContentID,
                    ContentService,
                    ContentSource,
                    ContentDate,
                    ContentText,
                    ReviewRank,
                ) = x
                cleaned_text = filter_prompt(ContentText)
                if cleaned_text != "":
                    score = sentiment_analysis(ContentText)
                    if score != "error":
                        sentiment_score = extract_value(score)
                        if sentiment_score != -1:
                            sql = "INSERT INTO usi.results_sentiment (ContentID, ResponseID, ResponseService, SentimentJSON, SentimentTier, SentimentScore, AddDate, isActive) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"

                            val = (
                                ContentID,
                                ResponseID,
                                ContentService,
                                service_json,
                                "review",
                                sentiment_score,
                                datetime.now(),
                                1,
                            )

                            cursor.execute(sql, val)

                            create_success_log(
                                f"inserting data into database for ResponseID: {ResponseID} ContentID: {ContentID} review: {ContentText} sentiment_score: {sentiment_score}"
                            )

                            mydb.commit()
                            # time.sleep(10)
                        else:
                            create_error(
                                f"Getting error in sentiment ResponseID: {ResponseID} ContentID: {ContentID} Review: {ContentText} Generated Score: {score}"
                            )
                    else:
                        create_error(
                            f"Getting error in sentiment ResponseID: {ResponseID} ContentID: {ContentID} Review: {ContentText} Generated Score: {score}"
                        )
                else:
                    create_error(
                        f"Getting error in sentiment ResponseID: {ResponseID} ContentID: {ContentID} Review: {ContentText} Generated Score: error"
                    )

            create_service_summary(
                mydb, pagination["responseID"], ContentService, service_json, summary
            )
            company_json.append({"review": summary})
            pagination = counter(pagination["responseID"], 0)

    company_reviews.append({"role": "user", "content": json.dumps(company_json)})
    company_summary = sentiment_analysis_summary(company_reviews)
    company_json = json.dumps(company_json)
    create_company_summary(
        mydb, pagination["responseID"], company_json, company_summary
    )


try:
    # Access environment variables
    host = os.getenv("HOST")
    user = os.getenv("USER")
    password = os.getenv("PASSWORD")
    database = os.getenv("DATABASE")

    # Creating connection object
    mydb = mysql.connector.connect(
        host=host, user=user, password=password, database=database
    )
    print(":::::::::: START ::::::::::")
    # 1, 4, 10, 12, 25, 30, 35
    responseID = get_first_record(mydb)
    if responseID:
        remove_file()
        # responseID = 35 #add any response id manually
        pagination = counter(responseID)
        start_time = time.time()
        create_success_log("process start ...")
        process_reviews(mydb, pagination)
        create_success_log("process end ...")
        end_time = time.time()
        duration = end_time - start_time
        create_success_log(
            f"Total time interval for ResponseID: {responseID} - Time: {duration} seconds"
        )
        print(":::::::::: END ::::::::::")

    else:
        print(":::::::::: END ::::::::::")
    # Close the cursor and the database connection
    mydb.close()
except Exception as e:
    print("::::::::::: ERROR :::::::::::")
    print(e)
