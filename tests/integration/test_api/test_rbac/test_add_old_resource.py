'''
copyright:
    Copyright (C) 2015-2021, Wazuh Inc.

    Created by Wazuh, Inc. <info@wazuh.com>.

    This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

type:
    integration

description:
    These tests will check if the `rbac` (Role-Based Access Control) feature
    of the API is working properly. Specifically, they will verify that when
    resources are added with the same identifier of previously existing ones,
    the previous relationships are not maintained. The `rbac` capability
    allows users accessing the API to be assigned a role that will
    define the privileges they have.

tiers:
    - 0

component:
    manager

path:
    tests/integration/test_api/test_rbac/

daemons:
    - apid
    - analysisd
    - syscheckd
    - wazuh-db

os_support:
    - linux, centos 6
    - linux, centos 7
    - linux, centos 8
    - linux, rhel6
    - linux, rhel7
    - linux, rhel8
    - linux, amazon linux 1
    - linux, amazon linux 2
    - linux, debian buster
    - linux, debian stretch
    - linux, debian wheezy
    - linux, ubuntu bionic
    - linux, ubuntu xenial
    - linux, ubuntu trusty
    - linux, arch linux

coverage:

pytest_args:

tags:
    - api
'''
import requests
from wazuh_testing.api import get_security_resource_information

# Variables
user_id, role_id, policy_id, rule_id = None, None, None, None


# Tests
def test_add_old_user(set_security_resources, get_api_details):
    '''
    description:
        Remove a user with defined relationships and create it
        with the same ID to see if said relationships remain.

    wazuh_min_version:
        4.1

    parameters:
        - set_security_resources:
            type: fixture
            brief: Creates a set of role-based security resources along with a user for testing.

        - get_api_details:
            type: fixture
            brief: Get API information.

    assertions:
        - Verify that testing user information exists.
        - Verify that `status code` 200 (ok) is received when the testing user is removed.
        - Verify that `status code` 200 (ok) is received when the testing user is added.
        - Verify that security relationships do not exist between the old and the new user.

    test_input:
        From the `set_security_resources` fixture information is obtained to perform the test,
        concretely the `user_id`.

    logging:
        - api.log:
            - Requests made to the API should be logged.

    tags:
        - rbac
    '''
    api_details = get_api_details()
    old_user_info = get_security_resource_information(user_ids=user_id)
    assert old_user_info, f'There is not information about this role: {user_id}'

    delete_endpoint = api_details['base_url'] + f'/security/users?user_ids={user_id}'
    response = requests.delete(delete_endpoint, headers=api_details['auth_headers'], verify=False)
    assert response.status_code == 200, f'Status code was not 200. Response: {response.text}'

    add_endpoint = api_details['base_url'] + f'/security/users'
    response = requests.post(add_endpoint, json={'username': old_user_info['username'],
                                                 'password': 'Password1!'}, headers=api_details['auth_headers'],
                             verify=False)
    assert response.status_code == 200, f'Status code was not 200. Response: {response.text}'
    relationships = response.json()['data']['affected_items'][0]
    for key, value in relationships.items():
        if key not in ['id', 'username', 'password', 'allow_run_as']:
            assert not value, f'Relationships are not empty: {key}->{value}'


def test_add_old_role(set_security_resources, get_api_details):
    '''
    description:
        Remove a role with defined relationships and create it
        with the same ID to see if said relationships remain.

    wazuh_min_version:
        4.1

    parameters:
        - set_security_resources:
            type: fixture
            brief: Creates a set of role-based security resources along with a user for testing.

        - get_api_details:
            type: fixture
            brief: Get API information.

    assertions:
        - Verify that testing role information exists.
        - Verify that `status code` 200 (ok) is received when the testing role is removed.
        - Verify that `status code` 200 (ok) is received when the testing role is added.
        - Verify that security relationships do not exist between the old and the new role.

    test_input:
        From the `set_security_resources` fixture information is obtained to perform the test,
        concretely the `role_id`.

    logging:
        - api.log:
            - Requests made to the API should be logged.

    tags:
        - rbac
    '''
    api_details = get_api_details()
    old_role_info = get_security_resource_information(role_ids=role_id)
    assert old_role_info, f'There is not information about this role: {role_id}'

    delete_endpoint = api_details['base_url'] + f'/security/roles?role_ids={role_id}'
    response = requests.delete(delete_endpoint, headers=api_details['auth_headers'], verify=False)
    assert response.status_code == 200, f'Status code was not 200. Response: {response.text}'

    add_endpoint = api_details['base_url'] + f'/security/roles'
    response = requests.post(add_endpoint, json={'name': old_role_info['name']}, headers=api_details['auth_headers'],
                             verify=False)
    assert response.status_code == 200, f'Status code was not 200. Response: {response.text}'
    relationships = response.json()['data']['affected_items'][0]
    for key, value in relationships.items():
        if key not in ['id', 'name']:
            assert not value, f'Relationships are not empty: {key}->{value}'


def test_add_old_policy(set_security_resources, get_api_details):
    '''
    description:
        Remove a policy with defined relationships and create it
        with the same ID to see if said relationships remain.

    wazuh_min_version:
        4.1

    parameters:
        - set_security_resources:
            type: fixture
            brief: Creates a set of role-based security resources along with a user for testing.

        - get_api_details:
            type: fixture
            brief: Get API information.

    assertions:
        - Verify that testing policy information exists.
        - Verify that `status code` 200 (ok) is received when the testing policy is removed.
        - Verify that `status code` 200 (ok) is received when the testing policy is added.
        - Verify that security relationships do not exist between the old and the new policy.

    test_input:
        From the `set_security_resources` fixture information is obtained to perform the test,
        concretely the `policy_id`.

    logging:
        - api.log:
            - Requests made to the API should be logged.

    tags:
        - rbac
    '''
    api_details = get_api_details()
    old_policy_info = get_security_resource_information(policy_ids=policy_id)
    assert old_policy_info, f'There is not information about this policy: {policy_id}'

    delete_endpoint = api_details['base_url'] + f'/security/policies?policy_ids={policy_id}'
    response = requests.delete(delete_endpoint, headers=api_details['auth_headers'], verify=False)
    assert response.status_code == 200, f'Status code was not 200. Response: {response.text}'

    add_endpoint = api_details['base_url'] + f'/security/policies'
    response = requests.post(add_endpoint,
                             json={'name': old_policy_info['name'],
                                   'policy': old_policy_info['policy']},
                             headers=api_details['auth_headers'],
                             verify=False)
    assert response.status_code == 200, f'Status code was not 200. Response: {response.text}'
    relationships = response.json()['data']['affected_items'][0]
    for key, value in relationships.items():
        if key not in ['id', 'name', 'policy']:
            assert not value, f'Relationships are not empty: {key}->{value}'


def test_add_old_rule(set_security_resources, get_api_details):
    '''
    description:
        Remove a rule with defined relationships and create it
        with the same ID to see if said relationships remain.

    wazuh_min_version:
        4.1

    parameters:
        - set_security_resources:
            type: fixture
            brief: Creates a set of role-based security resources along with a user for testing.

        - get_api_details:
            type: fixture
            brief: Get API information.

    assertions:
        - Verify that testing rule information exists.
        - Verify that `status code` 200 (ok) is received when the testing rule is removed.
        - Verify that `status code` 200 (ok) is received when the testing rule is added.
        - Verify that security relationships do not exist between the old and the new rule.

    test_input:
        From the `set_security_resources` fixture information is obtained to perform the test,
        concretely the `rule_id`.

    logging:
        - api.log:
            - Requests made to the API should be logged.

    tags:
        - rbac
    '''
    api_details = get_api_details()
    old_rule_info = get_security_resource_information(rule_ids=rule_id)
    assert old_rule_info, f'There is not information about this policy: {rule_id}'

    delete_endpoint = api_details['base_url'] + f'/security/rules?rule_ids={rule_id}'
    response = requests.delete(delete_endpoint, headers=api_details['auth_headers'], verify=False)
    assert response.status_code == 200, f'Status code was not 200. Response: {response.text}'

    add_endpoint = api_details['base_url'] + f'/security/rules'
    response = requests.post(add_endpoint,
                             json={'name': old_rule_info['name'],
                                   'rule': old_rule_info['rule']},
                             headers=api_details['auth_headers'],
                             verify=False)
    assert response.status_code == 200, f'Status code was not 200. Response: {response.text}'
    relationships = response.json()['data']['affected_items'][0]
    for key, value in relationships.items():
        if key not in ['id', 'name', 'rule']:
            assert not value, f'Relationships are not empty: {key}->{value}'
