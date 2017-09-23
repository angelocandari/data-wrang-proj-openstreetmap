from collections import defaultdict
import xml.etree.cElementTree as ET
import re
import pprint

file_sample = "auckland_new-zealand-sample.osm" # Sample extract for testing.
file_actual = "auckland_new-zealand.osm" # Main file.

# Searches the last word of a street address.
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)

# Expected street names that expect and are more frequently used in the dataset.
expected = ["Avenue", "Crescent", "Drive", "Highway",
    "Lane", "Place", "Road", "Street", "Way"]

mapping = { # This is what I use for reference when I update the street names.
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

def audit_street_type(street_types, street_name): # Audits addresses.
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            new_name = update_name(street_name, mapping)
            street_types[street_type].add(new_name)

def is_street_name(elem): # Checks if element is a street addresses.
    return (elem.attrib['k'] == 'addr:street')

def audit(osmfile): # Initiates the audit.
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
