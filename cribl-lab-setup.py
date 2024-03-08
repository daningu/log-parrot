import json
import requests
import re


def get_secrets():
    # Parsing secrets.json to get API Creds
    with open("secrets.json", encoding="utf-8") as secrets_file:
        file_secrets = json.load(secrets_file)
    return file_secrets


def cribl_authenticate():
    # Authenticating with API Creds to get Auth Token
    payload = json.dumps(
        {
            "grant_type": "client_credentials",
            "client_id": CRIBL_API_ID,
            "client_secret": CRIBL_API_SECRET,
            "audience": "https://api.cribl.cloud",
        }
    )
    headers = {"content-type": "application/json"}

    response = requests.post(
        "https://login.cribl.cloud/oauth/token",
        headers=headers,
        data=payload,
        timeout=35,
    )

    return json.loads(response.text)["access_token"]


# def cribl_create_input():


def cribl_create_ls_output(output_name, ingest_token):
    # Creating a LogScale output from template
    url = CRIBL_URL + "/api/v1/m/default/system/outputs"

    payload = json.dumps(
        {
            "id": output_name,
            "systemFields": ["cribl_pipe"],
            "streamtags": [],
            "loadBalanced": False,
            "concurrency": 5,
            "maxPayloadSizeKB": 4096,
            "maxPayloadEvents": 0,
            "compress": True,
            "rejectUnauthorized": True,
            "timeoutSec": 30,
            "flushPeriodSec": 1,
            "failedRequestLoggingMode": "none",
            "safeHeaders": [],
            "format": "JSON",
            "authType": "manual",
            "responseRetrySettings": [],
            "timeoutRetrySettings": {"timeoutRetry": False},
            "responseHonorRetryAfterHeader": False,
            "onBackpressure": "block",
            "url": "https://cloud.us.humio.com/api/v1/ingest/hec",
            "useRoundRobinDns": False,
            "type": "humio_hec",
            "token": ingest_token,
        }
    )
    headers = {
        "accept": "application/json",
        "Authorization": "Bearer " + cribl_auth_token,
        "Content-Type": "application/json",
    }

    response = requests.post(url, headers=headers, data=payload, timeout=5)

    print(response.text)
    return 0


# def cribl_create_output_router():


def cribl_update_output_router(rule_list):

    url = CRIBL_URL + "/api/v1/m/default/system/outputs/lab-parrot"
    body = (
        '{"id": "lab-parrot","systemFields": ["cribl_pipe"],"streamtags": [],"type": "router","rules": ['
        + rule_list
        + "]}"
    )
    headers = {
        "Authorization": "Bearer " + cribl_auth_token,
        "Content-Type": "application/json",
    }

    response = requests.request("PATCH", url, headers=headers,
                                data=body, timeout=5)

    print(response.status_code)
    return 0


def create_output_router_rules(ls_ingest_token_list):
    rules_list = ""
    for entry in range(len(ls_ingest_token_list)):
        rule = json.dumps(
            {"filter": "true", "final": False,
             "output": "participant" + str(entry)}
        )
        if entry == 0:
            rules_list = rule
        else:
            rules_list = rules_list + ", " + rule
    return rules_list


def cribl_commit_deploy():
    # Commits and deploys changes
    commit_url = CRIBL_URL + "/api/v1/version/commit"
    deploy_url = CRIBL_URL + "/api/v1/m/default/master/groups/default/deploy"

    commit_payload = json.dumps(
        {"effective": True, "group": "default", "message": "api sent commit"}
    )
    headers = {
        "Authorization": "Bearer " + cribl_auth_token,
        "Content-Type": "application/json",
    }

    commit_response = requests.request(
        "POST", commit_url, headers=headers, data=commit_payload, timeout=5
    )
    response_items = json.loads(commit_response.text)["items"][0]
    version_number = response_items["commit"]
    print(version_number)
    print(commit_response.status_code)
    commit_summary = [
        response_items["summary"]["changes"],
        response_items["summary"]["insertions"],
        response_items["summary"]["deletions"],
    ]
    if commit_summary == [0, 0, 0]:
        print("No changes were committed, therefore nothing was deployed")
        return 0

    if commit_response.status_code == 200:
        deploy_payload = json.dumps({"version": version_number})

        requests.request(
            "PATCH", deploy_url, headers=headers, data=deploy_payload, timeout=5
        )

        print("Changes have been deployed and committed. Cheers!")
        return 0
    else:
        print("Something went wrong, commit was not deployed")
        return 1


def cribl_get_output_lists():
    url = CRIBL_URL + "/api/v1/m/default/system/outputs"

    headers = {
        "Authorization": "Bearer " + cribl_auth_token,
        "Content-Type": "application/json",
    }
    response = requests.get(url, headers=headers, timeout=5)

    output_list = json.loads(response.text)['items']
    number_of_outputs = len(output_list)
    guid_list = []
    for i in range(number_of_outputs):
        if re.match(r"^[{]?[0-9a-fA-F]{8}-([0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}[}]?$", output_list[i]['id']):
            guid_list.append(output_list[i]['id'])
            # print(json_test[i]['id'])
    return guid_list


def cribl_delete_participant_outputs(id_list):
    for output_id in id_list:
        url = CRIBL_URL + "/api/v1/m/default/system/outputs/" + output_id
        headers = {
            'accept': 'application/json',
            'Authorization': 'Bearer ' + cribl_auth_token
            }

        response = requests.request("DELETE", url, headers=headers, timeout=5)
        print(response.text)



# Getting Secrets from secrets.json file
secrets = get_secrets()
CRIBL_API_ID = secrets.get("CRIBL_API_ID")
CRIBL_API_SECRET = secrets.get("CRIBL_API_SECRET")
CRIBL_URL = secrets.get("CRIBL_URL")

# Sanity Check
# print(f"API_ID: {CRIBL_API_ID}")
# print(f"API_SECRET: {CRIBL_API_SECRET}")
# print(f"URL: {CRIBL_URL}")

ingest_token_list = [
    "985ab82d-8063-4091-848b-9abe8dc8e0b9",
    "05e30a35-19ef-482f-ab69-b51c4f775c83",
    "f79794a5-2b4d-4d32-aa43-ee0388cfc8bc",
    "41f40f3a-babe-4afd-aec1-b3aedf4b66c8",
    "a2d343b9-9390-4de0-8f93-e3de719aad03",
    "61790533-9c71-4865-af1f-d2c7b976a7e1",
    "1e10c647-1c5e-45d7-9f7d-df233f31c3e6",
    "1985fbc1-1591-4e4f-8a81-59d8814a0721",
    "0f67ea51-7681-4db7-b6e6-c5a50d339df5",
    "e63d805e-5941-48e7-9222-00f033f5d9c2",
    "28686fe6-a683-43ee-abbd-c740a0e76db9",
    "6639528f-f57b-408c-aec5-640e99edef9d"
    ]

# ALWAYS AUTHENTICATE!
cribl_auth_token = cribl_authenticate()


# CREATING OUTPUTS FOR PARTICIPANTS
#for ingest_token in ingest_token_list:
#    cribl_create_ls_output(ingest_token, ingest_token)

# ADDING ALL PARTICIPANT OUTPUTS TO OTUPUT ROUTER
#output_router_rule_list = create_output_router_rules(ingest_token_list)
#cribl_update_output_router(output_router_rule_list)


# DELETING ALL PARTICIPANTS' OUTPUTS
list_to_delete = cribl_get_output_lists()
cribl_delete_participant_outputs(list_to_delete)

# COMMIT AND DEPLOY
cribl_commit_deploy()
