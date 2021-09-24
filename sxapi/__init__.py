#!/usr/bin/python
# coding: utf8

import warnings

from .low import LowLevelPublicAPI, LowLevelInternAPI
from .models import User, Animal, Organisation, Annotation
from .helper import toTS

__version__ = "0.15"


warnings.warn(
    "deprecated: this package will break all APIs with version 1.x", ImportWarning
)


class API(object):
    def __init__(
        self, email=None, password=None, api_key=None, endpoint=None, tz_aware=True
    ):
        """Initialize a new API client instance."""
        self.low = LowLevelPublicAPI(
            email=email,
            password=password,
            api_key=api_key,
            endpoint=endpoint,
            tz_aware=tz_aware,
        )
        warnings.warn(
            "deprecated: this package will break all APIs with version 1.x",
            DeprecationWarning,
        )

    @property
    def status(self):
        return self.low.get_status()

    def print_stats(self):
        for p in self.low.stats():
            print(p)

    @property
    def user(self):
        return User(api=self.low, data=self.low.get_user())

    @property
    def organisations(self):
        return [
            Organisation.create_from_data(
                api=self.low, data=x, _id=x["organisation_id"]
            )
            for x in self.low.get_organisations()
        ]

    def get_annotation(self, annotation_id):
        return Annotation(api=self.low, _id=annotation_id)

    def get_animal(self, animal_id):
        return Animal(api=self.low, _id=animal_id)

    def get_organisation(self, organisation_id):
        return Organisation(api=self.low, _id=organisation_id)


class LowLevelAPI(object):
    def __init__(
        self,
        email=None,
        password=None,
        private_endpoint=None,
        api_key=None,
        public_endpoint=None,
        tz_aware=True,
    ):
        """Initialize a new API client instance."""
        self.publiclow = LowLevelPublicAPI(
            email=email,
            password=password,
            api_key=api_key,
            endpoint=public_endpoint,
            tz_aware=tz_aware,
        )
        if private_endpoint is not None and api_key is not None:
            self.privatelow = LowLevelInternAPI(
                endpoint=private_endpoint, api_key=api_key, tz_aware=tz_aware
            )
        else:
            pass
            # self.privatelow = self._privatelow
            # do something to raise warning

    @property
    def _privatelow(self):
        raise RuntimeError("internal API not accessable without endpoint and token")

    # Status Calls

    def get_public_status(self):
        return self.publiclow.get_status()

    def get_private_status(self):
        return self.privatelow.get_status()

    # Calls to Public API

    # High Level

    def get_animal_object(self, animal_id):
        return Animal(api=self.publiclow, _id=animal_id)

    def get_organisation_object(self, organisation_id):
        return Organisation(api=self.publiclow, _id=organisation_id)

    # Low Level

    def get_organisation_animal_ids(self, organisation_id):
        return self.publiclow.get_organisation_animal_ids(organisation_id)

    def get_animal_by_id(self, animal_id):
        return self.publiclow.get_animal_by_id(animal_id)

    def get_device_by_id(self, device_id):
        return self.publiclow.get_device_by_id(device_id)

    def get_device_uploads(self, from_ts, to_ts, device_id):
        return self.publiclow.get_device_uploads(from_ts, to_ts, device_id)

    def get_organisation_by_id(self, organisation_id):
        return self.publiclow.get_organisation_by_id(organisation_id)

    def get_device_sensordata(self, device_id, metric, from_date, to_date):
        f = toTS(from_date)
        t = toTS(to_date)
        return self.publiclow.get_device_sensordata(device_id, metric, f, t)

    def get_animal_sensordata(self, animal_id, metric, from_date, to_date):
        f = toTS(from_date)
        t = toTS(to_date)
        return self.publiclow.get_animal_sensordata(animal_id, metric, f, t)

    def get_animal_events(self, animal_id, from_date=None, to_date=None):
        f = None
        if from_date is not None:
            f = toTS(from_date)
        t = None
        if to_date is not None:
            t = toTS(to_date)
        return self.publiclow.get_animal_events(animal_id, f, t)

    def get_device_events(self, device_id, from_date=None, to_date=None):
        f = None
        if from_date is not None:
            f = toTS(from_date)
        t = None
        if to_date is not None:
            t = toTS(to_date)
        return self.publiclow.get_device_events(device_id, f, t)

    def get_events_by_organisation(
        self, organisation_id, from_date, to_date, categories=None
    ):
        f = toTS(from_date)
        t = toTS(to_date)
        return self.publiclow.get_events_by_organisation(
            organisation_id, f, t, categories=categories
        )

    def get_animals_by_organisation(self, organisation_id):
        return self.privatelow.get_animals_by_organisation(organisation_id)

    # Deprecated Calls to Public (old name)

    def getAnimalIdsForOrganisation(self, organisation_id):
        raise DeprecationWarning("use get_organisation_animal_ids")

    def getAnimalsForOrganisation(self, organisation_id):
        raise DeprecationWarning("use get_animal_by_id")

    def getDeviceEventList(self, device_id, from_date, to_date):
        raise DeprecationWarning("use get_device_events")

    def getAnimalEventList(self, animal_id, from_date, to_date):
        raise DeprecationWarning("use get_animal_events")

    # Old internal calls

    def updateSensorData(self, device_id, metric, data):
        return self.privatelow.updateSensorData(device_id, metric, data)

    def updateSensorDataBulk(self, sensordata):
        return self.privatelow.updateSensorDataBulk(sensordata)

    def insertSensorData(self, device_id, metric, data):
        return self.privatelow.insertSensorData(device_id, metric, data)

    def insertSensorDataBulk(self, sensordata):
        return self.privatelow.insertSensorDataBulk(sensordata)

    def getSensorData(self, device_id, metric, from_date, to_date):
        return self.privatelow.getSensorData(device_id, metric, from_date, to_date)

    def getSensorDataRange(self, device_id, metric):
        return self.privatelow.getSensorDataRange(device_id, metric)

    def getSensorDataBulk(self, device_id, metrics, from_date, to_date):
        return self.privatelow.getSensorDataBulk(device_id, metrics, from_date, to_date)

    def getLastSensorData(self, device_id, metric):
        return self.privatelow.getLastSensorData(device_id, metric)

    def getLastSensorDataBulk(self, device_id, metrics):
        return self.privatelow.getLastSensorDataBulk(device_id, metrics)

    def insertEvent(
        self,
        device_id,
        event_type,
        timestamp,
        value,
        metadata,
        level=10,
        disable_notifications=False,
    ):
        return self.privatelow.insertEvent(
            device_id,
            event_type,
            timestamp,
            value,
            metadata,
            level=level,
            disable_notifications=disable_notifications,
        )

    def updateEventMeta(self, device_id, _id, event_meta):
        return self.privatelow.updateEventMeta(device_id, _id, event_meta)

    def getLastEventTimestamps(self, device_id):
        return self.privatelow.getLastEventTimestamps(device_id)

    def setDeviceMeta(self, device_id, metadata):
        return self.privatelow.setDeviceMeta(device_id, metadata)

    def getSensorInfo(self, device_id):
        return self.privatelow.getSensorInfo(device_id)

    def deleteEvent(self, event_id):
        return self.privatelow.deleteEvent(event_id)

    def getDevice(
        self, device_id, with_animal=True, with_organisation=True, with_allmeta=True
    ):
        return self.privatelow.getDevice(
            device_id,
            with_animal=with_animal,
            with_organisation=with_organisation,
            with_allmeta=with_allmeta,
        )

    def get_interal_organisation_by_id(self, organisation_id):
        return self.privatelow.getOrganisation(organisation_id)

    def getOrganisation(self, organisation_id):
        return self.privatelow.getOrganisation(organisation_id)

    def getAnimal(self, animal_id):
        warnings.warn(
            "getAnimal (internal) is deprecated. use get_animal_by_id",
            DeprecationWarning,
        )
        return self.privatelow.getAnimal(animal_id)

    def getOrganisationList(self):
        warnings.warn(
            "getOrganisationList (internal) is deprecated. use query_organisations",
            DeprecationWarning,
        )
        return self.privatelow.getOrganisationList()

    def get_devices_seen(self, device_id, hours_back=24, return_sum=True, to_ts=None):
        return self.privatelow.get_devices_seen(
            device_id, hours_back, return_sum, to_ts
        )

    def getNodeInfos(self, device_id, from_date, to_date):
        return self.privatelow.getNodeInfos(device_id, from_date, to_date)

    def getUploads(self, device_id, from_date, to_date):
        return self.privatelow.getUploads(device_id, from_date, to_date)

    def lastProductionDevices(self, device_id=None, skip=0, limit=10):
        return self.privatelow.lastProductionDevices(device_id, skip, limit)

    def searchDevices(self, search_string):
        return self.privatelow.search_devices(search_string)

    # Annotation Calls

    def get_annotation_by_id(self, annotation_id):
        return self.publiclow.get_annotation_by_id(annotation_id)

    def get_annotation_definitions(self):
        return self.publiclow.get_annotation_definition()

    def get_annotations_by_class(self, annotation_class, from_date, to_date):
        return self.publiclow.get_annotations_by_class(
            annotation_class, from_date, to_date
        )

    def get_annotations_by_organisation(self, organisation_id, from_date, to_date):
        return self.publiclow.get_annotations_by_organisation(
            organisation_id, from_date, to_date
        )

    def get_animal_annotations(self, animal_id, from_date, to_date):
        return self.publiclow.get_animal_annotations(animal_id, from_date, to_date)

    def insert_animal_annotation(self, animal_id, ts, end_ts, classes, attributes):
        return self.publiclow.insert_animal_annotation(
            animal_id=animal_id,
            ts=ts,
            end_ts=end_ts,
            classes=classes,
            attributes=attributes,
        )

    def update_annotation(
        self, annotation_id, ts=None, end_ts=None, classes=None, attributes=None
    ):
        return self.publiclow.update_annotation(
            annotation_id, ts, end_ts, classes, attributes
        )

    # Organisation Calls

    def query_organisations(
        self, name_search_string=None, partner_id=None, active_test_package=None
    ):
        return self.privatelow.query_organisations(
            name_search_string, partner_id, active_test_package
        )

    def update_organisation_partner(self, organisation_id, partner_id):
        return self.privatelow.update_organisation_partner(organisation_id, partner_id)

    def move_device(self, device_id, organisation_id):
        return self.privatelow.move_device(device_id, organisation_id)

    def deactivate_device(self, device_id, activation_code):
        return self.privatelow.deactivate_device(device_id, activation_code)

    def move_animal(self, animal_id, organisation_id):
        return self.privatelow.move_animal(animal_id, organisation_id)

    # User Calls

    def get_user_by_id(self, user_id):
        return self.privatelow.getUser(user_id)

    def query_users(self, email_search_string=None):
        return self.privatelow.query_users(email_search_string=email_search_string)

    def get_hidden_shares(self, user_id):
        return self.privatelow.get_hidden_shares(user_id)

    def delete_hidden_share(self, share_id):
        return self.privatelow.delete_hidden_share(share_id)

    def create_hidden_share(self, organisation_id, user_id):
        return self.privatelow.create_hidden_share(organisation_id, user_id)

    def activate_user(self, email):
        return self.privatelow.activate_user(email)

    # Testset Calls

    def insert_testset(self, name, meta_data, annotation_ids):
        return self.publiclow.insert_testset(name, meta_data, annotation_ids)

    def update_testset(self, testset_id, annotation_ids):
        return self.publiclow.update_testset(testset_id, annotation_ids)

    def get_testset_by_id(self, testset_id):
        return self.publiclow.get_testset_by_id(testset_id)

    def get_testset_by_name(self, name):
        return self.publiclow.get_testset_by_name(name)

    def getGroupSensorDataBulk(self, group_id, metrics, from_date, to_date):
        return self.privatelow.getGroupSensorDataBulk(
            group_id, metrics, from_date, to_date
        )

    def insertGroupSensorDataBulk(self, sensordata):
        return self.privatelow.insertGroupSensorDataBulk(sensordata)

    # Other Stuff

    def set_device_defect(self, device_id, defect_date, defect_info):
        return self.privatelow.set_device_defect(device_id, defect_date, defect_info)

    def update_organisation_infos(
        self,
        organisation_id,
        partner_id=None,
        service_model_mode=None,
        country_code=None,
    ):
        return self.privatelow.update_organisation_infos(
            organisation_id,
            partner_id=partner_id,
            service_model_mode=service_model_mode,
            country_code=country_code,
        )

    def activate_test_package(self, organisation_id, end_date):
        return self.privatelow.activate_test_package(organisation_id, end_date)

    def query_accounts(self, name_search_string=None, partner_id=None):
        return self.privatelow.query_accounts(
            name_search_string=name_search_string, partner_id=partner_id
        )

    def get_account(self, account_id):
        return self.privatelow.get_account(account_id)

    def get_partner_list(self):
        return self.privatelow.get_partner_list()

    def create_billing_report(self, partner_id):
        assert False
        return self.privatelow.create_billing_report(partner_id)

    def update_account_infos(
        self,
        account_id,
        partner_id=None,
        account_nr=None,
        owner_id=None,
        billing_emails=None,
    ):
        return self.privatelow.update_account_infos(
            account_id,
            partner_id=partner_id,
            account_nr=account_nr,
            owner_id=owner_id,
            billing_emails=billing_emails,
        )
