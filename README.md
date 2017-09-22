# OpenStreetMap Case Study

## Introduction
<p>My task is to investigate a data set from a location of my choosing from
openstreetmap. I need identify problems, clean it and store the data in SQL.
Then, I am to explore the data programmatically and propose ideas on how to
improve the data set. This investigation is a practice project needed to
complete the Data Analyst Nanodegree from Udacity.
</p>

### Getting Started
<p>This case has been documented using jupyter notebook
DAND-Wrang-openStreetMap.ipynb. All relevant information, link to the map and
python codes can be found by opening the file DAND-Wrang-openStreetMap.ipynb.
</p>
- openStreetMap_case.pdf: Contains my answers to the rubric and documents my
data wrangling process.
- audit_streetnames.py: Script that audits streetnames.
- process_map.py: Script that converts and cleans my data.
- auckland_new-zealand-sample.osm: Contains small part of the map region I used.

### Location
<p>I chose Auckland, New Zealand as my location for my investigation because I
have been planning to take a trip here for sometime now. I would like to take
the opportunity to get myself familiar with the place by using it as an example
for this project.</p>
- [www.openstreetmap.org/node/292806332](https://www.openstreetmap.org/node/292806332)

## Problems Encountered in Your Map
<p>To find and fix the streetnames in the map data, I ran the entire map data
through a function that groups all street addresses into a dictionary according
to the different variations used in the map. I filter the street names that I
expect to be used and review the street addresses that I don't expect. Below
are the problems that I will focus on for my audit.</p>

- **Mispelled Names.** Some street names are spelled incorrectly like *Strreet*.
- **Incorrect Capitalization.** Some street names are not capitalized
consistently like *road*.
- **Abbreviated Names.** Some of the street names are abbreviated. I would
prefer not to use abbreviations of their names. Instead of *Hwy*, use *Highway*.
- **Problematic Format.** Street names with problematic characters will be
ignored.

<p>I start fixing the data set by using the function *update_name*, which
revises the streetnames according to my specifications that are outlined in
*mapping*. Once I am satisfied with my data, I process the data in an xml
structure accordng to the example schema. I then turn xml into csv. Once the
CSVs are generated and validated, I then import the data into an SQL database
to begin my exploration.</p>

```py
from collections import defaultdict
import xml.etree.cElementTree as ET
import re
import pprint

file_sample = "auckland_new-zealand-sample.osm" # Sample extract for testing.
file_actual = "auckland_new-zealand.osm" # Main file.

street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE) # Searches the last word of a street address.

# Expected street names that expect and are more frequently used in the dataset.
expected = ["Avenue", "Crescent", "Drive", "Highway", "Lane", "Place", "Road", "Street", "Way"]

mapping = { # Mapping is the dict that I use for reference when I update the street names.
    "street": "Street",
    "st": "Street",
    "st.": "Street",
    "rd": "Road",
    "road": "Road",
    "strret": "Street",
    "cr": "Crescent",
    "cresent": "Crescent",
    "crest": "Crescent",
    "hwy": "Highway",
    "ave": "Avenue",
    "plc,": "Place",
    "beach": "Beach",
    "way": "Way",
    "ln": "Lane"
}

def update_name(name, mapping): # Updates street name according to mapping dict.
    name_a = name.split(" ")

    for w in range(len(name_a)):
        if name_a[w].lower() in mapping.keys():
            name_a[w] = mapping[name_a[w].lower()]
    name = " ".join(name_a)

    return name

def audit_street_type(street_types, street_name): # Audits addresses. Excludes expected and updates names.
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            new_name = update_name(street_name, mapping)
            street_types[street_type].add(new_name)

def is_street_name(elem): # Checks if element is a street addresses.
    return (elem.attrib['k'] == 'addr:street')

def audit(osmfile): # Initiates the audit, searches for sreet addresses and organizes them for review.
    osm_file = open(osmfile, 'r')
    street_types = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=('start',)):
        if elem.tag == "way" or elem.tag == 'node':
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])
    osm_file.close()
    return street_types

st_types = audit(file_actual) # Element that holds the audited data.

pprint.pprint(dict(st_types)) # Prints street names before and after the update.
```

```py
import csv
import codecs
import cerberus
import schema

NODES_PATH = "nodes.csv" # These are the csv file paths.
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

SCHEMA = schema.schema # Example schema that validates the data model.

# Column Headers to populate the data set.
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']

def shape_element(element, node_attr_fields=NODE_FIELDS, # Creates the XML structure. Updates street names.
                  way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS,
                  default_tag_type='regular'):
    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []

    if element.tag == 'node': # Nodes.
        for elem in NODE_FIELDS:
            if element.get(elem):
                node_attribs[elem] = element.attrib[elem]
            else: # Some nodes does not have attributes. This ignores them.
                return

        for elem in element:
            item = {}
            if PROBLEMCHARS.match(elem.attrib['k']): # Ignores problematic characters.
                continue
            elif LOWER_COLON.match(elem.attrib['k']): # If the element has a ':'.
                item['id'] = element.attrib['id']
                item['key'] = elem.attrib['k'].split(':')[1]
                item['type'] = elem.attrib['k'].split(':')[0]
                if is_street_name(elem):
                    item['value'] = update_name(elem.attrib['v'], mapping) # Updates street names.
                else:
                    item['value'] = elem.attrib['v']
            else: # For everythin else.
                item['id'] = element.attrib['id']
                item['key'] = elem.attrib['k']
                item['type'] = 'regular'
                if is_street_name(elem):
                    item['value'] = update_name(elem.attrib['v'], mapping)
                else:
                    item['value'] = elem.attrib['v']
            tags.append(item)

        return {'node': node_attribs, 'node_tags': tags}

    if element.tag == 'way': # Ways.
        i = 0 # counter for way_nodes elements. Since we do know how many they are.
        for elem in element.attrib:
            if elem in WAY_FIELDS:
                way_attribs[elem] = element.attrib[elem]

        for elem in element:
            item = {}
            item_nd = {}
            if elem.tag == "tag":
                if LOWER_COLON.match(elem.attrib["k"]):
                    item["id"] = element.attrib["id"]
                    item["key"] = elem.attrib["k"].split(":", 1)[1]
                    item["type"] = elem.attrib["k"].split(":", 1)[0]
                    if is_street_name(elem):
                        item['value'] = update_name(elem.attrib['v'], mapping)
                    else:
                        item["value"] = elem.attrib["v"]
                else:
                    item["id"] = element.attrib["id"]
                    item["key"] = elem.attrib["k"]
                    item["type"] = "regular"
                    if is_street_name(elem):
                        item['value'] = update_name(elem.attrib['v'], mapping)
                    else:
                        item["value"] = elem.attrib["v"]
                tags.append(item)

            if elem.tag == "nd":
                item_nd["id"] = int(element.attrib["id"])
                item_nd["node_id"] = int(elem.attrib["ref"])
                item_nd["position"] = i
                i += 1
                way_nodes.append(item_nd)

        return {"way": way_attribs, "way_nodes": way_nodes, "way_tags": tags}

# Helper Functions.
def get_element(osm_file, tags=('node', 'way', 'relation')): # Efficient parser.
    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()

def validate_element(element, validator, schema=SCHEMA): # Validates our data structure.
    """Raise ValidationError if element does not match schema"""
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_string = pprint.pformat(errors)

        raise Exception(message_string.format(field, error_string))

class UnicodeDictWriter(csv.DictWriter, object): # Helps write the csv.
    def writerow(self,row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v, in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)            

def process_map(file_in, validate): # Main function that processes the map data.
    # Opens each csv file.
    with codecs.open(NODES_PATH, "w") as nodes_file, \
    codecs.open(NODE_TAGS_PATH, "w") as node_tags_file, \
    codecs.open(WAYS_PATH, "w") as ways_file, \
    codecs.open(WAY_NODES_PATH, "w") as way_nodes_file, \
    codecs.open(WAY_TAGS_PATH, "w") as way_tags_file:
        # CSV writing variables and methods.
        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(node_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')): # CSV writing process.
            el = shape_element(element)
            if el:
                if validate is True:
                    validate_element(el, validator)
                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == "way":
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el["way_nodes"])
                    way_tags_writer.writerows(el["way_tags"])

process_map(file_actual, validate=True) # Initiates writing the CSVs.
```
## Overview of the Data
### File Size
- auckland_new-zealand.osm: 658 MB
- project.db: 409 MB
- node_tags.csv: 3.67 MB
- ways.csv: 20 MB
- ways_nodes.csv: 84 MB
- ways_tags.csv: 86 MB
- nodes.csv: 246 MB

### Counts
- Number of Unique Users: 953
- Number of Nodes: 2,913,110
- Number of Ways: 328,159
- Number of Hotels: 61
- Number of Attractions: 55
- Number of Museums: 13

## Other Ideas about the Dataset
### More descriptive Attractions Markers for Tourists
<p>It would be a lot more helpful if tourists attractions are given more detail
on their labels. Currently, the tags are labeled as **attractions** are not as
helpful as much for traveler to plan their trip. If the attractions have more
detail such as **beach**, **monuments** or **nature**, then these would be more
helpful for would-be travelers planning a visit to Auckland.</p>

<p>Currently, there are 18 types of tourism markers. One of the tourism sites
are labeled as *attractions* with 55 markers on Auckland, New Zealand. If these
markers are provided with more detail, it could be helpful information to
travelers.</p>

<p>I suggest that if when users edit, there should be a snippet of text within
text field, where the users would input the data, that would encourage the user
to add more detail to their markers or labels. Instead of an empty field, it
could instead say, "What can I see here?".</p>

## Conclusions
<p>Auckland, New Zealand map is well populated by contributions from active
users. But because of the lack of guidelines or motivation to properly fill
in the data is affecting the extent of details that each of the users is
willing to input. If at the moment of data entry, there would be a descriptive
text in a form of a question, users would be more obliged or encourage to
place more detail on the data.</p>

## References
<p>I have reviewed and patterned my analysis from carlward's sample_project.md
that was recommended by the Udacity Project Description of this Submission.
[Link](https://gist.github.com/carlward/54ec1c91b62a5f911c42#file-sample_project-md)
</p>
