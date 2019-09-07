from django.test import TestCase
import json
import os
# from AzureSite.settings import BASE_DIR
import glob



def read_json_attributes():
    adf_path = str(os.path.join(BASE_DIR+ '\ADFParameters.json')).replace('\\', '/')
    vault_path = str(os.path.join(BASE_DIR+ '\KeyVaultParameters.json')).replace('\\', '/')

    with open(adf_path) as file:
        ADFParameters = json.load(file)

    with open(vault_path) as file:
        KeyVaultParameters = json.load(file)

    return list(ADFParameters['parameters'].keys()), list(KeyVaultParameters['parameters'].keys())

# path = str(os.path.join(BASE_DIR+ '\AzureSite\sections.json')).replace('\\', '/')
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
print(BASE_DIR)
var = "{}/SupplyChain/databricks_linux/main.sh {} {}".format(BASE_DIR, "e", "yuabjk")
print('var' , var) 