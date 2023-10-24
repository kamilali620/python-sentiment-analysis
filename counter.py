import json
import os

json_file_path = "counter.json"


def counter(responseID=1, offset=0, limit=25):
    try:
        with open(json_file_path, "r") as json_file:
            data = json.load(json_file)
            data["responseID"] = responseID
            data["offset"] = data["offset"] + limit

            with open(json_file_path, "w") as json_file:
                json.dump(data, json_file, indent=2)

            return data

    except FileNotFoundError:
        data = {"responseID": responseID, "offset": offset, "limit": 25}
        with open(json_file_path, "w") as json_file:
            json.dump(data, json_file, indent=2)

        return data


def remove_file():
    try:
        # Attempt to remove the file
        os.remove(json_file_path)
    except FileNotFoundError:
        print(f"File '{json_file_path}' not found.")
    except Exception as e:
        print(f"An error occurred while trying to remove the file: {str(e)}")


counter()
