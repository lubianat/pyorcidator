import clipboard
from dictionaries.all import *
from SPARQLWrapper import SPARQLWrapper, JSON


def add_key(dictionary, string):
    clipboard.copy(string)
    qid = input(f"What is the qid for: {string} ?")
    dictionary[string] = qid
    return


def process_item(qs, property_id, key, target_list, subject_qid):
    global dicts
    for target_item in target_list:
        if target_item not in dicts[key]:
            add_key(dicts[key], target_item)
            with open(f"src/dictionaries/{key}.json", "w+") as f:
                f.write(json.dumps(dicts[key], indent=4, sort_keys=True))

        qid = dicts[key][target_item]
        qs = (
            qs
            + f"""
{subject_qid}|{property_id}|{qid}
    """
        )
    return qs


def lookup_orcid(orcid):
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
    query = f"""
    SELECT ?item ?itemLabel
    WHERE
    {{
        ?item wdt:P496 "{orcid}" .
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
        return "LAST"
