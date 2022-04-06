import clipboard
from dictionaries.all import *
from SPARQLWrapper import SPARQLWrapper, JSON
from wikidata_lookup import search_wikidata
import re


def add_key(dictionary, string):
    clipboard.copy(string)

    predicted_id = search_wikidata(string)

    annotated = False

    while annotated == False:

        answer = input(
            f"Is the QID for '{string}' {predicted_id['id']}"
            f" ({predicted_id['url']}) ? (y/n) "
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


def get_qid_for_item(original_dict, target_item):
    if target_item not in dicts[original_dict]:
        add_key(dicts[original_dict], target_item)
        with open(f"src/dictionaries/{original_dict}.json", "w+") as f:
            f.write(json.dumps(dicts[original_dict], indent=4, sort_keys=True))

    qid = dicts[original_dict][target_item]
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


def get_education_info(data):
    organization_list = []
    qualifier_nested_dict = {}

    for a in data:
        qualifiers = {}

        title = a["role-title"]
        title_qid = get_qid_for_item("degree", title)
        qualifiers["P512"] = title_qid

        a = a["organization"]
        name = a["name"]
        if a["disambiguated-organization"]["disambiguation-source"] == "GRID":
            grid = a["disambiguated-organization"][
                "disambiguated-organization-identifier"
            ]
            id = lookup_id(grid, "P2427", name)
            name = id
        organization_list.append(name)

        qualifier_nested_dict[name] = qualifiers
        print(qualifier_nested_dict)
    return organization_list, qualifier_nested_dict
