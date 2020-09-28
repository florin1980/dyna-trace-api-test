import yaml, requests, ssl, json, logging
from random import randint

CFG_ENDPOINT = '/api/config/v1/'
RULE_ITEMS = 'host-group-prefixes'
ID_MZ_LENGTH = 18


class DynatraceAPI:

    def __init__(self):
        # 1. open yaml file and get data
        self.yaml_data = {}                                                             # Dict for YAML based data
        with open(r'desc-mz.yml') as file:
            self.yaml_data.update(yaml.load(file, Loader=yaml.FullLoader))

        self.env_id = str(self.yaml_data['enviromment_id'])                             # Base URL for JSON payload
        self.tenant = str(self.yaml_data['tenant_id'])                                  # Florin Sandescu Trial Tenant ID
        self.type = str(self.yaml_data['type'])                                         # Florin Sandescu Type:MZ
        self.token = str(self.yaml_data['api_token'])                                   # Config API Token
        self.headers = {'Content-Type': 'application/json; charset=utf-8',
                        'Authorization': 'Api-Token ' + self.token}                     # headers & Dynatrace Config API Token for json payload validation
        self.dyna_mz_data = []                                                          # list of Dyna Current IDs/Names
        self.dyna_mz_ids = []                                                           # List of current reserved IDs (excepted from randomizing)
        self.logger = logging.getLogger(__name__)

        # make it self.logger.debug to the console.
        console = logging.StreamHandler()
        self.logger.addHandler(console)

    # 2. get current dynatrace list of IDs/Names
    def get_current_data_mz(self) -> None:
        try:
            # attempt to fetch all existing current Dyna dictionary (IDs/Names)
            r = requests.get(url=f'{self.env_id}{CFG_ENDPOINT}{self.type}', headers=self.headers)
            self.logger.debug('%s save list: %d' % (self.type, r.status_code))
            res = r.json()

            self.dyna_mz_data.append(res['values'])
            for entry in res['values']:
                self.dyna_mz_ids.append(entry['id'])

        except ssl.SSLError:
            self.logger.debug('SSL Error')

    # 3. Validate JSON payload prior to sending
    # ... as recommended here:
    # https://www.dynatrace.com/support/help/dynatrace-api/configuration-api/management-zones-api/put-mz/
    def validate_json_payload(self, id_mz: str, json_data: str) -> int:
        try:
            # attempt JSON request put
            r = requests.post(url=f'{self.env_id}{CFG_ENDPOINT}{self.type}/{id_mz}/validator',
                              data=json_data, headers=self.headers)
            return r.status_code

        except ssl.SSLError:
            self.logger.debug('SSL Error')

    # 4. Send PUT requests to Dyna Config API to update/create MZs
    def update_data_mz(self) -> None:
        for name_mz, doc in self.yaml_data['teams'].items():

            # get ID
            id_mz = self.get_dyna_mz_id(name_mz)
            # build JSON data / append rules according to YAML host-group-prefixes entries
            data = {'name': name_mz, 'rules': list(), }
            if RULE_ITEMS in doc:
                for host_group_prefix in doc[RULE_ITEMS]:
                    data['rules'].append({
                        'type': 'PROCESS_GROUP', 'enabled': 'true',
                        'propagationTypes': ['PROCESS_GROUP_TO_SERVICE', 'PROCESS_GROUP_TO_HOST', ],
                        'conditions': [{'key': {'attribute': 'HOST_GROUP_NAME', },
                                        'comparisonInfo': {'type': 'STRING', 'operator': 'BEGINS_WITH',
                                                           'value': host_group_prefix, 'negate': 'false',
                                                           'caseSensitive': 'true', }}, ]
                    })
            json_data = json.dumps(data)

            # UPDATE/CREATE existing/new Management Zone
            try:
                # validate JSON request put
                v = self.validate_json_payload(id_mz, json_data)
                if v == 204:
                    # if valid attempt JSON request put
                    r = requests.put(url=f'{self.env_id}{CFG_ENDPOINT}{self.type}/{id_mz}',
                                     data=json_data, headers=self.headers)
                    self.logger.debug('%s UPDATE/CREATE MZ with ID: %d' % (id_mz, r.status_code))

                    # add this ID to exception list
                    self.dyna_mz_ids.append(id_mz)
                else:
                    self.logger.debug('JSON payload Validation failed with status: ' + str(v))

            except ssl.SSLError:
                self.logger.debug('SSL Error')

    # generate new ID for json request OR get existing ID
    def get_dyna_mz_id(self, name_mz: str) -> str:
        r = ''
        # get dyna ID if dyna name matches YAML name
        s = r.join([i['id'] for i in self.dyna_mz_data[0] if i['name'] == name_mz])
        # return random ID if above not found
        s = self.new_random_id_mz() if len(s) == 0 else s
        return str(s)

    # generate random number of ID_MZ_LENGTH digits as new IDs
    # excluding entries in dynatrace exception list
    def new_random_id_mz(self) -> int:
        range_start = 10 ** (ID_MZ_LENGTH - 1)
        range_end = (10 ** ID_MZ_LENGTH) - 1
        # and generate random number
        i = randint(range_start, range_end)

        # return random number NOT IN exception list IDs
        return self.new_random_id_mz() if i in self.dyna_mz_ids else i


# Main sequence execution
def main():
    api = DynatraceAPI()
    api.get_current_data_mz()
    api.update_data_mz()


# entry point
if __name__ == '__main__':
    main()
