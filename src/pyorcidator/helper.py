"""
Helper functions for pyorcidator
"""

import json
import logging
import re
from typing import List, Optional

import requests

from wdcuration import add_key
from .classes import AffiliationEntry
from .dictionaries import dicts, stem_to_path
from .wikidata_lookup import query_wikidata
from .quickstatements import TextQualifier, DateQualifier, Annotated, EntityQualifier,CreateLine, BaseLine, TextLine, EntityLine, Line, Qualifier

logger = logging.getLogger(__name__)
EXTERNAL_ID_PROPERTIES = {
    "Loop profile": "P2798",
    "Scopus Author ID": "P1153",
    "ResearcherID": "P1053",
}


def get_external_ids(data):
    id_list = data["person"]["external-identifiers"]["external-identifier"]
    id_dict = {}
    for id in id_list:
        id_dict[id["external-id-type"]] = id["external-id-value"]
    return id_dict


def render_orcid_qs(orcid: str) -> str:
    """
    Import info from ORCID for Wikidata.

    Args:
        orcid: The ORCID of the researcher to reconcile to Wikidata.
    """
    return "\n".join(
        line.get_text()
        for line in get_orcid_quickstatements(orcid)
    )


def get_orcid_quickstatements(orcid: str) -> List[Line]:
    """Get a list of quickstatement line objects."""
    data = get_orcid_data(orcid)

    researcher_qid = lookup_id(orcid, property="P496", default="LAST")

    qualifiers = [
        TextQualifier(predicate="S854", target=f'https://orcid.org/{orcid}'),
    ]

    lines: List[Line] = get_base_qs(orcid, data, researcher_qid, ref=qualifiers)

    employment_data = data["activities-summary"]["employments"]["employment-summary"]
    employment_entries = get_affiliation_info(employment_data)
    lines.extend(process_affiliation_entries(
        subject_qid=researcher_qid,
        ref=qualifiers,
        affiliation_entries=employment_entries,
        role_property_id="P2868",  # subject has role
        property_id="P108",  # Property for employer
    ))

    education_data = data["activities-summary"]["educations"]["education-summary"]
    education_entries = get_affiliation_info(education_data)
    lines.extend(process_affiliation_entries(
        subject_qid=researcher_qid,
        ref=qualifiers,
        affiliation_entries=education_entries,
        role_property_id="P512",  # academic degree
        property_id="P69",  # Property for educated at
    ))

    external_ids = get_external_ids(data)
    for key, value in external_ids.items():
        if key in EXTERNAL_ID_PROPERTIES:
            lines.append(TextLine(
                subject=researcher_qid,
                predicate=EXTERNAL_ID_PROPERTIES[key],
                target=value,
                qualifiers=qualifiers,
            ))

    return lines


def get_base_qs(orcid, data, researcher_qid, ref: List[Qualifier]) -> List[Line]:
    """Returns the first lines for the new Quickstatements"""
    rv = []

    personal_data = data["person"]
    first_name = personal_data["name"]["given-names"]["value"]
    last_name = personal_data["name"]["family-name"]["value"]

    if researcher_qid == "LAST":
        rv.append(CreateLine())
        rv.append(TextLine(subject=researcher_qid, predicate="Len", object=f"{first_name} {last_name}"))
        rv.append(TextLine(subject=researcher_qid, predicate="Den", object="researcher"))
    else:
        rv.append(EntityLine(subject=researcher_qid, predicate="P31", object="Q5", qualifiers=ref))
        rv.append(EntityLine(subject=researcher_qid, predicate="P106", object="Q1650915", qualifiers=ref))
        rv.append(TextLine(subject=researcher_qid, predicate="P496", object=orcid, qualifiers=ref))
    return rv


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
    # FIXME this is unused, delete?
    for target_item in target_list:
        if re.findall("Q[0-9]*", target_item):
            qid = target_item
        else:
            qid = get_qid_for_item(original_dict, target_item)
        if qid:
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


def get_qid_for_item(key: str, name: str) -> Optional[str]:
    """
    Looks up the qid given a key using global dict of dicts.
    If it is not present, it lets the user update the dict.

    Args:
        key (str): The stem f the file path (e.g., `role` for
        `role.json`, `institutions` for `institutions.json`)
        name: The string to lookup in the dict

    Returns:
        qid:str
    """
    data = dicts[key]
    if name in data:
        return data[name]
    add_key(data, name)
    qid = data.get(name)
    if qid:
        stem_to_path[key].write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False))
    return qid


def lookup_id(id, property, default):
    """
    Looks up a foreign ID on Wikidata based on its specific property.
    """
    query = f"""\
        SELECT ?item ?itemLabel
        WHERE
        {{
            ?item wdt:{property} "{id}" .
        }}
    """
    bindings = query_wikidata(query)
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


def get_affiliation_info(data) -> List[AffiliationEntry]:
    """
    Parses ORCID data and returns a list of AffiliationEntry objects.
    """
    organization_list = []

    for data_entry in data:
        title = data_entry["role-title"]
        if title is not None:
            role_qid = get_qid_for_item("role", title)
        else:
            role_qid = None
        start_date = get_date(data_entry, "start")
        end_date = get_date(data_entry, "end")
        data_entry = data_entry["organization"]
        name = data_entry["name"]
        institution_qid = get_institution_qid(data_entry, name)

        entry = AffiliationEntry(
            role=role_qid,
            institution=institution_qid,
            start_date=start_date,
            end_date=end_date,
        )

        organization_list.append(entry)

    return organization_list


def get_institution_qid(data_entry, name) -> Optional[str]:
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


def process_affiliation_entries(
    subject_qid, ref, affiliation_entries, property_id, role_property_id
):
    """
    From a list of EducationEntry objects, renders quickstatements for the QID.
    """
    # Quickstatements fails in the case of same institution for multliple roles.
    # See https://www.wikidata.org/wiki/Help:QuickStatements#Limitation
    rv = []
    for entry in affiliation_entries:
        qualifiers = ref.copy()
        if entry.role is not None:
            qualifiers.append(EntityQualifier(predicate=role_property_id, target=entry.role))
        if entry.start_date:
            qualifiers.append(DateQualifier(predicate="P580", target=entry.start_date))
            if entry.end_date:
                qualifiers.append(DateQualifier(predicate="P580", target=entry.end_date))
        line = EntityLine(subject=subject_qid, predicate=property_id, target=entry.institution, qualifiers=qualifiers)
        rv.append(line)
    return rv


def get_paper_dois(group_of_works_from_orcid):
    """ """
    dois = []
    for work in group_of_works_from_orcid:
        for external_id in work["external-ids"]["external-id"]:
            if external_id["external-id-type"] == "doi":
                dois.append(external_id["external-id-value"])
    logger.info("got paper DOIs: %s", dois)
    return dois
