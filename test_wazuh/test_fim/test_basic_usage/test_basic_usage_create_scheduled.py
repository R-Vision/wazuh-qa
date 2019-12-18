# Copyright (C) 2015-2019, Wazuh Inc.
# Created by Wazuh, Inc. <info@wazuh.com>.
# This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

import os
import sys
from datetime import timedelta

import pytest
from wazuh_testing.fim import CHECK_ALL, DEFAULT_TIMEOUT, FIFO, LOG_FILE_PATH, REGULAR, SOCKET, callback_detect_event, \
    create_file, validate_event, generate_params
from wazuh_testing.tools import FileMonitor, TimeMachine, check_apply_test, load_wazuh_configurations, PREFIX

# variables
test_directories = [os.path.join(PREFIX, 'testdir1'), os.path.join(PREFIX, 'testdir2')]

directory_str = ','.join(test_directories + [os.path.join(PREFIX, 'noexists')])

wazuh_log_monitor = FileMonitor(LOG_FILE_PATH)
test_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
configurations_path = os.path.join(test_data_path, 'wazuh_conf.yaml')
testdir1, testdir2 = test_directories

# configurations

monitoring_modes = ['scheduled']

conf_params = {'TEST_DIRECTORIES': directory_str, 'MODULE_NAME': __name__}
conf_metadata = {'test_directories': directory_str, 'module_name': __name__}
p, m = generate_params(conf_params, conf_metadata, modes=monitoring_modes)

configurations = load_wazuh_configurations(configurations_path, __name__, params=p, metadata=m)


# fixtures

@pytest.fixture(scope='module', params=configurations)
def get_configuration(request):
    """Get configurations from the module."""
    return request.param


# tests

@pytest.mark.parametrize('folder', [
    testdir1,
    testdir2
])
@pytest.mark.parametrize('name, filetype, content, checkers, tags_to_apply', [
    ('file', REGULAR, 'Sample content', {CHECK_ALL}, {'ossec_conf'}),
    ('file2', REGULAR, b'Sample content', {CHECK_ALL}, {'ossec_conf'}),
    ('socketfile', REGULAR if sys.platform == 'win32' else SOCKET, '', {CHECK_ALL}, {'ossec_conf'}),
    ('file3', REGULAR, 'Sample content', {CHECK_ALL}, {'ossec_conf'}),
    ('fifofile', REGULAR if sys.platform == 'win32' else FIFO, '', {CHECK_ALL}, {'ossec_conf'}),
    ('file4', REGULAR, b'', {CHECK_ALL}, {'ossec_conf'})
])
def test_create_file_scheduled(folder, name, filetype, content, checkers, tags_to_apply, get_configuration,
                               configure_environment, restart_syscheckd, wait_for_initial_scan):
    """ Checks if a special or regular file creation is detected by syscheck using scheduled monitoring

        Regular files must be monitored. Special files must not.

        :param folder: Name of the monitored folder
        :param name: Name of the file
        :param filetype: Type of the file
        :param content: Content of the file
        :param checkers: Checks that will compared to the ones from the event

        * This test is intended to be used with valid configurations files. Each execution of this test will configure
          the environment properly, restart the service and wait for the initial scan.
    """
    check_apply_test(tags_to_apply, get_configuration['tags'])

    # Create files
    create_file(filetype, folder, name, content=content)

    # Go ahead in time to let syscheck perform a new scan
    TimeMachine.travel_to_future(timedelta(hours=13))

    if filetype == REGULAR:
        # Wait until event is detected
        event = wazuh_log_monitor.start(
            timeout=DEFAULT_TIMEOUT, callback=callback_detect_event).result()
        validate_event(event, checkers)
    else:
        with pytest.raises(TimeoutError):
            wazuh_log_monitor.start(timeout=DEFAULT_TIMEOUT, callback=callback_detect_event)