import clipboard
from dictionaries.all import *
from SPARQLWrapper import SPARQLWrapper, JSON
import re
from dataclasses import dataclass



@dataclass
class EducationEntry:
    """Class for capturing the info for an education entry on ORCID."""
    institution: str
    degree: str
    start_date: str = None
    end_date: str = None

def add_key(dictionary, string):
    clipboard.copy(string)
    qid = input(f"What is the qid for: {string} ?")
    dictionary[string] = qid
    return


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
        qs = qs + f"""
        {subject_qid}|{property_id}|{qid}"""
       
        if qualifier_nested_dictionary != {}:
            qualifier_pairs = qualifier_nested_dictionary[target_item]

            for key, value in qualifier_pairs.items():
                qs = qs + f"|{key}|{value}" + f"{ref}"
        else:
            qs = qs + f"{ref}"
    return qs


def get_qid_for_item(original_dict_name, target_item):
    if target_item not in dicts[original_dict_name]:
        add_key(dicts[original_dict_name], target_item)
        with open(f"src/dictionaries/{original_dict_name}.json", "w+") as f:
            f.write(json.dumps(dicts[original_dict_name], indent=4, sort_keys=True))

    qid = dicts[original_dict_name][target_item]
    return qid


def lookup_id(id, property, default):
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
        if a["disambiguated-organization"]["disambiguation-source"] == "GRID":
            grid = a["disambiguated-organization"][
                "disambiguated-organization-identifier"
            ]
            id = lookup_id(grid, "P2427", name)
            name = id
        organization_list.append(name)
    return organization_list



def get_date(entry, start_or_end ="start"):
    date =  entry[f"{start_or_end}-date"]
    year = date["year"]["value"]
    month = date["month"]["value"]
    day = date["day"]["value"]

    return f"+{year}-{month}-{day}T00:00:00/11"


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
        if a["disambiguated-organization"]["disambiguation-source"] == "GRID":
            grid = a["disambiguated-organization"][
                "disambiguated-organization-identifier"
            ]

            institution_qid = lookup_id(grid, "P2427", name)
        else:
            institution_qid = get_qid_for_item("institutions", name)

        
        entry = EducationEntry(degree=degree_qid, institution =institution_qid, start_date=start_date, end_date=end_date )

        organization_list.append(entry)

    return organization_list


def process_education_entries(
    qs,
    subject_qid,
    ref,
    education_entries,
        property_id="P69"
):

    # Quickstatements fails in the case of same institution for multliple degrees. 
    # See https://www.wikidata.org/wiki/Help:QuickStatements#Limitation
    for entry in education_entries:      
        qs = qs + f"""
        {subject_qid}|{property_id}|{entry.institution}|P512|{entry.degree}|P580|"{entry.start_date}"|P582|"{entry.end_date}"{ref}"""
    return qs
