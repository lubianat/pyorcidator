import os
import sys
import requests
import json
from helper import *
from urllib.parse import quote

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
with open("sample.json", "w+") as f:
    f.write(json.dumps(data, indent=4))

personal_data = data["person"]
employment_data = data["activities-summary"]["employments"]["employment-summary"]
education_data = data["activities-summary"]["educations"]["education-summary"]
publication_data = data["activities-summary"]["works"]

first_name = personal_data["name"]["given-names"]["value"]
last_name = personal_data["name"]["family-name"]["value"]


employment_institutions = get_organization_list(employment_data)
education_institutions, qualifier_nested_dictionary = get_education_info(education_data)

s = lookup_id(orcid, property="P496", default="LAST")

ref = f'|S854|"https://orcid.org/{str(orcid)}"'


if s == "LAST":
    qs = "CREATE"
else:
    qs = ""
qs = (
    qs
    + f"""
{s}|Len|"{first_name} {last_name}"
{s}|Den|"researcher"
{s}|P31|Q5{ref}
{s}|P106|Q1650915{ref}
{s}|P496|"{orcid}"{ref}
"""
)

property_id = "P108"
key = "institutions"
target_list = employment_institutions
qs = process_item(
    qs, property_id, original_dict=key, target_list=target_list, subject_qid=s, ref=ref
)

property_id = "P69"
target_list = education_institutions

print(qualifier_nested_dictionary)
print(target_list)
qs = process_item(
    qs,
    property_id,
    original_dict=key,
    target_list=target_list,
    subject_qid=s,
    ref=ref,
    qualifier_nested_dictionary=qualifier_nested_dictionary,
)

clipboard.copy(qs)
print(qs)


quoted_qs = quote(qs.replace("\t", "|").replace("\n", "||"), safe="")
url = f"https://quickstatements.toolforge.org/#/v1={quoted_qs}\\"

print(url)
