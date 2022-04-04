import json
import os, json

dicts = {}

path_to_json = "src/dictionaries"
json_files = [
    pos_json for pos_json in os.listdir(path_to_json) if pos_json.endswith(".json")
]

for json_file in json_files:
    keyword = json_file.split(".")[0]
    with open(f"src/dictionaries/{keyword}.json") as f:
        dicts[keyword] = json.loads(f.read())
