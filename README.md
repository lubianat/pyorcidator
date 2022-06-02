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

## Usage

```
pip install -e .

pyorcidator import --orcid 0000-0003-2473-2313
```

(in construction)
