import json
import os
import re
import sys
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

import click
import clipboard
import requests
from SPARQLWrapper import JSON, SPARQLWrapper

from .dictionaries.all import dicts
from .wikidata_lookup import search_wikidata

HERE = Path(__file__).parent.resolve()
DICTIONARIES_PATH = HERE.joinpath("dictionaries")
DEGREE_PATH = DICTIONARIES_PATH.joinpath("degree.json")


def render_orcid_qs(orcid):
    """Import info from ORCID for Wikidata."""
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
    education_entries = get_education_info(education_data)

    s = lookup_id(orcid, property="P496", default="LAST")

    ref = f'|S854|"https://orcid.org/{str(orcid)}"'

    if s == "LAST":
        qs = f"""CREATE
        {s}|Len|"{first_name} {last_name}"
    {s}|Den|"researcher"
    """
    else:
        qs = ""
    qs = (
        qs
        + f"""
    {s}|P31|Q5{ref}
    {s}|P106|Q1650915{ref}
    {s}|P496|"{orcid}"{ref}
    """
    )

    property_id = "P108"
    key = "institutions"
    target_list = employment_institutions
    qs = process_item(
        qs,
        property_id,
        original_dict=key,
        target_list=target_list,
        subject_qid=s,
        ref=ref,
    )

    qs = process_education_entries(
        qs,
        subject_qid=s,
        ref=ref,
        education_entries=education_entries,
        property_id="P69",
    )

    return qs


def create_qs_url(qs: str, open_browser: str) -> None:
    quoted_qs = quote(qs.replace("\t", "|").replace("\n", "||"), safe="")
    url = f"https://quickstatements.toolforge.org/#/v1={quoted_qs}\\"
    click.echo(qs)
    click.echo(url)
    if open_browser:
        webbrowser.open_new_tab(url)


@dataclass
class EducationEntry:
    """Class for capturing the info for an education entry on ORCID."""

    institution: str
    degree: str
    start_date: str = None
    end_date: str = None


def add_key(dictionary, string):
    """
    Prompts the user for adding a key to the target dictionary.

    Args:
        dictionary (dict): A reference dictionary containing strings as keys and Wikidata QIDs as values.
        string (str): A new key to add to the dictionary.

    Returns:
        dict: The updated dictionary.
    """

    clipboard.copy(string)
    predicted_id = search_wikidata(string)
    annotated = False

    while annotated == False:
        answer = input(
            f"Is the QID for '{string}'  \n "
            f"{predicted_id['id']} - {predicted_id['label']} "
            f"({predicted_id['description']}) ? (y/n) "
        )

        if answer == "y":
            dictionary[string] = predicted_id["id"]
            annotated = True
        elif answer == "n":
            qid = input(f"What is the QID for: '{string}' ? ")
            dictionary[string] = qid
            annotated = True
        else:
            print("Answer must be either 'y' or 'n'")

    return dictionary


def process_item(
    qs,
    property_id,
    original_dict,
    target_list,
    subject_qid,
    ref,
    qualifier_nested_dictionary={},
):
    global dicts
    for target_item in target_list:
        if re.findall("Q[0-9]*", target_item):
            qid = target_item
        else:
            qid = get_qid_for_item(original_dict, target_item)
        qs = (
            qs
            + f"""
        {subject_qid}|{property_id}|{qid}"""
        )

        if qualifier_nested_dictionary != {}:
            qualifier_pairs = qualifier_nested_dictionary[target_item]

            for key, value in qualifier_pairs.items():
                qs = qs + f"|{key}|{value}" + f"{ref}"
        else:
            qs = qs + f"{ref}"
    return qs


def get_qid_for_item(original_dict_name, target_item):
    """
    Looks up a qid in a global dict of dicts.
    If it is not present, it lets the user update the dict.
    """
    if target_item not in dicts[original_dict_name]:
        add_key(dicts[original_dict_name], target_item)
        with DICTIONARIES_PATH.joinpath(f"{original_dict_name}.json").open("w") as f:
            f.write(json.dumps(dicts[original_dict_name], indent=4, sort_keys=True))

    qid = dicts[original_dict_name][target_item]
    return qid


def lookup_id(id, property, default):
    """
    Looks up a foreign ID on Wikidata based on its specific property.
    """

    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
    query = f"""
    SELECT ?item ?itemLabel
    WHERE
    {{
        ?item wdt:{property} "{id}" .
    }}
    """
    sparql.setQuery(query)

    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    bindings = results["results"]["bindings"]
    if len(bindings) == 1:
        item = bindings[0]["item"]["value"].split("/")[-1]
        return item
    else:
        return default


def get_organization_list(data):
    organization_list = []
    for a in data:
        a = a["organization"]
        name = a["name"]
        if a["disambiguated-organization"] is None:
            continue
        if a["disambiguated-organization"]["disambiguation-source"] == "GRID":
            grid = a["disambiguated-organization"]["disambiguated-organization-identifier"]
            id = lookup_id(grid, "P2427", name)
            name = id
        organization_list.append(name)
    return organization_list


def get_date(entry, start_or_end="start"):
    date = entry[f"{start_or_end}-date"]
    if date is None:
        return ""

    month = "00"
    day = "00"

    if date["year"] is not None:
        year = date["year"]["value"]
        precision = 9

    if date["month"] is not None:
        month = date["month"]["value"]
        precision = 10

    if date["day"] is not None:
        day = date["day"]["value"]
        precision = 11

    return f"+{year}-{month}-{day}T00:00:00Z/{str(precision)}"


def get_education_info(data):
    organization_list = []

    for a in data:
        qualifiers = {}

        title = a["role-title"]
        degree_qid = get_qid_for_item("degree", title)

        start_date = get_date(a, "start")
        end_date = get_date(a, "end")

        a = a["organization"]
        name = a["name"]
        if (
            a["disambiguated-organization"]
            and "disambiguation-source" in a["disambiguated-organization"]
            and a["disambiguated-organization"].get("disambiguation-source") == "GRID"
        ):
            grid = a["disambiguated-organization"]["disambiguated-organization-identifier"]

            institution_qid = lookup_id(grid, "P2427", name)
        else:
            institution_qid = get_qid_for_item("institutions", name)

        entry = EducationEntry(
            degree=degree_qid,
            institution=institution_qid,
            start_date=start_date,
            end_date=end_date,
        )

        organization_list.append(entry)

    return organization_list


def process_education_entries(qs, subject_qid, ref, education_entries, property_id="P69"):

    # Quickstatements fails in the case of same institution for multliple degrees.
    # See https://www.wikidata.org/wiki/Help:QuickStatements#Limitation

    for entry in education_entries:
        if entry.start_date == "":
            qs = (
                qs
                + f"""
        {subject_qid}|{property_id}|{entry.institution}|P512|{entry.degree}{ref}"""
            )
        else:
            qs = (
                qs
                + f"""
            {subject_qid}|{property_id}|{entry.institution}|P512|{entry.degree}|P580|{entry.start_date}|P582|{entry.end_date}{ref}"""
            )
    return qs
