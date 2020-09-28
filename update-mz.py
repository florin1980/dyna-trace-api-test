import yaml, requests, ssl, json
from random import randint

yaml_data = dict()                                              # GLOBAL dict to receive YAML data
rule_items = 'host-group-prefixes'                              # CONST YAML level entry for each new Dynatrace rule
id_mz_length = 18                                               # CONST Management Zone ID length
dyna_mz_data = []                                               # GLOBAL list to store existing Dynatrace IDs/Names
dyna_mz_ids = []                                                # GLOBAL list to store Used MZ IDs (These are excepted while generating new (random) IDs


# 1. open yaml file and get data
def open_yaml():
    global ENV, TENANT, TYPE, TOKEN, HEADERS
    with open(r'desc-mz.yml') as file:
        yaml_data.update(yaml.load(file, Loader=yaml.FullLoader))

    ENV = str(yaml_data['enviromment_id'])                      # Base URL for JSON payload
    TENANT = str(yaml_data['tenant_id'])                        # Florin Sandescu Trial Tenant ID
    TYPE = str(yaml_data['type'])                               # Florin Sandescu Trial Tenant ID
    TOKEN = str(yaml_data['api_token'])                         # Config API Token
    HEADERS = {'Content-Type': 'application/json; charset=utf-8',
               'Authorization': 'Api-Token ' + TOKEN}               # HEADERS & Dynatrace Config API Token for json payload validation


# 2. get current dynatrace list of IDs/Names
def get_current_data_mz():

    try:
        # attempt to fetch all existing current Dyna dictionary (IDs/Names)
        r = requests.get(ENV + '/api/config/v1/' + TYPE, headers=HEADERS)
        print('%s save list: %d' % (TYPE, r.status_code))
        res = r.json()

        dyna_mz_data.append(res['values'])
        for entry in res['values']:
            dyna_mz_ids.append(entry['id'])

    except ssl.SSLError:
        print('SSL Error')


# 3. Validate JSON payload prior to sending
# ... as recommended here:
# https://www.dynatrace.com/support/help/dynatrace-api/configuration-api/management-zones-api/put-mz/
def validate_json_payload(id_mz, json_data):
    try:
        # attempt JSON request put
        r = requests.post(
            ENV + '/api/config/v1/' + TYPE + '/' + str(id_mz) + '/validator',
            data=json_data, headers=HEADERS)
        return r.status_code

    except ssl.SSLError:
        print('SSL Error')


# 4. Send PUT requests to Dyna Config API to update/create MZs
def update_data_mz():
    for name_mz, doc in yaml_data['teams'].items():

        # get ID
        id_mz = get_dyna_mz_id(name_mz)

        # build JSON data / append rules according to YAML host-group-prefixes entries
        data = {'name': name_mz, 'rules': list(), }
        if rule_items in doc:
            for host_group_prefix in doc[rule_items]:
                data['rules'].append({
                    'type': 'PROCESS_GROUP', 'enabled': 'true',
                    'propagationTypes': ['PROCESS_GROUP_TO_SERVICE', 'PROCESS_GROUP_TO_HOST', ],
                    'conditions': [{'key': {'attribute': 'HOST_GROUP_NAME', }, 'comparisonInfo': {'type': 'STRING', 'operator': 'BEGINS_WITH', 'value': host_group_prefix, 'negate': 'false', 'caseSensitive': 'true', }}, ]
                })
        json_data = json.dumps(data)

        # UPDATE/CREATE existing/new Management Zone
        try:
            # validate JSON request put
            v = validate_json_payload(id_mz, json_data)
            if v == 204:
                # if valid attempt JSON request put
                r = requests.put(
                    ENV + '/api/config/v1/' + TYPE + '/' + str(id_mz),
                    data=json_data, headers=HEADERS)
                print('%s UPDATE/CREATE MZ with ID: %d' % (id_mz, r.status_code))

                # add this ID to exception list
                dyna_mz_ids.append(id_mz)
            else:
                print('JSON payload Validation failed with status: ' + str(v))

        except ssl.SSLError:
            print('SSL Error')


# generate new ID for json request OR get existing ID
def get_dyna_mz_id(name_mz):
    r = ''

    # get dyna ID if dyna name matches YAML name
    s = r.join([i['id'] for i in dyna_mz_data[0] if i['name'] == name_mz])
    # return random ID if above not found
    s = new_random_id_mz() if len(s) == 0 else s
    return s


# generate random number of n digits as new IDs
# excluding entries in dynatrace exception list
def new_random_id_mz():
    # set random number ranges as defined as CONST
    # and generate random number
    range_start = 10 ** (id_mz_length - 1)
    range_end = (10 ** id_mz_length) - 1
    i = randint(range_start, range_end)

    # return random number NOT IN exception list IDs
    return new_random_id_mz() if i in dyna_mz_ids else i


# Main sequence execution
def main():
    open_yaml()
    get_current_data_mz()
    update_data_mz()


# entry point
if __name__ == '__main__':
    main()
