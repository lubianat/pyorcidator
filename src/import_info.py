import os
import sys
import requests
import json

# Send API request to Numista
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
employment_data = data["activities-summary"]["employments"]
education_data = data["activities-summary"]["educations"]
publication_data = data["activities-summary"]["works"]


with open("sample.json", "w+") as f:
    f.write(json.dumps(data, indent=4))
