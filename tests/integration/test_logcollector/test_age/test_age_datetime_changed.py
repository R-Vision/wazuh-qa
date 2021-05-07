# Copyright (C) 2015-2021, Wazuh Inc.
# Created by Wazuh, Inc. <info@wazuh.com>.
# This program is free software; you can redistribute it and/or modify it under the terms of GPLv2
import os
import sys
import time
from datetime import datetime

import pytest
import wazuh_testing.logcollector as logcollector
from wazuh_testing.tools import LOG_FILE_PATH
from wazuh_testing.tools.configuration import load_wazuh_configurations
from wazuh_testing.tools.file import truncate_file
from wazuh_testing.tools.monitoring import FileMonitor, LOG_COLLECTOR_DETECTOR_PREFIX, AGENT_DETECTOR_PREFIX
from wazuh_testing.tools.services import control_service
from wazuh_testing.tools.time import TimeMachine, time_to_timedelta, time_to_seconds
import tempfile


# Marks
pytestmark = pytest.mark.tier(level=0)

# Configuration
test_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
configurations_path = os.path.join(test_data_path, 'wazuh_age.yaml')

DAEMON_NAME = "wazuh-logcollector"

now_date = datetime.now()
folder_path = os.path.join(tempfile.gettempdir(), 'wazuh_testing_age')


if sys.platform == 'win32':
    prefix = AGENT_DETECTOR_PREFIX
else:
    prefix = LOG_COLLECTOR_DETECTOR_PREFIX

file_structure = [
    {
        "folder_path": f"{folder_path}",
        "filename": "testing_age_dating.log",
    }
]

parameters = [
    {'LOCATION': f'{folder_path}*', 'LOG_FORMAT': 'syslog', 'AGE': '4000s'},
    {'LOCATION': f'{folder_path}*', 'LOG_FORMAT': 'syslog', 'AGE': '5m'},
    {'LOCATION': f'{folder_path}*', 'LOG_FORMAT': 'syslog', 'AGE': '500m'},
    {'LOCATION': f'{folder_path}*', 'LOG_FORMAT': 'syslog', 'AGE': '9h'},
    {'LOCATION': f'{folder_path}*', 'LOG_FORMAT': 'syslog', 'AGE': '200d'},
]
metadata = [
    {'location': f'{folder_path}*', 'log_format': 'syslog', 'age': '4000s'},
    {'location': f'{folder_path}*', 'log_format': 'syslog', 'age': '5m'},
    {'location': f'{folder_path}*', 'log_format': 'syslog', 'age': '500m'},
    {'location': f'{folder_path}*', 'log_format': 'syslog', 'age': '9h'},
    {'location': f'{folder_path}*', 'log_format': 'syslog', 'age': '200d'},
]

new_host_datetime = ['60s', '-60s', '30m', '-30m', '2h', '-2h', '43d', '-43d']

configurations = load_wazuh_configurations(configurations_path, __name__,
                                           params=parameters,
                                           metadata=metadata)
configuration_ids = [f"{x['LOCATION'], x['LOG_FORMAT'], x['AGE']}" for x in parameters]


@pytest.fixture(scope="module", params=configurations, ids=configuration_ids)
def get_configuration(request):
    """Get configurations from the module."""
    return request.param


@pytest.fixture(scope="function")
def get_files_list():
    """Get file list to create from the module."""
    return file_structure


@pytest.mark.parametrize('new_datetime', new_host_datetime)
def test_configuration_age_datetime(new_datetime, get_files_list, get_configuration,
                                    create_file_structure, configure_environment):
    """Check if logcollector age option works correctly when date time of the system changes.

    Ensure that when date of the system change logcollector use properly age value, ignoring files that have not been
    modified for a time greater than age value using current date.

    Raises:
        TimeoutError: If the expected callbacks are not generated.
    """
    cfg = get_configuration['metadata']
    age_seconds = time_to_seconds(cfg['age'])

    control_service('stop', daemon=DAEMON_NAME)
    truncate_file(LOG_FILE_PATH)
    wazuh_log_monitor = FileMonitor(LOG_FILE_PATH)
    control_service('start', daemon=DAEMON_NAME)

    TimeMachine.travel_to_future(time_to_timedelta(new_datetime))

    for file in file_structure:
        absolute_file_path = os.path.join(file['folder_path'], file['filename'])

        log_callback = logcollector.callback_file_matches_pattern(cfg['location'], absolute_file_path, prefix=prefix)
        wazuh_log_monitor.start(timeout=5, callback=log_callback,
                                error_message=f'{file["filename"]} was not detected')

        fileinfo = os.stat(absolute_file_path)
        current_time = time.time()
        mfile_time = current_time - fileinfo.st_mtime

        if age_seconds <= int(mfile_time):
            log_callback = logcollector.callback_ignoring_file(absolute_file_path, prefix=prefix)
            wazuh_log_monitor.start(timeout=5, callback=log_callback,
                                    error_message=f'{file["filename"]} was not ignored')
        else:
            with pytest.raises(TimeoutError):
                log_callback = logcollector.callback_ignoring_file(absolute_file_path, prefix=prefix)
                wazuh_log_monitor.start(timeout=5, callback=log_callback,
                                        error_message=f'{file["filename"]} was not ignored')

    TimeMachine.time_rollback()
