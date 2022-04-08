import clipboard
from .dictionaries.all import dicts
from SPARQLWrapper import SPARQLWrapper, JSON
from .wikidata_lookup import search_wikidata
import re
from dataclasses import dataclass
from pathlib import Path
import json

HERE = Path(__file__).parent.resolve()
DEGREE_PATH = HERE.joinpath("dictionaries", "degree.json")


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
            qid = input(f"What is the qid for: '{string}' ? ")
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
        with DEGREE_PATH.open("w") as f:
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
            grid = a["disambiguated-organization"][
                "disambiguated-organization-identifier"
            ]
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
            grid = a["disambiguated-organization"][
                "disambiguated-organization-identifier"
            ]

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


def process_education_entries(
    qs, subject_qid, ref, education_entries, property_id="P69"
):

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
