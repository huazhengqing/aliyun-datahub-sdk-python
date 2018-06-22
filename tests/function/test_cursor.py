#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import os
import sys
import time

from six.moves import configparser

from datahub import DataHub
from datahub.exceptions import ResourceExistException, InvalidOperationException
from datahub.models import RecordSchema, FieldType, TupleRecord, CursorType

current_path = os.path.split(os.path.realpath(__file__))[0]
root_path = os.path.join(current_path, '../..')

configer = configparser.ConfigParser()
configer.read(os.path.join(current_path, '../datahub.ini'))
access_id = configer.get('datahub', 'access_id')
access_key = configer.get('datahub', 'access_key')
endpoint = configer.get('datahub', 'endpoint')

print("=======================================")
print("access_id: %s" % access_id)
print("access_key: %s" % access_key)
print("endpoint: %s" % endpoint)
print("=======================================\n\n")

if not access_id or not access_key or not endpoint:
    print("[access_id, access_key, endpoint] must be set in datahub.ini!")
    sys.exit(-1)

dh = DataHub(access_id, access_key, endpoint)


def clean_topic(datahub_client, project_name, force=False):
    topic_names = datahub_client.list_topic(project_name).topic_names
    for topic_name in topic_names:
        if force:
            clean_subscription(datahub_client, project_name, topic_name)
        datahub_client.delete_topic(project_name, topic_name)


def clean_project(datahub_client, force=False):
    project_names = datahub_client.list_project().project_names
    for project_name in project_names:
        if force:
            clean_topic(datahub_client, project_name)
        try:
            datahub_client.delete_project(project_name)
        except InvalidOperationException:
            pass


def clean_subscription(datahub_client, project_name, topic_name):
    subscriptions = datahub_client.list_subscription(project_name, topic_name, '', 1, 100).subscriptions
    for subscription in subscriptions:
        datahub_client.delete_subscription(project_name, topic_name, subscription.sub_id)


class TestCursor:

    def test_get_cursor(self):
        project_name = "cursor_test_p%d_1" % int(time.time())
        topic_name = "cursor_test_t%d_1" % int(time.time())

        record_schema = RecordSchema.from_lists(
            ['bigint_field', 'string_field', 'double_field', 'bool_field', 'event_time1'],
            [FieldType.BIGINT, FieldType.STRING, FieldType.DOUBLE, FieldType.BOOLEAN, FieldType.TIMESTAMP])

        try:
            dh.create_project(project_name, '')
        except ResourceExistException:
            pass

        # make sure project wil be deleted
        try:
            try:
                dh.create_tuple_topic(project_name, topic_name, 3, 7, record_schema, '1')
                dh.wait_shards_ready(project_name, topic_name)
            except ResourceExistException:
                pass

            # put tuple records
            record = TupleRecord(schema=record_schema, values=[1, 'yc1', 10.01, True, 1455869335000000])
            record.shard_id = '0'
            record.put_attribute('AK', '47')
            records = [record for i in range(0, 3)]
            put_record_result = dh.put_records(project_name, topic_name, records)
            print(put_record_result)

            assert put_record_result.failed_record_count == 0

            # ======================= get cursor =======================
            cursor_oldest = dh.get_cursor(project_name, topic_name, '0', CursorType.OLDEST)
            cursor_latest = dh.get_cursor(project_name, topic_name, '0', CursorType.LATEST)
            cursor_sequence_1 = dh.get_cursor(project_name, topic_name, '0', CursorType.SEQUENCE, 0)
            cursor_sequence_2 = dh.get_cursor(project_name, topic_name, '0', CursorType.SEQUENCE, 2)
            cursor_system_time = dh.get_cursor(project_name, topic_name, '0', CursorType.SYSTEM_TIME, 0)
            print(cursor_system_time)

            assert cursor_oldest.cursor == cursor_sequence_1.cursor
            assert cursor_latest.cursor == cursor_sequence_2.cursor
            assert cursor_oldest.cursor == cursor_system_time.cursor
        finally:
            clean_topic(dh, project_name)
            dh.delete_project(project_name)


# run directly
if __name__ == '__main__':
    test = TestCursor()
    test.test_get_cursor()
