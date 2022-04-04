import clipboard
from dictionaries.all import *


def add_key(dictionary, string):
    clipboard.copy(string)
    qid = input(f"What is the qid for: {string} ?")
    dictionary[string] = qid
    return


def process_item(qs, property_id, key, target_list):
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
LAST|{property_id}|{qid}
    """
        )
    return qs
