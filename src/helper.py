import clipboard
from dictionaries.all import *
from SPARQLWrapper import SPARQLWrapper, JSON
import re


def add_key(dictionary, string):
    clipboard.copy(string)
    qid = input(f"What is the qid for: {string} ?")
    dictionary[string] = qid
    return


def process_item(
    qs,
    property_id,
    key,
    target_list,
    subject_qid,
    ref,
    qualifier_pairs={},
):
    global dicts
    for target_item in target_list:
        if re.findall("Q[0-9]*", target_item):
            qid = target_item
        else:
            if target_item not in dicts[key]:
                add_key(dicts[key], target_item)
                with open(f"src/dictionaries/{key}.json", "w+") as f:
                    f.write(json.dumps(dicts[key], indent=4, sort_keys=True))

            qid = dicts[key][target_item]
        qs = (
            qs
            + f"""
{subject_qid}|{property_id}|{qid}{ref}"""
        )

        if qualifier_pairs != {}:
            for key, value in qualifier_pairs.items():
                qs = qs + f"|{key}{value}"

    return qs


def lookup_id(id, property, default):
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
    query = f"""
    SELECT ?item ?itemLabel
    WHERE
    {{
        ?item wdt:{property} "{id}" .
    }}
    """
    print(query)
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
