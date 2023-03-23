"""
Helper functions for pyorcidator
"""

import datetime
import json
import logging
import re
from typing import Dict, List, Mapping, Optional, Tuple, Union
import pydantic
import requests
from wdcuration import add_key

from .classes import AffiliationEntry
from .dictionaries import dicts, stem_to_path
from .quickstatements import (
    CreateLine,
    DateQualifier,
    EntityLine,
    EntityQualifier,
    Line,
    Qualifier,
    TextLine,
    TextQualifier,
)
from .wikidata_lookup import query_wikidata

logger = logging.getLogger(__name__)
EXTERNAL_ID_PROPERTIES = {
    "Loop profile": "P2798",
    "Scopus Author ID": "P1153",
    "ResearcherID": "P1053",
    "GND": "P227",
    "github": "P2037",
    "twitter": "P2002",
    "scopus": "P1153",
}
HTTP_REGEX = "(https?:\/\/)?"
PREFIXES = [
    ("github", "github.com/"),
    ("twitter", "twitter.com/"),
    ("scopus", "www.scopus.com/authid/detail.uri?authorId=")
    # TODO linkedin, figshare, researchgate, publons, semion, semantic scholar, google scholar, etc.
]


def get_external_ids(data) -> Mapping[str, str]:
    """Get external identifiers that can be mapped to Wikidata properties."""
    rv = {}
    for d in data["person"]["external-identifiers"]["external-identifier"]:
        rv[d["external-id-type"]] = d["external-id-value"]
    for d in data["person"]["researcher-urls"].get("researcher-url", []):
        # url_name = d["url-name"].lower().replace(" ", "")
        url = d["url"]["value"].rstrip("/")
        for key, url_prefix in PREFIXES:
            prefix_w_regex = f"{HTTP_REGEX}{url_prefix}"
            if re.match(prefix_w_regex, url):
                rv[key] = re.sub(prefix_w_regex, "", url)
    return rv


def render_orcid_qs(orcid: str) -> str:
    """
    Import info from ORCID for Wikidata.

    Args:
        orcid: The ORCID of the researcher to reconcile to Wikidata.
    """
    return "\n".join(line.get_line() for line in get_orcid_quickstatements(orcid))


def _get_orcid_qualifier(orcid: str) -> Qualifier:
    return TextQualifier(predicate="S854", target=f"https://orcid.org/{orcid}")


def get_orcid_quickstatements(orcid: str) -> List[Line]:
    """Get a list of quickstatement line objects."""
    data = get_orcid_data(orcid)

    researcher_qid = lookup_id(orcid, property="P496", default="LAST")

    lines: List[Line] = get_base_qs(orcid, data, researcher_qid)

    keyword_data = data["person"]["keywords"]["keyword"]
    if len(keyword_data) > 0:
        lines.extend(
            process_keyword_entries(
                orcid=orcid,
                researcher_qid=researcher_qid,
                keyword_data=keyword_data,
                property_id="P101",
            )
        )

    employment_data = data["activities-summary"]["employments"]["employment-summary"]
    employment_entries = get_affiliation_info(employment_data)
    lines.extend(
        process_affiliation_entries(
            orcid=orcid,
            subject_qid=researcher_qid,
            affiliation_entries=employment_entries,
            role_property_id="P2868",  # subject has role
            property_id="P108",  # Property for employer
        )
    )

    education_data = data["activities-summary"]["educations"]["education-summary"]
    education_entries = get_affiliation_info(education_data)
    lines.extend(
        process_affiliation_entries(
            orcid=orcid,
            subject_qid=researcher_qid,
            affiliation_entries=education_entries,
            role_property_id="P512",  # academic degree
            property_id="P69",  # Property for educated at
        )
    )

    papers_data = data["activities-summary"]["works"]["group"]
    papers_entries = get_paper_dois(papers_data)
    if len(papers_entries) > 0:
        lines.extend(
            process_paper_entries(
                orcid=orcid,
                researcher_qid=researcher_qid,
                paper_dois=papers_entries,
                property_id="P50",
            )
        )

    external_ids = get_external_ids(data)
    for key, value in external_ids.items():
        predicate = EXTERNAL_ID_PROPERTIES.get(key)
        if predicate is None:
            continue
        lines.append(
            TextLine(
                subject=researcher_qid,
                predicate=predicate,
                target=value,
                qualifiers=[_get_orcid_qualifier(orcid)],
            )
        )

    return lines


def get_base_qs(orcid, data, researcher_qid) -> List[Line]:
    """Returns the first lines for the new Quickstatements"""
    quickstatements = []
    if researcher_qid == "LAST":
        quickstatements.append(CreateLine())
        first_name = data["person"]["name"]["given-names"]["value"]
        last_name = data["person"]["name"]["family-name"]["value"]
        quickstatements.append(
            TextLine(subject=researcher_qid, predicate="Len", target=f"{first_name} {last_name}")
        )
        quickstatements.append(
            TextLine(subject=researcher_qid, predicate="Den", target="researcher")
        )
    qualifiers = [_get_orcid_qualifier(orcid)]
    quickstatements.append(
        EntityLine(subject=researcher_qid, predicate="P31", target="Q5", qualifiers=qualifiers)
    )
    quickstatements.append(
        EntityLine(
            subject=researcher_qid, predicate="P106", target="Q1650915", qualifiers=qualifiers
        )
    )
    quickstatements.append(
        TextLine(subject=researcher_qid, predicate="P496", target=orcid, qualifiers=qualifiers)
    )
    return quickstatements


def get_orcid_data(orcid):
    """Pulls data from the ORCID API"""
    # From https://pub.orcid.org/v3.0/#!/Public_API_v2.0/viewRecord
    url = "https://pub.orcid.org/v2.0/"
    header = {"Accept": "application/json"}
    r = requests.get(f"{url}{orcid}", headers=header)
    data = r.json()
    return data


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


def get_date(
    entry, start_or_end="start"
) -> Union[Tuple[datetime.datetime, int], Tuple[None, None]]:
    date = entry.get(f"{start_or_end}-date")
    if date is None:
        return None, None
    year = int(date.get("year", {}).get("value", 0))
    if not year:
        return None, None
    month = int(date["month"]["value"]) if date["month"] else 1
    day = date["day"] and int(date["day"]["value"])

    if day:
        # precision of 11 means day is known
        try:
            return datetime.datetime(year=year, month=month, day=day), 11
        except:
            return datetime.datetime(year=year, month=month, day=1), 10

    elif month:
        # precision of 10 means up to the month is known
        return datetime.datetime(year=year, month=month, day=1), 10
    else:
        # precision of 9 means up to the year is known
        return datetime.datetime(year=year, month=1, day=1), 9


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
        start_date, start_date_precision = get_date(data_entry, "start")
        end_date, end_date_precision = get_date(data_entry, "end")
        data_entry = data_entry["organization"]
        name = data_entry["name"]
        institution_qid = get_institution_qid(data_entry, name)

        entry = AffiliationEntry(
            role=role_qid,
            institution=institution_qid,
            start_date=start_date,
            start_date_precision=start_date_precision,
            end_date=end_date,
            end_date_precision=end_date_precision,
        )

        organization_list.append(entry)

    return organization_list


def process_keyword_entries(
    orcid: str, researcher_qid: str, keyword_data: List, property_id: str
) -> List[EntityLine]:
    fields = [keyword["content"] for keyword in keyword_data]
    field_of_work_list = []
    for field in fields:
        print(field)
        if ";" in field:
            fields.extend(field.split(";"))
            continue
        qualifiers = [_get_orcid_qualifier(orcid)]

        field_qid = get_qid_for_item("fields", field)

        entry = EntityLine(
            subject=researcher_qid, predicate=property_id, target=field_qid, qualifiers=qualifiers
        )

        field_of_work_list.append(entry)

    return field_of_work_list


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
    *,
    orcid: str,
    subject_qid: str,
    affiliation_entries: List[AffiliationEntry],
    property_id: str,
    role_property_id: str,
) -> List[Line]:
    """
    From a list of EducationEntry objects, renders quickstatements for the QID.
    """
    # Quickstatements fails in the case of same institution for multliple roles.
    # See https://www.wikidata.org/wiki/Help:QuickStatements#Limitation
    rv = []
    for entry in affiliation_entries:
        qualifiers = [_get_orcid_qualifier(orcid)]
        if entry.role and entry.role.lower() != "none":
            if re.match(r"^[PQS]\d+$", entry.role):
                qualifiers.append(EntityQualifier(predicate=role_property_id, target=entry.role))
            else:
                logger.warning("ungrounded role: %s", entry.role)
        if entry.start_date:
            qualifiers.append(
                DateQualifier.start_time(entry.start_date, precision=entry.start_date_precision)
            )
            if entry.end_date:
                qualifiers.append(
                    DateQualifier.end_time(entry.end_date, precision=entry.end_date_precision)
                )
        line = EntityLine(
            subject=subject_qid,
            predicate=property_id,
            target=entry.institution,
            qualifiers=qualifiers,
        )
        rv.append(line)
    return rv


def get_paper_dois(group_of_works_from_orcid: List[Dict]) -> List[str]:
    """Return list of DOIs (strings) from an ORCID API result"""
    dois = []
    for work in group_of_works_from_orcid:
        for external_id in work["external-ids"]["external-id"]:
            if external_id["external-id-type"] == "doi":
                dois.append(external_id["external-id-value"])
    logger.info("got paper DOIs: %s", dois)
    return dois


def get_paper_qids(papers_dois: List[str]) -> List[str]:
    """Get QIDs for list of DOIs"""

    filtered_list_of_dois = [a for a in papers_dois if a[0:3] == "10."]
    print(filtered_list_of_dois)
    doi_values = " ".join(f"'{doi.upper()}'" for doi in filtered_list_of_dois)

    query = f"""\
        SELECT ?item
        WHERE
        {{
            VALUES ?doi {{{doi_values}}}
            ?itemURL wdt:P356 ?doi .
            BIND(REPLACE(STR(?itemURL), "http://www.wikidata.org/entity/", "") AS ?item)
        }}
    """

    bindings = query_wikidata(query)
    if len(bindings) > 0:
        return [binding["item"]["value"] for binding in bindings]


def process_paper_entries(
    orcid: str, researcher_qid: str, paper_dois: List[str], property_id: str
) -> List[EntityLine]:
    """From a list of paper DOIs create statements for linking them to author"""

    paper_qids = get_paper_qids(paper_dois)

    paper_statements = []

    qualifiers = [_get_orcid_qualifier(orcid)]
    try:
        for paper in paper_qids:
            entry = EntityLine(
                subject=paper, predicate=property_id, target=researcher_qid, qualifiers=qualifiers
            )

            paper_statements.append(entry)
    except pydantic.error_wrappers.ValidationError:
        # TODO
        pass
    return paper_statements
