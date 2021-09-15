'''
copyright: Copyright (C) 2015-2021, Wazuh Inc.

           Created by Wazuh, Inc. <info@wazuh.com>.

           This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

type: integration

brief: These tests will verify if the `wazuh-analysisd` daemon generates valid alerts from
       Linux `syscheck` events. The `wazuh-analysisd` daemon receives the log messages
       and compares them to the rules. It then creates an alert when a log message
       matches an applicable rule.

tier: 2

modules:
    - analysisd

components:
    - manager

daemons:
    - wazuh-analysisd
    - wazuh-db

os_platform:
    - linux

os_version:
    - Arch Linux
    - Amazon Linux 2
    - Amazon Linux 1
    - CentOS 8
    - CentOS 7
    - CentOS 6
    - Ubuntu Focal
    - Ubuntu Bionic
    - Ubuntu Xenial
    - Ubuntu Trusty
    - Debian Buster
    - Debian Stretch
    - Debian Jessie
    - Debian Wheezy
    - Red Hat 8
    - Red Hat 7
    - Red Hat 6

references:
    - https://documentation.wazuh.com/current/user-manual/reference/daemons/wazuh-analysisd.html

tags:
    - events
'''
import os

import pytest
import yaml
from wazuh_testing.analysis import validate_analysis_alert_complex
from wazuh_testing.tools import WAZUH_PATH, LOG_FILE_PATH, ALERT_FILE_PATH
from wazuh_testing.tools.monitoring import ManInTheMiddle

# Marks

pytestmark = [pytest.mark.linux, pytest.mark.tier(level=2), pytest.mark.server]

# Configurations

test_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
messages_path = os.path.join(test_data_path, 'syscheck_events.yaml')
with open(messages_path) as f:
    test_cases = yaml.safe_load(f)

# Variables

log_monitor_paths = [LOG_FILE_PATH, ALERT_FILE_PATH]
analysis_path = os.path.join(os.path.join(WAZUH_PATH, 'queue', 'sockets', 'queue'))

receiver_sockets_params = [(analysis_path, 'AF_UNIX', 'UDP')]

mitm_analysisd = ManInTheMiddle(address=analysis_path, family='AF_UNIX', connection_protocol='UDP')
# monitored_sockets_params is a List of daemons to start with optional ManInTheMiddle to monitor
# List items -> (wazuh_daemon: str,(
#                mitm: ManInTheMiddle
#                daemon_first: bool))
# Example1 -> ('wazuh-clusterd', None)              Only start wazuh-clusterd with no MITM
# Example2 -> ('wazuh-clusterd', (my_mitm, True))   Start MITM and then wazuh-clusterd
monitored_sockets_params = [('wazuh-db', None, None), ('wazuh-analysisd', mitm_analysisd, True)]

receiver_sockets, monitored_sockets, log_monitors = None, None, None  # Set in the fixtures

events_dict = {}
alerts_list = []
analysisd_injections_per_second = 200


# Fixtures


@pytest.fixture(scope='module', params=range(len(test_cases)))
def get_alert(request):
    return alerts_list[request.param]


# Tests


def test_validate_all_linux_alerts(configure_sockets_environment, connect_to_sockets_module, wait_for_analysisd_startup,
                                   generate_events_and_alerts, get_alert):
    '''
    description: Check if the alerts generated by the `wazuh-analysisd` daemon from
                 Linux `syscheck` events are valid. The `validate_analysis_alert_complex`
                 function checks if an `analysisd` alert is properly formatted in
                 reference to its `syscheck` event.

    wazuh_min_version: 4.2

    parameters:
        - configure_sockets_environment:
            type: fixture
            brief: Configure environment for sockets and MITM.
        - connect_to_sockets_module:
            type: fixture
            brief: Module scope version of `connect_to_sockets` fixture.
        - wait_for_analysisd_startup:
            type: fixture
            brief: Wait until the `wazuh-analysisd` has begun and the `alerts.json` file is created.
        - generate_events_and_alerts:
            type: fixture
            brief: Read the specified `YAML` and generate every event and alert using the input from every test case.
        - get_alert:
            type: fixture
            brief: List of alerts to be validated.

    assertions:
        - Verify that the alerts generated are consistent with the events received.

    input_description: Different test cases that are contained in an external `YAML` file (syscheck_events.yaml)
                       that includes `syscheck` events data and the expected output.

    expected_output:
        - Multiple messages (alert logs) corresponding to each test case,
          located in the external input data file.

    tags:
        - alerts
        - man_in_the_middle
        - wdb_socket
    '''
    alert = get_alert
    path = alert['syscheck']['path']
    mode = alert['syscheck']['event'].title()
    validate_analysis_alert_complex(alert, events_dict[path][mode])
