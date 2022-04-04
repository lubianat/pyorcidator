import os
import sys
import requests
import json
from helper import *

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

qs = process_item(qs, property_id, key, target_list)

with open("sample.json", "w+") as f:
    f.write(json.dumps(data, indent=4))

print(qs)
