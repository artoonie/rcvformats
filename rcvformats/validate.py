import json
import jsonschema

class Validator:
    def __init__(self):
        pass

    def validate(self, filename, schema):
        with open(filename, 'r') as f:
            data = json.load(f)
            jsonschema.validate(data, schema)
