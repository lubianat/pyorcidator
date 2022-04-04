import os
import sys
import requests
import json
from helper import *
from dictionaries.all import *

if len(sys.argv) > 1:
    orcid = sys.argv[1]
else:
    orcid = input("ORCID:")

# From https://pub.orcid.org/v3.0/#!/Public_API_v2.0/viewRecord

url = "https://pub.orcid.org/v2.0/"
header = {"Accept": "application/json"}
payload = {"orcid": orcid}
r = requests.get(f"{url}{orcid}", headers=header)
data = r.json()

personal_data = data["person"]
employment_data = data["activities-summary"]["employments"]["employment-summary"]
education_data = data["activities-summary"]["educations"]
publication_data = data["activities-summary"]["works"]

first_name = personal_data["name"]["given-names"]["value"]
last_name = personal_data["name"]["family-name"]["value"]


employment_institutions = [a["organization"]["name"] for a in employment_data]


qs = f"""
CREATE
LAST|Len|"{first_name} {last_name}"
LAST|Den|"researcher"
LAST|P31|Q5
LAST|P106|Q1650915
LAST|P496|"{orcid}"
"""

property_id = "P108"
key = "institutions"
target_list = employment_institutions


for target_item in target_list:
    if target_item not in dicts[key]:
        add_key(dicts[key], target_item)
        with open(f"src/dictionaries/{key}.json", "w+") as f:
            f.write(json.dumps(dicts[key], indent=4, sort_keys=True))

    qid = dicts[key][target_item]
    qs = (
        qs
        + f"""
LAST|{property_id}|{qid}
    """
    )

with open("sample.json", "w+") as f:
    f.write(json.dumps(data, indent=4))

print(qs)
