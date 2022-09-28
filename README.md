# PyORCIDator

PyORCIDator is a wrapper for ORCID data for integration to Wikidata.

It currently only tries and import for each ORCID:

- Employment data (*without* titles and start and end date)
- Educational data (with titles and start and end date)

It generates a quickstatement with a standard English description of "researcher" and a [occupation](https://www.wikidata.org/wiki/Property:P106) --> [researcher](https://www.wikidata.org/wiki/Q1650915) statement.

## Next steps

The current features are on the development list:

- Adding authorship (P50) statements for all listed articles. 
- Extract Google Scholar and Twitter IDs 

## Installation
To install PyORCIDator, run the easiest way is to clone the repository with:

```bash
git clone https://github.com/lubianat/pyorcidator.git
```

Then, install it from the project's root directory with:

```bash
pip install -e .
```

## Usage
To run PyORCIDator, interactively, run:
```bash
pyorcidator import
```

To run a simple query, just run:
```bash
pyorcidator import --orcid 0000-0003-2473-2313
```

To run a query with a list of ORCIDs, run:
```bash
# here orcids.txt is a file containing one ORCID per line
pyorcidator import_list --orcid-list orcids.txt
```

# Related Work
* https://pure.mpg.de/rest/items/item_3367602_1/component/file_3367603/content 
