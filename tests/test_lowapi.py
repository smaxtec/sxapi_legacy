#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import time

from .util import MockGet, MockPost, MockPut
from sxapi import LowLevelAPI


class LowApiTests(unittest.TestCase):
    INTERN_ENDPOINT = "http://0.0.0.0:8787/internapi/v0"
    PUBLIC_ENDPOINT = "http://0.0.0.0:8989/publicapi/v1"
    API_KEY = "abcd"

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @classmethod
    def setUpClass(cls):
        pass

    def test_status(self):
        api = LowLevelAPI(private_endpoint=self.INTERN_ENDPOINT, public_endpoint=self.PUBLIC_ENDPOINT,
                          api_key=self.API_KEY)
        with MockGet() as patched_session:
            r = api.get_public_status()
            self.assertTrue(r)
            call = patched_session.call_args_list
            self.assertEqual(call[0][0][0], "/service/status")
        with MockGet() as patched_session:
            r = api.get_private_status()
            self.assertTrue(r)
            call = patched_session.call_args_list
            self.assertEqual(call[0][0][0], "/")

    def test_sensordataupdate(self):
        t = int(time.time())
        d1 = {
            "device_id": "1234567890",
            "metric": "ph",
            "data": [(t - 10, 2.0), (t, 2.0), (t + 10, 3.0)]
        }
        d2 = {
            "device_id": "1234567890",
            "metric": "temp",
            "data": [(t, 2.0), (t + 10, 3.0)]
        }

        sxapi = LowLevelAPI(private_endpoint=self.INTERN_ENDPOINT, public_endpoint=self.PUBLIC_ENDPOINT,
                            api_key=self.API_KEY)

        with MockPost() as patched_session:
            sxapi.updateSensorData(**d1)
            call = patched_session.call_args_list
            self.assertTrue(call[0][0][0].endswith("sensordatabulk"))
            self.assertEqual(len(call[0][1]["json"]["sensordata"]), 1)
            self.assertEqual(call[0][1]["json"]["sensordata"][0]["data"],
                             [(t - 10, 2.0), (t, 2.0), (t + 10, 3.0)])
            self.assertEqual(call[0][1]["json"]["sensordata"][0]["metric"],
                             "ph")
            self.assertEqual(call[0][1]["json"]["sensordata"][0]["device_id"],
                             "1234567890")

        with MockPost() as patched_session:
            sxapi.updateSensorDataBulk([d1, d2])
            call = patched_session.call_args_list
            self.assertTrue(call[0][0][0].endswith("sensordatabulk"))
            self.assertEqual(len(call[0][1]["json"]["sensordata"]), 2)
            self.assertEqual(call[0][1]["json"]["sensordata"][0]["data"],
                             [(t - 10, 2.0), (t, 2.0), (t + 10, 3.0)])
            self.assertEqual(call[0][1]["json"]["sensordata"][0]["metric"],
                             "ph")
            self.assertEqual(call[0][1]["json"]["sensordata"][0]["device_id"],
                             "1234567890")
            self.assertEqual(call[0][1]["json"]["sensordata"][1]["data"],
                             [(t, 2.0), (t + 10, 3.0)])
            self.assertEqual(call[0][1]["json"]["sensordata"][1]["metric"],
                             "temp")
            self.assertEqual(call[0][1]["json"]["sensordata"][1]["device_id"],
                             "1234567890")

    def test_sensordata(self):
        t = int(time.time())
        d1 = {
            "device_id": "1234567890",
            "metric": "ph",
            "data": [(t - 10, 2.0), (t, 2.0), (t + 10, 3.0)]
        }
        d2 = {
            "device_id": "1234567890",
            "metric": "temp",
            "data": [(t, 2.0), (t + 10, 3.0)]
        }

        sxapi = LowLevelAPI(private_endpoint=self.INTERN_ENDPOINT, public_endpoint=self.PUBLIC_ENDPOINT,
                            api_key=self.API_KEY)

        with MockPut() as patched_session:
            sxapi.insertSensorData(**d1)
            call = patched_session.call_args_list
            self.assertTrue(call[0][0][0].endswith("sensordatabulk"))
            self.assertEqual(len(call[0][1]["json"]["sensordata"]), 1)
            self.assertEqual(call[0][1]["json"]["sensordata"][0]["data"],
                             [(t - 10, 2.0), (t, 2.0), (t + 10, 3.0)])
            self.assertEqual(call[0][1]["json"]["sensordata"][0]["metric"],
                             "ph")
            self.assertEqual(call[0][1]["json"]["sensordata"][0]["device_id"],
                             "1234567890")

        with MockPut() as patched_session:
            sxapi.insertSensorDataBulk([d1, d2])
            call = patched_session.call_args_list
            self.assertTrue(call[0][0][0].endswith("sensordatabulk"))
            self.assertEqual(len(call[0][1]["json"]["sensordata"]), 2)
            self.assertEqual(call[0][1]["json"]["sensordata"][0]["data"],
                             [(t - 10, 2.0), (t, 2.0), (t + 10, 3.0)])
            self.assertEqual(call[0][1]["json"]["sensordata"][0]["metric"],
                             "ph")
            self.assertEqual(call[0][1]["json"]["sensordata"][0]["device_id"],
                             "1234567890")
            self.assertEqual(call[0][1]["json"]["sensordata"][1]["data"],
                             [(t, 2.0), (t + 10, 3.0)])
            self.assertEqual(call[0][1]["json"]["sensordata"][1]["metric"],
                             "temp")
            self.assertEqual(call[0][1]["json"]["sensordata"][1]["device_id"],
                             "1234567890")

        with MockGet() as patched_session:
            sxapi.getSensorData("1234567890", "ph",
                                t - 30 * 24 * 60 * 60, t)
            call = patched_session.call_args_list
            self.assertTrue(call[0][0][0].endswith("sensordatabulk"))
            self.assertEqual(call[0][1]["params"]["device_id"], "1234567890")
            self.assertEqual(call[0][1]["params"]["metrics"], ["ph"])

        with MockGet() as patched_session:
            sxapi.getLastSensorDataBulk("1234567890", ["ph", "temp"])
            call = patched_session.call_args_list
            self.assertTrue(call[0][0][0].endswith("lastsensordata"))
            self.assertEqual(call[0][1]["params"]["device_id"], "1234567890")
            self.assertEqual(call[0][1]["params"]["metrics"], ["ph", "temp"])

    def test_events(self):
        sxapi = LowLevelAPI(private_endpoint=self.INTERN_ENDPOINT, public_endpoint=self.PUBLIC_ENDPOINT,
                            api_key=self.API_KEY)
        with MockGet() as patched_session:
            sxapi.getLastEventTimestamps("1234567890")
            call = patched_session.call_args_list
            self.assertTrue(call[0][0][0].endswith("lasteventtimestamps"))
            self.assertEqual(call[0][1]["params"]["device_id"], "1234567890")

        with MockPut() as patched_session:
            sxapi.insertEvent("1234567890", 101, 1480773600, 6.5,
                              {"foo": "bar"})
            call = patched_session.call_args_list
            self.assertTrue(call[0][0][0].endswith("event"))
            self.assertEqual(call[0][1]["json"]["device_id"], "1234567890")
            self.assertEqual(call[0][1]["json"]["metadata"],
                             {"foo": "bar", "value": 6.5})
            self.assertEqual(call[0][1]["json"]["event_type"], 101)
            self.assertEqual(call[0][1]["json"]["level"], 10)
            self.assertEqual(call[0][1]["json"]["timestamp"], 1480773600)
            self.assertEqual(call[0][1]["json"]["disable_hooks"], 0)

        with MockPost() as patched_session:
            sxapi.updateEventMeta("1234567890", "123",
                                  {"foo": "fooz", "bar": "hurtz"})
            call = patched_session.call_args_list
            self.assertTrue(call[0][0][0].endswith("event"))
            self.assertEqual(call[0][1]["json"]["metadata"],
                             {"foo": "fooz", "bar": "hurtz"})

    def test_device(self):
        sxapi = LowLevelAPI(private_endpoint=self.INTERN_ENDPOINT, public_endpoint=self.PUBLIC_ENDPOINT,
                            api_key=self.API_KEY)
        with MockGet() as patched_session:
            sxapi.getDevice("1234567890")
            call = patched_session.call_args_list
            self.assertTrue(call[0][0][0].endswith("device"))
            self.assertEqual(call[0][1]["params"]["device_id"], "1234567890")
            self.assertEqual(call[0][1]["params"]["with_animal"], 1)
            self.assertEqual(call[0][1]["params"]["with_organisation"], 1)
            self.assertEqual(call[0][1]["params"]["with_allmeta"], 1)

        with MockPost() as patched_session:
            sxapi.setDeviceMeta("1234567890", {"hello": "world"})
            call = patched_session.call_args_list
            self.assertTrue(call[0][0][0].endswith("devicemetadata"))
            self.assertEqual(call[0][1]["json"]["device_id"], "1234567890")
            self.assertEqual(call[0][1]["json"]["metadata"],
                             {"hello": "world"})

    def test_sensorinfo(self):
        sxapi = LowLevelAPI(private_endpoint=self.INTERN_ENDPOINT, public_endpoint=self.PUBLIC_ENDPOINT,
                            api_key=self.API_KEY)
        with MockGet() as patched_session:
            sxapi.getSensorInfo("1234567890")
            call = patched_session.call_args_list
            self.assertTrue(call[0][0][0].endswith("sensorinfo"))
            self.assertEqual(call[0][1]["params"]["device_id"], "1234567890")

    def test_sensorrange(self):
        sxapi = LowLevelAPI(private_endpoint=self.INTERN_ENDPOINT, public_endpoint=self.PUBLIC_ENDPOINT,
                            api_key=self.API_KEY)
        with MockGet() as patched_session:
            sxapi.getSensorDataRange("1234567890", "act")
            call = patched_session.call_args_list
            self.assertTrue(call[0][0][0].endswith("sensordatarange"))
            self.assertEqual(call[0][1]["params"]["device_id"], "1234567890")
            self.assertEqual(call[0][1]["params"]["metric"], "act")

    def test_annotation(self):
        sxapi = LowLevelAPI(private_endpoint=self.INTERN_ENDPOINT, public_endpoint=self.PUBLIC_ENDPOINT,
                            api_key=self.API_KEY)
        with MockGet() as patched_session:
            sxapi.get_annotation_definitions()
            call = patched_session.call_args_list
            self.assertTrue(call[0][0][0].endswith("/annotation/definition"))

        with MockGet() as patched_session:
            sxapi.get_annotation_by_id("myannoid")
            call = patched_session.call_args_list
            self.assertTrue(call[0][0][0].endswith("/annotation/id"))
            self.assertEqual(call[0][1]["params"]["annotation_id"], "myannoid")

        with MockGet() as patched_session:
            sxapi.get_annotations_by_class("health", 1480773600, 1480773610)
            call = patched_session.call_args_list
            self.assertTrue(call[0][0][0].endswith("/annotation/query"))
            self.assertEqual(call[0][1]["params"]["annotation_class"], "health")
            self.assertEqual(call[0][1]["params"]["from_date"], 1480773600)
            self.assertEqual(call[0][1]["params"]["to_date"], 1480773610)
            self.assertEqual(call[0][1]["params"]["offset"], 0)

        with MockGet() as patched_session:
            sxapi.get_animal_annotations("myanimal", 1480773600, 1480773610)
            call = patched_session.call_args_list
            self.assertTrue(call[0][0][0].endswith("/annotation/query"))
            self.assertEqual(call[0][1]["params"]["animal_id"], "myanimal")
            self.assertEqual(call[0][1]["params"]["from_date"], 1480773600)
            self.assertEqual(call[0][1]["params"]["to_date"], 1480773610)
            self.assertEqual(call[0][1]["params"]["offset"], 0)

        with MockPut() as patched_session:
            sxapi.insert_animal_annotation("myanimal", 34, 35, ["health", "desease"], [{"foo": "bar"}])
            call = patched_session.call_args_list
            self.assertTrue(call[0][0][0].endswith("/annotation/animal"))
            self.assertEqual(call[0][1]["json"]["animal_id"], "myanimal")
            self.assertEqual(call[0][1]["json"]["ts"], 34)
            self.assertEqual(call[0][1]["json"]["end_ts"], 35)
            self.assertEqual(call[0][1]["json"]["classes"], ["health", "desease"])
            self.assertEqual(call[0][1]["json"]["attributes"], [{"foo": "bar"}])

        with MockGet() as patched_session:
            sxapi.get_annotations_by_organisation("my_org_id", 1480773600, 1480773610)
            call = patched_session.call_args_list
            self.assertTrue(call[0][0][0].endswith("/annotation/query"))
            self.assertEqual(call[0][1]["params"]["organisation_id"], "my_org_id")
            self.assertEqual(call[0][1]["params"]["from_date"], 1480773600)
            self.assertEqual(call[0][1]["params"]["to_date"], 1480773610)
            self.assertEqual(call[0][1]["params"]["offset"], 0)

    def test_organisations(self):
        sxapi = LowLevelAPI(private_endpoint=self.INTERN_ENDPOINT, public_endpoint=self.PUBLIC_ENDPOINT,
                            api_key=self.API_KEY)
        with MockGet() as patched_session:
            sxapi.query_organisations()
            call = patched_session.call_args_list
            self.assertEqual(call[0][0][0], "/organisation/list")
