import time
from .deployer_file import Deployer
from django.shortcuts import render
from rest_framework.views import APIView
from django.http.response import JsonResponse
import os
from AzureSite.settings import BASE_DIR
import json
import random
import string
import glob
from django.views.generic import TemplateView
from azure.storage.blob import BlockBlobService
from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.storage.models import StorageAccountCreateParameters
# from .databricks_linux import databricks

# read Data for form config File
def read_mapping():
    """

    :return: data containing sections and sectionAttributes to be shown on frontend
    """
    try:
        path = str(os.path.join(BASE_DIR, 'AzureSite\sections.json')).replace('\\', '/')
        with open(path) as file:
            data = json.load(file)
        return data
    except Exception as e:
        print("Error in reading the file mappings: ", e)

# Funtion for generating random unique id
def random_id(request):
    """

    :param request:
    :return: Returns a random string of 16 characters
    """
    uniqueID = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(16))
    return JsonResponse({'id': uniqueID})


# To initialize Azure resource and storage account
def azure_account(data):
    """

    :param data: request data
    :return: resource_id and client_id
    """
    sections_data = data['sections']
    client_id = ''
    secret = ''
    tenant = ''
    subscription_id = ''
    for section in range(len(sections_data)):
        try:
            # Fetch details about subscription of azure account from user data
            if sections_data[section]['title']=='Subscription Details':
                subscription_id = sections_data[section]['sectionAttributes'][0]['value']
                tenant = sections_data[section]['sectionAttributes'][1]['value']
                client_id = sections_data[section]['sectionAttributes'][2]['value']
                secret = sections_data[section]['sectionAttributes'][3]['value']
                resource_group = sections_data[section]['sectionAttributes'][4]['value']
            elif sections_data[section]['title'] =='Storage Account Details':
                storage_account_name = sections_data[section]['sectionAttributes'][0]['value']
        except Exception as e:
            print('Error in for loop of azure_account function: ', e)
    try:
        # Initialization of Azure resources
        credentials = ServicePrincipalCredentials(
            client_id=client_id,
            secret=secret,
            tenant=tenant
        )
        print("credentials: ", credentials)
        resource_client = ResourceManagementClient(credentials, subscription_id)
        storage_client = StorageManagementClient(credentials, subscription_id)
    except Exception as e:
        print('Error in azure_account function', e)
        return e
    return resource_client, storage_client, storage_account_name, resource_group


# To validate the user credentials and other attributes
class azure_functions(APIView):

    def get(self, request):
        return JsonResponse({"success": "No Data to Display"})

    def post(self, request):
        # If credentials are invalid then only exception message will be returned from azure_account function
        try:
            resource_client, storage_client, storage_account_name, resource_group = azure_account(request.data)
        except Exception as e:
            return JsonResponse({'status': 'failed', "message": "Invalid Credentials"})
        try:
            # TODO: Change the logic, send key in post call or improve conditions
            # Checking availability for storage account name
            if request.data["columnName"] == "StorageAccountName":
                availability = storage_client.storage_accounts.check_name_availability(storage_account_name)
                reason = availability.reason
                if reason is not None and reason == "AlreadyExists":
                    return JsonResponse({"status": "success", "message": ""})
                else:
                    return JsonResponse({"status": "failed", "message": "Storage Account doesn't exist"})
            # Checking availability for resource group
            if request.data['columnName'] == "ResourceGroupName":
                resource_availability = resource_client.resource_groups.check_existence(resource_group)
                if resource_availability:
                    return JsonResponse({"status": "success", "message": ""})
                else:
                    return JsonResponse({"status": "failed", "message": "Resource Group Doesn't exist"})
        except Exception as e:
            print('In azure_function exception', e)
            return JsonResponse({'status': 'failed', "message": "Invalid Credentials"})


class index(TemplateView):
    template_name = "index.html"

    def get(self, request):
        try:
            form_data = read_mapping()
        except Exception as e:
            return render(request, self.template_name, context={'message': 'failed'})
        return render(request, self.template_name, context={'message': 'Successful'})


class SupplyChain(APIView):

    def get(self, request):
        """

        :param request: request data
        :return: JsonResponse containing form sections detail
        """
        try:
            data = read_mapping()
        except Exception as e:
            return JsonResponse({'Output': 'Error in reading json file ' + str(e)})
        return JsonResponse({'message': 'Successful', 'formConfig': data})

    def post(self, request):
        """

        :param request: Request Data
        :return:
        """
        path = str(os.path.join(BASE_DIR +'\AzureSite\parameters.json')).replace('\\', '/')
        try:
            # Fetch paramenters from paparameters.json to create file in desired output
            with open(path) as parameters_file:
                try:
                    param_file = json.load(parameters_file)
                    adf_parameters = param_file['ADFParameters']['values']
                    vault_parameters = param_file['KeyVaultParameters']['values']
                    adf_dict = { '$schema': param_file['general']['schema'],
                                'contentVersion': param_file['general']['contentVersion'], 'parameters': {}}
                    vault_dict = { '$schema': param_file['general']['schema'],
                                'contentVersion': param_file['general']['contentVersion'], 'parameters': {}}
                except Exception as e:
                    print("Exception in opening parameters.json file: ", e)
            # Container Name to be used in Azure Deployment
            container_name = param_file['containername']
            # Convert Parameter list to lowercase
            adf_parameters = list(map(lambda func: func.lower(), adf_parameters))
            vault_parameters = list(map(lambda func: func.lower(), vault_parameters))
        except Exception as e:
            print('Error opening json file: ', e)
        try:
            section_data = request.data['sections']
        except Exception as e:
            return JsonResponse({"message": "error in request data" + str(e)})

        for section_attr in range(len(section_data)):
            # Creation of ADFparamenters and KVparameters from user data
            try:
                sectionAttributes = section_data[section_attr]['sectionAttributes']
                for sectionAttribute in range(len(sectionAttributes)):
                    try:
                        name = sectionAttributes[sectionAttribute]['internalName']
                        value = sectionAttributes[sectionAttribute]['value']
                        if name.lower() in adf_parameters:
                            adf_dict['parameters'][name] = {'value': value}
                        if name.lower() in vault_parameters:
                            vault_dict['parameters'][name] = {'value': value}
                    except Exception as e:
                        print('error in inner loop', sectionAttribute, str(e))
            except Exception as e:
                print('error in in outer loop at index ', section_attr)
                return JsonResponse({'Output': 'error'})

        # For optional Table
        select_variables = ["SAP", "SalesForce", "Oracle", "BQ"]
        try:
            selected_value = adf_dict['parameters']['Sources']['value']
            # Create the table schema and corresponding data
            if selected_value in select_variables:
                temp_param = (selected_value) + 'Tables'
                subsections = section_data[3]['subsections']['sections'][selected_value]['subsectionAttributes']
                schemas = []
                tables = []
                for subsection in range(len(subsections)):
                    if subsections[subsection]['internalName'] == selected_value+'Schema':
                        schemas = subsections[subsection]['value'].split(',')
                    elif subsections[subsection]['internalName'] == selected_value+'Tables':
                        tables = subsections[subsection]['value'].split(',')
                    else:
                        adf_dict['parameters'][subsections[subsection]['internalName']] = {'value': subsections[subsection]['value']}
                adf_dict['parameters'][temp_param] = {"value": []}
                for schema in range(len(schemas)):
                    adf_dict['parameters'][temp_param]["value"].append({
                        "table_schema": schemas[schema],
                        "table_name": tables[schema]})
            else:
                # when Blob Option is choosen
                adf_dict['parameters']["BlobTable"] = {"value": []}
                tables = section_data[3]['subsections']['sections'][selected_value]['subsectionAttributes'][0]['value'].split(',')
                for table in range(len(tables)):
                    adf_dict['parameters']["BlobTable"]['value'].append({'table_name': tables[table]})
        except KeyError as e:
            print("Keyerror Exception in creating table data: ", e)
            return JsonResponse({"message": "error"})
        except Exception as e:
            print('Exception in creating table data: ', e)
            return JsonResponse({"message": "error"})

        # Get all required parameters from submitted data for Azure Deployment
        try:
            connectionstring = vault_dict['parameters']['StorageConnectionString']['value']
            account_name = vault_dict['parameters']['StorageAccountName']['value']
            access_key = vault_dict['parameters']['StorageAccessKey']['value']
            for key in range(len(section_data)):
                try:
                    if section_data[key]['title']=='Subscription Details':
                        subscription_id = section_data[key]['sectionAttributes'][0]['value']
                        tenant = section_data[key]['sectionAttributes'][1]['value']
                        client_id = section_data[key]['sectionAttributes'][2]['value']
                        secret = section_data[key]['sectionAttributes'][3]['value']
                        resource_group = section_data[key]['sectionAttributes'][4]['value']
                        resource_group_location = section_data[key]['sectionAttributes'][5]['value']
                    elif section_data[key]['title'] =='Storage Account Details':
                        storage_account_name = section_data[key]['sectionAttributes'][0]['value']
                except Exception as e:
                    print("Exception in initializing various keys: ", e)
                    client_id = ''
                    secret = ''
                    tenant = ''
                    subscription_id = ''
                    resource_group = ''
                    resource_group_location = ''
        except KeyError as key:
            print('Key Not found', key)

        # Azure Deployment code
        try:
            with open('upload_files/ADFParameters.json', 'w') as adf:
                json.dump(adf_dict, adf)
            with open('upload_files/KeyVaultParameters.json', 'w') as kv:
                json.dump(vault_dict, kv)
            # resource_client, storage_client = azure_account(request.data)
            # Create a storage blob container to store the files
            # Create the BlockBlockService that is used to call the Blob service for the storage account.
            block_blob_service = BlockBlobService(
                account_name=account_name,
                account_key=access_key)
            # Create a container called 'quickstartblobs'.
            # container_name = 'marketplacecodes'
            # TODO: Review and improve
            create_container = False
            counter = 0
            while create_container != True and counter < 5:
                try:
                    create_container = block_blob_service.create_container(container_name)
                    counter = counter + 1
                    time.sleep(10)
                except Exception as e:
                    print("Error in creating a new container: ", e)
            # Set the permission so the blobs are public.
            # block_blob_service.set_container_acl(
            #     container_name, public_access=PublicAccess.Container)
            # retrive conn string from storage variable "storageconnstring" for azure push

            blob_name_adf = "ADFParameters.json"
            blob_name_kv = "KeyVaultParameters.json"
            blob_client = BlockBlobService(connection_string=connectionstring)
            # Creation of blobs for all the parameters and deployment file in container
            for filepath in glob.iglob('upload_files/*.json'):
                try:
                    file_name = filepath.split("\\")
                    response_obj = blob_client.create_blob_from_path(container_name=container_name, blob_name=file_name[1],
                                                             file_path=os.path.join(BASE_DIR, filepath))
                    print("blob_create status: ", response_obj)
                    time.sleep(5)
                except Exception as e:
                    print("Exception in creating Blob: ", e)

            # Deployment of blobs
            try:
                deployment_obj = Deployer(resource_group, subscription_id, client_id, secret,
                                          tenant, container_name, resource_group_location)
                adf_obj = deployment_obj.deploy("upload_files/DataFactoryDeployment.json",
                                                "upload_files/ADFParameters.json", connectionstring)
                kv_obj = deployment_obj.deploy("upload_files/KeyVaultDeployment.json",
                                               "upload_files/KeyVaultParameters.json", connectionstring)
            except Exception as e:
                print("Exception in deploy the data factory: ", e)

            # Remove conatiner from storage account after deployment
            try:
                databricksToken = vault_dict['parameters']['DataBricksToken']
                databricksScope = vault_dict['parameters']['DataBricksScope']
                databricksURL = vault_dict['parameters']['DataBricksWorkspaceURL']
                # databricks.main(databricksURL, databricksToken, databricksScope)
            except Exception as e:
                print('exception in databricks function: ', e)
            try:
                time.sleep(720)
                delete_container = blob_client.delete_container(container_name)
                print("delete container: ", delete_container)
            except Exception as e:
                print("Exception in removing conatiner from storage account: ", e)
            # Remove ADFParameters.json and KeyVaultParameters.json after deployment
            try:
                os.remove('upload_files/ADFParameters.json')
                os.remove('upload_files/KeyVaultParameters.json')
                print('files removed')
            except Exception as e:
                print('Error in removing ADFParameters.json and KeyVaultParameters.json file:', str(e))
        except Exception as e:
            print("exception in azure conn: " + str(e))
        print('done')

        return JsonResponse({"message": "Successful"})
