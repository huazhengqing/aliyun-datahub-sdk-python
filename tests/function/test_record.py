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
import decimal

from six.moves import configparser

from datahub import DataHub
from datahub.exceptions import ResourceExistException, InvalidOperationException
from datahub.models import RecordSchema, FieldType, TupleRecord, BlobRecord, CursorType, CompressFormat

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

dh = DataHub(access_id, access_key, endpoint, enable_pb=False)
dh_lz4 = DataHub(access_id, access_key, endpoint, enable_pb=False, compress_format=CompressFormat.LZ4)
dh_zlib = DataHub(access_id, access_key, endpoint, enable_pb=False, compress_format=CompressFormat.ZLIB)
dh_deflate = DataHub(access_id, access_key, endpoint, enable_pb=False, compress_format=CompressFormat.DEFLATE)
dh_pb = DataHub(access_id, access_key, endpoint, enable_pb=True)
dh_pb_lz4 = DataHub(access_id, access_key, endpoint, enable_pb=True, compress_format=CompressFormat.LZ4)
dh_pb_zlib = DataHub(access_id, access_key, endpoint, enable_pb=True, compress_format=CompressFormat.ZLIB)
dh_pb_deflate = DataHub(access_id, access_key, endpoint, enable_pb=True, compress_format=CompressFormat.DEFLATE)


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


class TestRecord:

    def test_put_get_tuple_records(self):
        project_name = "record_test_p%d_1" % int(time.time())
        topic_name = "record_test_t%d_1" % int(time.time())

        record_schema = RecordSchema.from_lists(
            ['bigint_field', 'string_field', 'double_field', 'bool_field', 'time_field', 'decimal_field'],
            [FieldType.BIGINT, FieldType.STRING, FieldType.DOUBLE, FieldType.BOOLEAN, FieldType.TIMESTAMP, FieldType.DECIMAL],
            [False, True, True, True, True, True])

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

            # ======================= put record =======================
            # put tuple records
            failed_records = []
            record = TupleRecord(schema=record_schema,
                                 values=[99, 'yc1', 10.01, True, 1455869335000000,
                                         decimal.Decimal('12.2219999999999995310417943983338773250579833984375')])

            # write by partition key
            record.partition_key = 'TestPartitionKey'
            put_result = dh.put_records(project_name, topic_name, [record])
            failed_records.extend(put_result.failed_records)

            # write by hash key
            record.hash_key = '4FFFFFFFFFFFFFFD7FFFFFFFFFFFFFFD'
            put_result = dh.put_records(project_name, topic_name, [record])
            failed_records.extend(put_result.failed_records)

            # write by shard id
            record.shard_id = '0'
            record.put_attribute('AK', '47')
            put_result = dh.put_records(project_name, topic_name, [record])
            failed_records.extend(put_result.failed_records)

            record1 = TupleRecord(schema=record_schema)
            record1.set_value('bigint_field', 2)
            record1.set_value('string_field', 'yc2')
            record1.set_value('double_field', None)
            record1.set_value(3, False)
            record1.set_value(4, 1455869335000011)
            record1.set_value(5, decimal.Decimal('12.2219999999999995310417943983338773250579833984375'))
            record1.attributes = {'key': 'value'}
            record1.shard_id = '0'

            put_result = dh.put_records(project_name, topic_name, [record1, record1, record1])
            failed_records.extend(put_result.failed_records)

            print(put_result)
            print("put result: %s" % put_result)
            print("failed records: %s" % put_result.failed_records)

            print(failed_records)
            assert len(failed_records) == 0

            # ======================= get record =======================
            cursor = dh.get_cursor(project_name, topic_name, '0', CursorType.OLDEST)
            record_result = dh.get_tuple_records(project_name, topic_name, '0', record_schema, cursor.cursor, 4)
            print(record_result)
            print(record_result.records[3])
            assert record_result.record_count == 4
            assert record_result.records[0].sequence == record_result.start_seq
            assert record_result.records[1].sequence == record_result.start_seq + 1
            assert record_result.records[2].sequence == record_result.start_seq + 2
        finally:
            clean_topic(dh, project_name)
            dh.delete_project(project_name)

    def test_put_get_tuple_records_lz4(self):
        project_name = "record_test_p%d_1" % int(time.time())
        topic_name = "record_test_t%d_1" % int(time.time())

        record_schema = RecordSchema.from_lists(
            ['bigint_field', 'string_field', 'double_field', 'bool_field', 'time_field', 'decimal_field'],
            [FieldType.BIGINT, FieldType.STRING, FieldType.DOUBLE, FieldType.BOOLEAN, FieldType.TIMESTAMP, FieldType.DECIMAL],
            [False, True, True, True, True, True])

        try:
            dh_lz4.create_project(project_name, '')
        except ResourceExistException:
            pass

        # make sure project wil be deleted
        try:
            try:
                dh_lz4.create_tuple_topic(project_name, topic_name, 3, 7, record_schema, '1')
                dh_lz4.wait_shards_ready(project_name, topic_name)
            except ResourceExistException:
                pass

            # ======================= put record =======================
            # put tuple records
            failed_records = []
            record = TupleRecord(schema=record_schema,
                                 values=[99, 'yc1', 10.01, True, 1455869335000000,
                                         decimal.Decimal('12.2219999999999995310417943983338773250579833984375')])

            # write by partition key
            record.partition_key = 'TestPartitionKey'
            put_result = dh_lz4.put_records(project_name, topic_name, [record])
            failed_records.extend(put_result.failed_records)

            # write by hash key
            record.hash_key = '4FFFFFFFFFFFFFFD7FFFFFFFFFFFFFFD'
            put_result = dh_lz4.put_records(project_name, topic_name, [record])
            failed_records.extend(put_result.failed_records)

            # write by shard id
            record.shard_id = '0'
            record.put_attribute('AK', '47')
            put_result = dh_lz4.put_records(project_name, topic_name, [record])
            failed_records.extend(put_result.failed_records)

            record1 = TupleRecord(schema=record_schema)
            record1.set_value('bigint_field', 2)
            record1.set_value('string_field', 'yc2')
            record1.set_value('double_field', None)
            record1.set_value(3, False)
            record1.set_value(4, 1455869335000011)
            record1.set_value(5, decimal.Decimal('12.2219999999999995310417943983338773250579833984375'))
            record1.attributes = {'key': 'value'}
            record1.shard_id = '0'

            put_result = dh_lz4.put_records(project_name, topic_name, [record1, record1, record1])
            failed_records.extend(put_result.failed_records)

            print(put_result)
            print("put result: %s" % put_result)
            print("failed records: %s" % put_result.failed_records)

            print(failed_records)
            assert len(failed_records) == 0

            # ======================= get record =======================
            cursor = dh_lz4.get_cursor(project_name, topic_name, '0', CursorType.OLDEST)
            record_result = dh_lz4.get_tuple_records(project_name, topic_name, '0', record_schema, cursor.cursor, 4)
            print(record_result)
            print(record_result.records[3])
            assert record_result.record_count == 4
            assert record_result.records[0].sequence == record_result.start_seq
            assert record_result.records[1].sequence == record_result.start_seq + 1
            assert record_result.records[2].sequence == record_result.start_seq + 2
        finally:
            clean_topic(dh_lz4, project_name)
            dh.delete_project(project_name)

    def test_put_get_tuple_records_zlib(self):
        project_name = "record_test_p%d_1" % int(time.time())
        topic_name = "record_test_t%d_1" % int(time.time())

        record_schema = RecordSchema.from_lists(
            ['bigint_field', 'string_field', 'double_field', 'bool_field', 'time_field', 'decimal_field'],
            [FieldType.BIGINT, FieldType.STRING, FieldType.DOUBLE, FieldType.BOOLEAN, FieldType.TIMESTAMP, FieldType.DECIMAL],
            [False, True, True, True, True, True])

        try:
            dh_zlib.create_project(project_name, '')
        except ResourceExistException:
            pass

        # make sure project wil be deleted
        try:
            try:
                dh_zlib.create_tuple_topic(project_name, topic_name, 3, 7, record_schema, '1')
                dh_zlib.wait_shards_ready(project_name, topic_name)
            except ResourceExistException:
                pass

            # ======================= put record =======================
            # put tuple records
            failed_records = []
            record = TupleRecord(schema=record_schema,
                                 values=[99, 'yc1', 10.01, True, 1455869335000000,
                                         decimal.Decimal('12.2219999999999995310417943983338773250579833984375')])

            # write by partition key
            record.partition_key = 'TestPartitionKey'
            put_result = dh_zlib.put_records(project_name, topic_name, [record])
            failed_records.extend(put_result.failed_records)

            # write by hash key
            record.hash_key = '4FFFFFFFFFFFFFFD7FFFFFFFFFFFFFFD'
            put_result = dh_zlib.put_records(project_name, topic_name, [record])
            failed_records.extend(put_result.failed_records)

            # write by shard id
            record.shard_id = '0'
            record.put_attribute('AK', '47')
            put_result = dh_zlib.put_records(project_name, topic_name, [record])
            failed_records.extend(put_result.failed_records)

            record1 = TupleRecord(schema=record_schema)
            record1.set_value('bigint_field', 2)
            record1.set_value('string_field', 'yc2')
            record1.set_value('double_field', None)
            record1.set_value(3, False)
            record1.set_value(4, 1455869335000011)
            record1.set_value(5, decimal.Decimal('12.2219999999999995310417943983338773250579833984375'))
            record1.attributes = {'key': 'value'}
            record1.shard_id = '0'

            put_result = dh_zlib.put_records(project_name, topic_name, [record1, record1, record1])
            failed_records.extend(put_result.failed_records)

            print(put_result)
            print("put result: %s" % put_result)
            print("failed records: %s" % put_result.failed_records)

            print(failed_records)
            assert len(failed_records) == 0

            # ======================= get record =======================
            cursor = dh_zlib.get_cursor(project_name, topic_name, '0', CursorType.OLDEST)
            record_result = dh_zlib.get_tuple_records(project_name, topic_name, '0', record_schema, cursor.cursor, 4)
            print(record_result)
            print(record_result.records[3])
            assert record_result.record_count == 4
            assert record_result.records[0].sequence == record_result.start_seq
            assert record_result.records[1].sequence == record_result.start_seq + 1
            assert record_result.records[2].sequence == record_result.start_seq + 2
        finally:
            clean_topic(dh_zlib, project_name)
            dh.delete_project(project_name)

    def test_put_get_tuple_records_deflate(self):
        project_name = "record_test_p%d_1" % int(time.time())
        topic_name = "record_test_t%d_1" % int(time.time())

        record_schema = RecordSchema.from_lists(
            ['bigint_field', 'string_field', 'double_field', 'bool_field', 'time_field', 'decimal_field'],
            [FieldType.BIGINT, FieldType.STRING, FieldType.DOUBLE, FieldType.BOOLEAN, FieldType.TIMESTAMP, FieldType.DECIMAL],
            [False, True, True, True, True, True])

        try:
            dh_deflate.create_project(project_name, '')
        except ResourceExistException:
            pass

        # make sure project wil be deleted
        try:
            try:
                dh_deflate.create_tuple_topic(project_name, topic_name, 3, 7, record_schema, '1')
                dh_deflate.wait_shards_ready(project_name, topic_name)
            except ResourceExistException:
                pass

            # ======================= put record =======================
            # put tuple records
            failed_records = []
            record = TupleRecord(schema=record_schema,
                                 values=[99, 'yc1', 10.01, True, 1455869335000000,
                                         decimal.Decimal('12.2219999999999995310417943983338773250579833984375')])

            # write by partition key
            record.partition_key = 'TestPartitionKey'
            put_result = dh_deflate.put_records(project_name, topic_name, [record])
            failed_records.extend(put_result.failed_records)

            # write by hash key
            record.hash_key = '4FFFFFFFFFFFFFFD7FFFFFFFFFFFFFFD'
            put_result = dh_deflate.put_records(project_name, topic_name, [record])
            failed_records.extend(put_result.failed_records)

            # write by shard id
            record.shard_id = '0'
            record.put_attribute('AK', '47')
            put_result = dh_deflate.put_records(project_name, topic_name, [record])
            failed_records.extend(put_result.failed_records)

            record1 = TupleRecord(schema=record_schema)
            record1.set_value('bigint_field', 2)
            record1.set_value('string_field', 'yc2')
            record1.set_value('double_field', None)
            record1.set_value(3, False)
            record1.set_value(4, 1455869335000011)
            record1.set_value(5, decimal.Decimal('12.2219999999999995310417943983338773250579833984375'))
            record1.attributes = {'key': 'value'}
            record1.shard_id = '0'

            put_result = dh_deflate.put_records(project_name, topic_name, [record1, record1, record1])
            failed_records.extend(put_result.failed_records)

            print(put_result)
            print("put result: %s" % put_result)
            print("failed records: %s" % put_result.failed_records)

            print(failed_records)
            assert len(failed_records) == 0

            # ======================= get record =======================
            cursor = dh_deflate.get_cursor(project_name, topic_name, '0', CursorType.OLDEST)
            record_result = dh_deflate.get_tuple_records(project_name, topic_name, '0', record_schema, cursor.cursor, 4)
            print(record_result)
            print(record_result.records[3])
            assert record_result.record_count == 4
            assert record_result.records[0].sequence == record_result.start_seq
            assert record_result.records[1].sequence == record_result.start_seq + 1
            assert record_result.records[2].sequence == record_result.start_seq + 2
        finally:
            clean_topic(dh_deflate, project_name)
            dh.delete_project(project_name)

    def test_put_get_tuple_records_pb(self):
        project_name = "record_test_p%d_1" % int(time.time())
        topic_name = "record_test_t%d_1" % int(time.time())

        record_schema = RecordSchema.from_lists(
            ['bigint_field', 'string_field', 'double_field', 'bool_field', 'time_field'],
            [FieldType.BIGINT, FieldType.STRING, FieldType.DOUBLE, FieldType.BOOLEAN, FieldType.TIMESTAMP])

        try:
            dh_pb.create_project(project_name, '')
        except ResourceExistException:
            pass

        # make sure project wil be deleted
        try:
            try:
                dh_pb.create_tuple_topic(project_name, topic_name, 3, 7, record_schema, '1')
                dh_pb.wait_shards_ready(project_name, topic_name)
            except ResourceExistException:
                pass

            # ======================= put record =======================
            # put tuple records
            failed_records = []
            record = TupleRecord(schema=record_schema, values=[99, 'yc1', 10.01, True, 1455869335000000])

            # write by partition key
            record.partition_key = 'TestPartitionKey'
            put_result = dh_pb.put_records(project_name, topic_name, [record])
            failed_records.extend(put_result.failed_records)

            # write by hash key
            record.hash_key = '4FFFFFFFFFFFFFFD7FFFFFFFFFFFFFFD'
            put_result = dh_pb.put_records(project_name, topic_name, [record])
            failed_records.extend(put_result.failed_records)

            # write by shard id
            record.shard_id = '0'
            record.put_attribute('AK', '47')
            put_result = dh_pb.put_records(project_name, topic_name, [record])
            failed_records.extend(put_result.failed_records)

            # test failed records
            record1 = TupleRecord(schema=record_schema)
            record1.values = [99, 'yc1', 10.01, True, 1455869335000000]
            record1.shard_id = '-1'
            record1.put_attribute('a', 'b')

            put_result = dh_pb.put_records(project_name, topic_name, [record1, record1, record1])
            failed_records.extend(put_result.failed_records)

            print(put_result)
            print("put result: %s" % put_result)
            print("failed records: %s" % put_result.failed_records)

            print(failed_records)
            assert len(failed_records) == 3
            for i in range(0, 3):
                assert failed_records[i].error_code == 'InvalidShardId'
                assert failed_records[i].error_message == 'Invalid shard id: -1'

            # ======================= get record =======================
            cursor = dh_pb.get_cursor(project_name, topic_name, '0', CursorType.OLDEST)
            record_result = dh_pb.get_tuple_records(project_name, topic_name, '0', record_schema, cursor.cursor, 3)
            print(record_result)
            assert record_result.record_count == 2
            assert record_result.records[0].values == record.values
            assert record_result.records[0].sequence == record_result.start_seq
            assert record_result.records[1].sequence == record_result.start_seq + 1
        finally:
            clean_topic(dh_pb, project_name)
            dh_pb.delete_project(project_name)

    def test_put_get_tuple_records_pb_lz4(self):
        project_name = "record_test_p%d_1" % int(time.time())
        topic_name = "record_test_t%d_1" % int(time.time())

        record_schema = RecordSchema.from_lists(
            ['bigint_field', 'string_field', 'double_field', 'bool_field', 'time_field'],
            [FieldType.BIGINT, FieldType.STRING, FieldType.DOUBLE, FieldType.BOOLEAN, FieldType.TIMESTAMP])

        try:
            dh_pb_lz4.create_project(project_name, '')
        except ResourceExistException:
            pass

        # make sure project wil be deleted
        try:
            try:
                dh_pb_lz4.create_tuple_topic(project_name, topic_name, 3, 7, record_schema, '1')
                dh_pb_lz4.wait_shards_ready(project_name, topic_name)
            except ResourceExistException:
                pass

            # ======================= put record =======================
            # put tuple records
            failed_records = []
            record = TupleRecord(schema=record_schema, values=[99, 'yc1', 10.01, True, 1455869335000000])

            # write by partition key
            record.partition_key = 'TestPartitionKey'
            put_result = dh_pb_lz4.put_records(project_name, topic_name, [record])
            failed_records.extend(put_result.failed_records)

            # write by hash key
            record.hash_key = '4FFFFFFFFFFFFFFD7FFFFFFFFFFFFFFD'
            put_result = dh_pb_lz4.put_records(project_name, topic_name, [record])
            failed_records.extend(put_result.failed_records)

            # write by shard id
            record.shard_id = '0'
            record.put_attribute('AK', '47')
            put_result = dh_pb_lz4.put_records(project_name, topic_name, [record])
            failed_records.extend(put_result.failed_records)

            record1 = TupleRecord(schema=record_schema)
            record1.values = [99, 'yc1', 10.01, True, 1455869335000000]
            record1.shard_id = '0'
            record1.put_attribute('a', 'b')

            put_result = dh_pb_lz4.put_records(project_name, topic_name, [record1, record1, record1])
            failed_records.extend(put_result.failed_records)

            print(put_result)
            print("put result: %s" % put_result)
            print("failed records: %s" % put_result.failed_records)

            print(failed_records)
            assert len(failed_records) == 0

            # ======================= get record =======================
            cursor = dh_pb_lz4.get_cursor(project_name, topic_name, '0', CursorType.OLDEST)
            record_result = dh_pb_lz4.get_tuple_records(project_name, topic_name, '0', record_schema, cursor.cursor, 3)
            print(record_result)
            assert record_result.record_count == 3
            assert record_result.records[0].values == record.values
            assert record_result.records[0].sequence == record_result.start_seq
            assert record_result.records[1].sequence == record_result.start_seq + 1
            assert record_result.records[2].sequence == record_result.start_seq + 2
        finally:
            clean_topic(dh_pb_lz4, project_name)
            dh_pb_lz4.delete_project(project_name)

    def test_put_get_tuple_records_pb_zlib(self):
        project_name = "record_test_p%d_1" % int(time.time())
        topic_name = "record_test_t%d_1" % int(time.time())

        record_schema = RecordSchema.from_lists(
            ['bigint_field', 'string_field', 'double_field', 'bool_field', 'time_field'],
            [FieldType.BIGINT, FieldType.STRING, FieldType.DOUBLE, FieldType.BOOLEAN, FieldType.TIMESTAMP])

        try:
            dh_pb_zlib.create_project(project_name, '')
        except ResourceExistException:
            pass

        # make sure project wil be deleted
        try:
            try:
                dh_pb_zlib.create_tuple_topic(project_name, topic_name, 3, 7, record_schema, '1')
                dh_pb_zlib.wait_shards_ready(project_name, topic_name)
            except ResourceExistException:
                pass

            # ======================= put record =======================
            # put tuple records
            failed_records = []
            record = TupleRecord(schema=record_schema, values=[99, 'yc1', 10.01, True, 1455869335000000])

            # write by partition key
            record.partition_key = 'TestPartitionKey'
            put_result = dh_pb_zlib.put_records(project_name, topic_name, [record])
            failed_records.extend(put_result.failed_records)

            # write by hash key
            record.hash_key = '4FFFFFFFFFFFFFFD7FFFFFFFFFFFFFFD'
            put_result = dh_pb_zlib.put_records(project_name, topic_name, [record])
            failed_records.extend(put_result.failed_records)

            # write by shard id
            record.shard_id = '0'
            record.put_attribute('AK', '47')
            put_result = dh_pb_zlib.put_records(project_name, topic_name, [record])
            failed_records.extend(put_result.failed_records)

            record1 = TupleRecord(schema=record_schema)
            record1.values = [99, 'yc1', 10.01, True, 1455869335000000]
            record1.shard_id = '0'
            record1.put_attribute('a', 'b')

            put_result = dh_pb_zlib.put_records(project_name, topic_name, [record1, record1, record1])
            failed_records.extend(put_result.failed_records)

            print(put_result)
            print("put result: %s" % put_result)
            print("failed records: %s" % put_result.failed_records)

            print(failed_records)
            assert len(failed_records) == 0

            # ======================= get record =======================
            cursor = dh_pb_zlib.get_cursor(project_name, topic_name, '0', CursorType.OLDEST)
            record_result = dh_pb_zlib.get_tuple_records(project_name, topic_name, '0', record_schema, cursor.cursor, 3)
            print(record_result)
            assert record_result.record_count == 3
            assert record_result.records[0].values == record.values
            assert record_result.records[0].sequence == record_result.start_seq
            assert record_result.records[1].sequence == record_result.start_seq + 1
            assert record_result.records[2].sequence == record_result.start_seq + 2
        finally:
            clean_topic(dh_pb_zlib, project_name)
            dh_pb_zlib.delete_project(project_name)

    def test_put_get_tuple_records_pb_deflate(self):
        project_name = "record_test_p%d_1" % int(time.time())
        topic_name = "record_test_t%d_1" % int(time.time())

        record_schema = RecordSchema.from_lists(
            ['bigint_field', 'string_field', 'double_field', 'bool_field', 'time_field'],
            [FieldType.BIGINT, FieldType.STRING, FieldType.DOUBLE, FieldType.BOOLEAN, FieldType.TIMESTAMP])

        try:
            dh_pb_deflate.create_project(project_name, '')
        except ResourceExistException:
            pass

        # make sure project wil be deleted
        try:
            try:
                dh_pb_deflate.create_tuple_topic(project_name, topic_name, 3, 7, record_schema, '1')
                dh_pb_deflate.wait_shards_ready(project_name, topic_name)
            except ResourceExistException:
                pass

            # ======================= put record =======================
            # put tuple records
            failed_records = []
            record = TupleRecord(schema=record_schema, values=[99, 'yc1', 10.01, True, 1455869335000000])

            # write by partition key
            record.partition_key = 'TestPartitionKey'
            put_result = dh_pb_deflate.put_records(project_name, topic_name, [record])
            failed_records.extend(put_result.failed_records)

            # write by hash key
            record.hash_key = '4FFFFFFFFFFFFFFD7FFFFFFFFFFFFFFD'
            put_result = dh_pb_deflate.put_records(project_name, topic_name, [record])
            failed_records.extend(put_result.failed_records)

            # write by shard id
            record.shard_id = '0'
            record.put_attribute('AK', '47')
            put_result = dh_pb_deflate.put_records(project_name, topic_name, [record])
            failed_records.extend(put_result.failed_records)

            record1 = TupleRecord(schema=record_schema)
            record1.values = [99, 'yc1', 10.01, True, 1455869335000000]
            record1.shard_id = '0'
            record1.put_attribute('a', 'b')

            put_result = dh_pb_deflate.put_records(project_name, topic_name, [record1, record1, record1])
            failed_records.extend(put_result.failed_records)

            print(put_result)
            print("put result: %s" % put_result)
            print("failed records: %s" % put_result.failed_records)

            print(failed_records)
            assert len(failed_records) == 0

            # ======================= get record =======================
            cursor = dh_pb_deflate.get_cursor(project_name, topic_name, '0', CursorType.OLDEST)
            record_result = dh_pb_deflate.get_tuple_records(project_name, topic_name, '0', record_schema, cursor.cursor, 3)
            print(record_result)
            assert record_result.record_count == 3
            assert record_result.records[0].values == record.values
            assert record_result.records[0].sequence == record_result.start_seq
            assert record_result.records[1].sequence == record_result.start_seq + 1
            assert record_result.records[2].sequence == record_result.start_seq + 2
        finally:
            clean_topic(dh_pb_deflate, project_name)
            dh_pb_deflate.delete_project(project_name)

    def test_put_get_blob_records(self):
        project_name = "record_test_p%d_2" % int(time.time())
        topic_name = "record_test_t%d_2" % int(time.time())

        try:
            dh.create_project(project_name, '')
        except ResourceExistException:
            pass

        # make sure project wil be deleted
        try:
            try:
                dh.create_blob_topic(project_name, topic_name, 3, 7, '')
                dh.wait_shards_ready(project_name, topic_name)
            except ResourceExistException:
                pass

            # ======================= put record =======================
            # put blob record
            data = None
            with open(os.path.join(root_path, 'tests/resources/datahub.png'), 'rb') as f:
                data = f.read()

            records = []

            record0 = BlobRecord(blob_data=data)
            record0.shard_id = '0'
            record0.put_attribute('a', 'b')
            records.append(record0)

            failed_indices = (dh.put_records(project_name, topic_name, records)).failed_records
            assert len(failed_indices) == 0

            # ======================= get record =======================
            cursor = dh.get_cursor(project_name, topic_name, '0', CursorType.OLDEST)
            record_result = dh.get_blob_records(project_name, topic_name, '0', cursor.cursor, 3)
            print(record_result)
            assert record_result.record_count == 1
            assert record_result.records[0].blob_data == data
        finally:
            clean_topic(dh, project_name)
            dh.delete_project(project_name)

    def test_put_get_blob_records_lz4(self):
        project_name = "record_test_p%d_2" % int(time.time())
        topic_name = "record_test_t%d_2" % int(time.time())

        try:
            dh_lz4.create_project(project_name, '')
        except ResourceExistException:
            pass

        # make sure project wil be deleted
        try:
            try:
                dh_lz4.create_blob_topic(project_name, topic_name, 3, 7, '')
                dh_lz4.wait_shards_ready(project_name, topic_name)
            except ResourceExistException:
                pass

            # ======================= put record =======================
            # put blob record
            data = None
            with open(os.path.join(root_path, 'tests/resources/datahub.png'), 'rb') as f:
                data = f.read()

            records = []

            record0 = BlobRecord(blob_data=data)
            record0.shard_id = '0'
            record0.put_attribute('a', 'b')
            records.append(record0)

            failed_indices = (dh_lz4.put_records(project_name, topic_name, records)).failed_records
            assert len(failed_indices) == 0

            # ======================= get record =======================
            cursor = dh_lz4.get_cursor(project_name, topic_name, '0', CursorType.OLDEST)
            record_result = dh_lz4.get_blob_records(project_name, topic_name, '0', cursor.cursor, 3)
            print(record_result)
            assert record_result.record_count == 1
            assert record_result.records[0].blob_data == data
        finally:
            clean_topic(dh_lz4, project_name)
            dh_lz4.delete_project(project_name)

    def test_put_get_blob_records_zlib(self):
        project_name = "record_test_p%d_2" % int(time.time())
        topic_name = "record_test_t%d_2" % int(time.time())

        try:
            dh_zlib.create_project(project_name, '')
        except ResourceExistException:
            pass

        # make sure project wil be deleted
        try:
            try:
                dh_zlib.create_blob_topic(project_name, topic_name, 3, 7, '')
                dh_zlib.wait_shards_ready(project_name, topic_name)
            except ResourceExistException:
                pass

            # ======================= put record =======================
            # put blob record
            data = None
            with open(os.path.join(root_path, 'tests/resources/datahub.png'), 'rb') as f:
                data = f.read()

            records = []

            record0 = BlobRecord(blob_data=data)
            record0.shard_id = '0'
            record0.put_attribute('a', 'b')
            records.append(record0)

            failed_indices = (dh_zlib.put_records(project_name, topic_name, records)).failed_records
            assert len(failed_indices) == 0

            # ======================= get record =======================
            cursor = dh_zlib.get_cursor(project_name, topic_name, '0', CursorType.OLDEST)
            record_result = dh_zlib.get_blob_records(project_name, topic_name, '0', cursor.cursor, 3)
            print(record_result)
            assert record_result.record_count == 1
            assert record_result.records[0].blob_data == data
        finally:
            clean_topic(dh_zlib, project_name)
            dh_zlib.delete_project(project_name)

    def test_put_get_blob_records_deflate(self):
        project_name = "record_test_p%d_2" % int(time.time())
        topic_name = "record_test_t%d_2" % int(time.time())

        try:
            dh_deflate.create_project(project_name, '')
        except ResourceExistException:
            pass

        # make sure project wil be deleted
        try:
            try:
                dh_deflate.create_blob_topic(project_name, topic_name, 3, 7, '')
                dh_deflate.wait_shards_ready(project_name, topic_name)
            except ResourceExistException:
                pass

            # ======================= put record =======================
            # put blob record
            data = None
            with open(os.path.join(root_path, 'tests/resources/datahub.png'), 'rb') as f:
                data = f.read()

            records = []

            record0 = BlobRecord(blob_data=data)
            record0.shard_id = '0'
            record0.put_attribute('a', 'b')
            records.append(record0)

            failed_indices = (dh_deflate.put_records(project_name, topic_name, records)).failed_records
            assert len(failed_indices) == 0

            # ======================= get record =======================
            cursor = dh_deflate.get_cursor(project_name, topic_name, '0', CursorType.OLDEST)
            record_result = dh_deflate.get_blob_records(project_name, topic_name, '0', cursor.cursor, 3)
            print(record_result)
            assert record_result.record_count == 1
            assert record_result.records[0].blob_data == data
        finally:
            clean_topic(dh_deflate, project_name)
            dh_deflate.delete_project(project_name)

    def test_put_get_blob_records_pb(self):
        project_name = "record_test_p%d_2" % int(time.time())
        topic_name = "record_test_t%d_2" % int(time.time())

        try:
            dh_pb.create_project(project_name, '')
        except ResourceExistException:
            pass

        # make sure project wil be deleted
        try:
            try:
                dh_pb.create_blob_topic(project_name, topic_name, 3, 7, '')
                dh_pb.wait_shards_ready(project_name, topic_name)
            except ResourceExistException:
                pass

            # ======================= put record =======================
            # put blob record
            data = None
            with open(os.path.join(root_path, 'tests/resources/datahub.png'), 'rb') as f:
                data = f.read()

            records = []

            record0 = BlobRecord(blob_data=data)
            record0.shard_id = '0'
            record0.put_attribute('a', 'b')
            records.append(record0)

            failed_indices = (dh_pb.put_records(project_name, topic_name, records)).failed_records
            assert len(failed_indices) == 0

            # ======================= get record =======================
            cursor = dh_pb.get_cursor(project_name, topic_name, '0', CursorType.OLDEST)
            record_result = dh_pb.get_blob_records(project_name, topic_name, '0', cursor.cursor, 3)
            print(record_result)
            assert record_result.record_count == 1
            assert record_result.records[0].blob_data == data
        finally:
            clean_topic(dh_pb, project_name)
            dh_pb.delete_project(project_name)

    def test_put_get_blob_records_pb_lz4(self):
        project_name = "record_test_p%d_2" % int(time.time())
        topic_name = "record_test_t%d_2" % int(time.time())

        try:
            dh_pb_lz4.create_project(project_name, '')
        except ResourceExistException:
            pass

        # make sure project wil be deleted
        try:
            try:
                dh_pb_lz4.create_blob_topic(project_name, topic_name, 3, 7, '')
                dh_pb_lz4.wait_shards_ready(project_name, topic_name)
            except ResourceExistException:
                pass

            # ======================= put record =======================
            # put blob record
            data = None
            with open(os.path.join(root_path, 'tests/resources/datahub.png'), 'rb') as f:
                data = f.read()

            records = []

            record0 = BlobRecord(blob_data=data)
            record0.shard_id = '0'
            record0.put_attribute('a', 'b')
            records.append(record0)

            failed_indices = (dh_pb_lz4.put_records(project_name, topic_name, records)).failed_records
            assert len(failed_indices) == 0

            # ======================= get record =======================
            cursor = dh_pb_lz4.get_cursor(project_name, topic_name, '0', CursorType.OLDEST)
            record_result = dh_pb_lz4.get_blob_records(project_name, topic_name, '0', cursor.cursor, 3)
            print(record_result)
            assert record_result.record_count == 1
            assert record_result.records[0].blob_data == data
        finally:
            clean_topic(dh_pb_lz4, project_name)
            dh_pb_lz4.delete_project(project_name)

    def test_put_get_blob_records_pb_zlib(self):
        project_name = "record_test_p%d_2" % int(time.time())
        topic_name = "record_test_t%d_2" % int(time.time())

        try:
            dh_pb_zlib.create_project(project_name, '')
        except ResourceExistException:
            pass

        # make sure project wil be deleted
        try:
            try:
                dh_pb_zlib.create_blob_topic(project_name, topic_name, 3, 7, '')
                dh_pb_zlib.wait_shards_ready(project_name, topic_name)
            except ResourceExistException:
                pass

            # ======================= put record =======================
            # put blob record
            data = None
            with open(os.path.join(root_path, 'tests/resources/datahub.png'), 'rb') as f:
                data = f.read()

            records = []

            record0 = BlobRecord(blob_data=data)
            record0.shard_id = '0'
            record0.put_attribute('a', 'b')
            records.append(record0)

            failed_indices = (dh_pb_zlib.put_records(project_name, topic_name, records)).failed_records
            assert len(failed_indices) == 0

            # ======================= get record =======================
            cursor = dh_pb_zlib.get_cursor(project_name, topic_name, '0', CursorType.OLDEST)
            record_result = dh_pb_zlib.get_blob_records(project_name, topic_name, '0', cursor.cursor, 3)
            print(record_result)
            assert record_result.record_count == 1
            assert record_result.records[0].blob_data == data
        finally:
            clean_topic(dh_pb_zlib, project_name)
            dh_pb_zlib.delete_project(project_name)

    def test_put_get_blob_records_pb_deflate(self):
        project_name = "record_test_p%d_2" % int(time.time())
        topic_name = "record_test_t%d_2" % int(time.time())

        try:
            dh_pb_deflate.create_project(project_name, '')
        except ResourceExistException:
            pass

        # make sure project wil be deleted
        try:
            try:
                dh_pb_deflate.create_blob_topic(project_name, topic_name, 3, 7, '')
                dh_pb_deflate.wait_shards_ready(project_name, topic_name)
            except ResourceExistException:
                pass

            # ======================= put record =======================
            # put blob record
            data = None
            with open(os.path.join(root_path, 'tests/resources/datahub.png'), 'rb') as f:
                data = f.read()

            records = []

            record0 = BlobRecord(blob_data=data)
            record0.shard_id = '0'
            record0.put_attribute('a', 'b')
            records.append(record0)

            failed_indices = (dh_pb_deflate.put_records(project_name, topic_name, records)).failed_records
            assert len(failed_indices) == 0

            # ======================= get record =======================
            cursor = dh_pb_deflate.get_cursor(project_name, topic_name, '0', CursorType.OLDEST)
            record_result = dh_pb_deflate.get_blob_records(project_name, topic_name, '0', cursor.cursor, 3)
            print(record_result)
            assert record_result.record_count == 1
            assert record_result.records[0].blob_data == data
        finally:
            clean_topic(dh_pb_deflate, project_name)
            dh_pb_deflate.delete_project(project_name)


# run directly
if __name__ == '__main__':
    test = TestRecord()
    test.test_put_get_tuple_records()
    test.test_put_get_tuple_records_lz4()
    test.test_put_get_tuple_records_zlib()
    test.test_put_get_tuple_records_deflate()

    test.test_put_get_blob_records()
    test.test_put_get_blob_records_lz4()
    test.test_put_get_blob_records_zlib()
    test.test_put_get_blob_records_deflate()

    test.test_put_get_tuple_records_pb()
    test.test_put_get_tuple_records_pb_lz4()
    test.test_put_get_tuple_records_pb_zlib()
    test.test_put_get_tuple_records_pb_deflate()

    test.test_put_get_blob_records_pb()
    test.test_put_get_blob_records_pb_lz4()
    test.test_put_get_blob_records_pb_zlib()
    test.test_put_get_blob_records_pb_deflate()
