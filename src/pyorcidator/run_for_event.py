import os
import click
from urllib.parse import quote
from SPARQLWrapper import SPARQLWrapper, JSON
from pyorcidator.import_info import render_orcid_qs


def get_orcids_for_event(event_qid):
    endpoint_url = "https://query.wikidata.org/sparql"

    query = f"""
    SELECT DISTINCT ?orcid WHERE {{
      wd:{event_qid} wdt:P823 ?speaker.
      ?speaker wdt:P496 ?orcid.
    }}
    """

    sparql = SPARQLWrapper(endpoint_url)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    orcids = [result["orcid"]["value"] for result in results["results"]["bindings"]]
    return orcids


@click.command(name="parse_event")
@click.option(
    "--event_qid",
    prompt="Event QID",
    help="The QID of the event you are interested in",
)
def import_orcids_from_event(event_qid: str):
    processed_orcids_file = "processed_orcids.txt"
    if os.path.exists(processed_orcids_file):
        with open(processed_orcids_file) as f:
            processed_orcids = f.read().splitlines()
    else:
        processed_orcids = []

    orcids = get_orcids_for_event(event_qid)
    orcids_to_process = [orcid for orcid in orcids if orcid not in processed_orcids]

    for orcid in orcids_to_process:
        print(f"===== Running for {orcid} ======")
        qs = render_orcid_qs(orcid)
        quoted_qs = quote(qs.replace("\t", "|").replace("\n", "||"), safe="")
        url = f"https://quickstatements.toolforge.org/#/v1={quoted_qs}\\"
        print(qs)
        print(url)
        mock = input("Enter anything to continue.")

        # Record processed ORCIDs
        processed_orcids.append(orcid)
        with open(processed_orcids_file, "a") as f:
            f.write(f"{orcid}\n")


if __name__ == "__main__":
    import_orcids_from_event()
