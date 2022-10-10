"""
Helper functions for pyorcidator
"""

import json
import logging
import re
import requests
from SPARQLWrapper import JSON, SPARQLWrapper
from wdcuration import add_key
from .classes import EducationEntry
from .dictionaries import dicts, stem_to_path


logger = logging.getLogger(__name__)


def get_external_ids(data):
    id_list = data["person"]["external-identifiers"]["external-identifier"]
    id_dict = {}
    for id in id_list:
        id_dict[id["external-id-type"]] = id["external-id-value"]
    return id_dict


def render_orcid_qs(orcid):
    """
    Import info from ORCID for Wikidata.

    Args:
        orcid: The ORCID of the researcher to reconcile to Wikidata.
    """
    data = get_orcid_data(orcid)

    with open("sample.json", "w+") as f:
        f.write(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False))

    researcher_qid = lookup_id(orcid, property="P496", default="LAST")
    ref = f'|S854|"https://orcid.org/{str(orcid)}"'

    qs = get_base_qs(orcid, data, researcher_qid, ref)

    employment_data = data["activities-summary"]["employments"]["employment-summary"]
    employment_institutions = get_organization_list(employment_data)
    qs = process_item(
        qs,
        property_id="P108",  # Property for employer
        original_dict="institutions",  # Handles institutions.json
        target_list=employment_institutions,
        subject_qid=researcher_qid,
        ref=ref,
    )

    education_data = data["activities-summary"]["educations"]["education-summary"]
    education_entries = get_education_info(education_data)
    qs = process_education_entries(
        qs,
        subject_qid=researcher_qid,
        ref=ref,
        education_entries=education_entries,
        property_id="P69",  # Property for educated at
    )

    external_ids = get_external_ids(data)

    external_id_properties = {"Loop profile": "P2798"}
    for key, value in external_ids.items():
        if key in external_id_properties:
            qs += f'\n{researcher_qid}|{external_id_properties[key]}|"{value}"{ref}'

    return qs


def get_base_qs(orcid, data, researcher_qid, ref):
    """Returns the first lines for the new Quickstatements"""

    personal_data = data["person"]
    first_name = personal_data["name"]["given-names"]["value"]
    last_name = personal_data["name"]["family-name"]["value"]

    if researcher_qid == "LAST":
        # Creates a new item
        qs = f"""CREATE
{researcher_qid}|Len|"{first_name} {last_name}"
{researcher_qid}|Den|"researcher"
    """
    else:
        # Updates an existing item
        qs = ""
    qs = (
        qs
        + f"""
{researcher_qid}|P31|Q5{ref}
{researcher_qid}|P106|Q1650915{ref}
{researcher_qid}|P496|"{orcid}"{ref} """
    )
    return qs


def get_orcid_data(orcid):
    """Pulls data from the ORCID API"""
    # From https://pub.orcid.org/v3.0/#!/Public_API_v2.0/viewRecord
    url = "https://pub.orcid.org/v2.0/"
    header = {"Accept": "application/json"}
    r = requests.get(f"{url}{orcid}", headers=header)
    data = r.json()
    return data


def process_item(
    qs,
    property_id,
    original_dict,
    target_list,
    subject_qid,
    ref,
    qualifier_nested_dictionary=None,
):
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

        if qualifier_nested_dictionary is not None:
            qualifier_pairs = qualifier_nested_dictionary[target_item]

            for key, value in qualifier_pairs.items():
                qs = qs + f"|{key}|{value}" + f"{ref}"
        else:
            qs = qs + f"{ref}"
    return qs


def get_qid_for_item(key, target_item):
    """
    Looks up the qid given a key using global dict of dicts.
    If it is not present, it lets the user update the dict.

    Args:
        key (str): The stem f the file path (e.g., `degree` for
        `degree.json`, `institutions` for `institutions.json`)
        target_item (str): The string to lookup in the dict

    Returns:
        qid:str
    """
    data = dicts[key]
    if target_item not in data:
        add_key(data, target_item)
        stem_to_path[key].write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False))
    qid = data[target_item]
    return qid


def lookup_id(id, property, default):
    """
    Looks up a foreign ID on Wikidata based on its specific property.
    """

    sparql = SPARQLWrapper(
        "https://query.wikidata.org/sparql",
        agent="PyORCIDator (https://github.com/lubianat/pyorcidator)",
    )
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
        if a["disambiguated-organization"] is not None:
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
    """
    Parses ORCID data and returns a list of EducationEntry objects.
    """
    organization_list = []

    for data_entry in data:

        title = data_entry["role-title"]
        if title is not None:
            role_qid = get_qid_for_item("degree", title)
        else:
            role_qid = None
        start_date = get_date(data_entry, "start")
        end_date = get_date(data_entry, "end")
        data_entry = data_entry["organization"]
        name = data_entry["name"]
        institution_qid = get_institution_qid(data_entry, name)

        entry = EducationEntry(
            degree=role_qid,
            institution=institution_qid,
            start_date=start_date,
            end_date=end_date,
        )

        organization_list.append(entry)

    return organization_list


def get_institution_qid(data_entry, name):
    """Gets the QID for an academic institution"""

    # Tries to get it from GRID: Global Research Identifier Database
    if (
        data_entry["disambiguated-organization"]
        and "disambiguation-source" in data_entry["disambiguated-organization"]
        and data_entry["disambiguated-organization"].get("disambiguation-source") == "GRID"
    ):
        grid = data_entry["disambiguated-organization"]["disambiguated-organization-identifier"]
        institution_qid = lookup_id(grid, "P2427", name)
    else:
        # Gets the QID from the controlled vocabullary dict
        institution_qid = get_qid_for_item("institutions", name)
    return institution_qid


def process_education_entries(qs, subject_qid, ref, education_entries, property_id="P69"):
    """
    From a list of EducationEntry objects, renders quickstatements for the QID.
    """
    # Quickstatements fails in the case of same institution for multliple degrees.
    # See https://www.wikidata.org/wiki/Help:QuickStatements#Limitation

    for entry in education_entries:

        qs += f"""
        {subject_qid}|{property_id}|{entry.institution}"""

        if entry.degree is not None:
            qs += f"|P512|{entry.degree}"
        if entry.start_date != "":
            qs += f"|P580|{entry.start_date}|P582|{entry.end_date}"

        qs += f"{ref}"
    return qs


def get_paper_dois(group_of_works_from_orcid):
    """ """
    dois = []
    for work in group_of_works_from_orcid:
        for external_id in work["external-ids"]["external-id"]:
            if external_id["external-id-type"] == "doi":
                dois.append(external_id["external-id-value"])
    logger.info("got paper DOIs: %s", dois)
    return dois
