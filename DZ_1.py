import requests
import json
from pprint import pprint
url = 'https://api.github.com/users/Viktor1606/repos'
res = requests.get(url)
j_data = res.json()

pprint(j_data)
with open("example.json", "w") as res:
    json.dump(j_data, res, indent=4)
