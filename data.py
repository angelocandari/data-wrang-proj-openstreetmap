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
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset',
    'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']

# Creates the XML structure. Updates street names.
def shape_element(element, node_attr_fields=NODE_FIELDS,
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
            if PROBLEMCHARS.match(elem.attrib['k']): # Ignores problematic char.
                continue
            elif LOWER_COLON.match(elem.attrib['k']): # If  element has a ':'.
                item['id'] = element.attrib['id']
                item['key'] = elem.attrib['k'].split(':')[1]
                item['type'] = elem.attrib['k'].split(':')[0]
                if is_street_name(elem): # Updates street names.
                    item['value'] = update_name(elem.attrib['v'], mapping)
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
        i = 0 # counter for way_nodes elements.
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
 # Validates our data structure.
def validate_element(element, validator, schema=SCHEMA):
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
        # CSV writing process.
        for element in get_element(file_in, tags=('node', 'way')):
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
