#!/usr/bin/python
# coding: utf8


import time
import logging
import requests
import re
import pendulum

from requests.exceptions import HTTPError

from .models import HDict
from .helper import splitTimeRange, Memoize


PUBLIC_API = "https://api.smaxtec.com/api/v1"


class Req(object):
    def __init__(self, url, status, start, end=None):
        self.url = url
        self.start = start
        self.status = status
        if end is None:
            self.end = time.time()
        else:
            self.end = end

    @property
    def timer(self):
        return self.end - self.start


class BaseAPI(object):
    def __init__(self, base_url, email=None, password=None, api_key=None, tz_aware=True):
        """Initialize a new base low level API client instance.
        """
        self.api_base_url = base_url.rstrip("/")
        self.email = email
        self.password = password
        self.api_key = api_key

        self._session_key = None
        self._session_expiration = time.time() - 1
        self._session = None
        self.counter = 0
        self.requests = []
        self.tz_aware = tz_aware

    @property
    def session(self):
        """Geneate a new HTTP session on the fly and login.
        """
        if not self._session:
            self._session = requests.Session()
        # check login
        if not self._login():
            raise ValueError("invalid login information")
        return self._session

    def track_request(self, url, status, start):
        self.counter += 1
        self.requests.append(Req(url, status, start))
        if len(self.requests) > 100:
            self.requests.pop(0)

    def stats(self):
        out = []
        out.append("{} Requests".format(self.counter))
        for r in self.requests:
            out.append("{} in {} seconds".format(r.url, r.timer))
        return out

    def to_url(self, path, version_modifier=None):
        url = "{}{}".format(self.api_base_url, path)
        if version_modifier is not None:
            url = re.sub(r'\/[vV][0-9]+\/',
                         "/{}/".format(version_modifier), url)
        return url

    def _login(self):
        """Login to the api with api key or the given credentials.
        """
        # check expiration
        diff = time.time() - self._session_expiration
        if diff < 0.0:
            return True
        # try to use api key
        if self.api_key:
            self._session_key = self.api_key
            self._session.headers.update(
                {"Authorization": "Bearer {}".format(self._session_key)})
            self._session_expiration = time.time() + 365 * 24 * 60 * 60
            return True
        # login with credentials
        if self.email is None or self.password is None:
            raise ValueError("email and password are needed for API access")
        params = {"email": self.email, "password": self.password}
        res = self._session.get(self.to_url("/user/get_token"), params=params)
        if res.status_code == requests.codes.ok:
            pass
        elif res.status_code == 401 or res.status_code == 409 or res.status_code == 422:
            raise ValueError("invalid login credentials")
        else:
            res.raise_for_status()
        self._session_key = res.json()["token"]
        self._session.headers.update(
            {"Authorization": "Bearer {}".format(self._session_key)})
        self._session_expiration = time.time() + 23 * 60 * 60
        return True

    def get(self, path, *args, **kwargs):
        version = kwargs.pop("version", None)
        url = self.to_url(path, version)
        start = time.time()
        r = self.session.get(url, *args, **kwargs)
        self.track_request(url, r.status_code, start)
        if 400 <= r.status_code < 500:
            try:
                msg = r.json().get("message", "unknown")
            except Exception:
                msg = "unknown"
            raise HTTPError("{} Error: {}".format(
                r.status_code, msg))
        r.raise_for_status()
        return r.json()

    def post(self, path, *args, **kwargs):
        version = kwargs.pop("version", None)
        url = self.to_url(path, version)
        start = time.time()
        r = self.session.post(url, *args, allow_redirects=False, **kwargs)
        self.track_request(url, r.status_code, start)
        if r.status_code == 301:
            raise HTTPError("301 redirect for POST")
        if 400 <= r.status_code < 500:
            try:
                msg = r.json().get("message", "unknown")
            except Exception:
                msg = "unknown"
            raise HTTPError("{} Error: {}".format(
                r.status_code, msg))
        r.raise_for_status()
        return r.json()

    def put(self, path, *args, **kwargs):
        version = kwargs.pop("version", None)
        url = self.to_url(path, version)
        start = time.time()
        r = self.session.put(url, *args, allow_redirects=False, **kwargs)
        self.track_request(url, r.status_code, start)
        if r.status_code == 301:
            raise HTTPError("301 redirect for PUT")
        if 400 <= r.status_code < 500:
            try:
                msg = r.json().get("message", "unknown")
            except Exception:
                msg = "unknown"
            raise HTTPError("{} Error: {}".format(
                r.status_code, msg))
        r.raise_for_status()
        return r.json()

    def delete(self, path, *args, **kwargs):
        version = kwargs.pop("version", None)
        url = self.to_url(path, version)
        start = time.time()
        r = self.session.delete(url, *args, **kwargs)
        self.track_request(url, r.status_code, start)
        if 400 <= r.status_code < 500:
            try:
                msg = r.json().get("message", "unknown")
            except Exception:
                msg = "unknown"
            raise HTTPError("{} Error: {}".format(
                r.status_code, msg))
        r.raise_for_status()
        return r.json()


class LowLevelPublicAPI(BaseAPI):
    def __init__(self, email=None, password=None, api_key=None, endpoint=None, tz_aware=True):
        """Initialize a new low level API client instance.
        """
        ep = endpoint or PUBLIC_API
        super(LowLevelPublicAPI, self).__init__(ep, email=email,
                                                password=password, api_key=api_key, tz_aware=tz_aware)

    def get_status(self):
        return self.get("/service/status")

    def get_organisations(self):
        if self.api_key:
            return []
        return self.get("/organisation")

    def get_user(self):
        if self.api_key:
            return {"type": "apikey"}
        u = self.get("/user")
        u["type"] = "email"
        return u

    def get_organisation_animal_ids(self, organisation_id):
        params = HDict({"organisation_id": organisation_id})
        animal_ids = self.get("/animal/ids_by_organisation", params=params)
        return [x["_id"] for x in animal_ids]

    def get_animal_by_id(self, animal_id):
        params = HDict({"animal_id": animal_id})
        return self.get("/animal/by_id", params=params)

    def get_device_by_id(self, device_id):
        params = HDict({"device_id": device_id})
        return self.get("/device/by_id", params=params)

    def get_organisation_by_id(self, organisation_id):
        params = HDict({"organisation_id": organisation_id})
        return self.get("/organisation/by_id", params=params)

    def get_device_sensordata(self, device_id, metric, from_date, to_date):
        data = []
        for f, t in splitTimeRange(from_date, to_date, 100):
            data += self._get_device_sensordata(device_id,
                                                metric, f, t)["data"]
        return data

    def _get_device_sensordata(self, device_id, metric, from_date, to_date):
        params = HDict({"device_id": device_id, "metric": metric,
                        "from_date": from_date, "to_date": to_date})
        return self.get("/data/query", params=params)

    def get_animal_sensordata(self, animal_id, metric, from_date, to_date):
        data = []
        for f, t in splitTimeRange(from_date, to_date, 100):
            data += self._get_animal_sensordata(animal_id,
                                                metric, f, t)["data"]
        return data

    def _get_animal_sensordata(self, animal_id, metric, from_date, to_date):
        params = HDict({"animal_id": animal_id, "metric": metric,
                        "from_date": from_date, "to_date": to_date})
        return self.get("/data/query", params=params)

    def get_animal_events(self, animal_id, from_date=None, to_date=None,
                          limit=100, offset=0):
        if from_date:
            from_date = int(from_date)
        if to_date:
            to_date = int(to_date)

        params = HDict({"animal_id": animal_id, "limit": limit,
                        "offset": offset, "from_date": from_date,
                        "to_date": to_date})
        all_events = []
        while True:
            events = self.get("/event/query", params=params)
            all_events += events["data"]
            if len(events["data"]) < params["limit"]:
                break
            else:
                params["offset"] = events["pagination"]["next_offset"]
        return all_events

    def get_device_events(self, device_id, from_date=None, to_date=None):
        if from_date:
            from_date = int(from_date)
        if to_date:
            to_date = int(to_date)

        params = HDict({"device_id": device_id, "limit": 100, "offset": 0,
                        "from_date": from_date, "to_date": to_date})
        all_events = []
        while True:
            events = self.get("/event/query", params=params)
            all_events += events["data"]
            if len(events["data"]) < params["limit"]:
                break
            else:
                params["offset"] = events["pagination"]["next_offset"]
        return all_events

    def get_events_by_organisation(self, organisation_id, from_date, to_date, categories=None):
        params = HDict({"organisation_id": organisation_id, "offset": 0, "limit": 100,
                        "from_date": int(from_date), "to_date": int(to_date),
                        "categories": categories})
        all_res = []
        while True:
            res = self.get("/event/by_organisation", params=params)
            all_res += res["data"]
            if len(res["data"]) < params["limit"]:
                break
            else:
                params["offset"] = res["pagination"]["next_offset"]
        return all_res

    def get_annotation_by_id(self, annotation_id):
        params = HDict({"annotation_id": annotation_id})
        return self.get("/annotation/id", params=params)

    def get_animal_annotations(self, animal_id, from_date, to_date):
        params = HDict({"to_date": to_date, "from_date": from_date, "limit": 100,
                        "offset": 0, "animal_id": animal_id})
        all_annotations = []
        while True:
            annotations = self.get("/annotation/query", params=params)
            all_annotations += annotations["data"]
            if len(annotations["data"]) < params["limit"]:
                break
            else:
                params["offset"] = annotations["pagination"]["next_offset"]
        return all_annotations

    def get_annotations_by_class(self, annotation_class, from_date, to_date):
        params = HDict({"to_date": to_date, "from_date": from_date, "limit": 100,
                        "offset": 0, "annotation_class": annotation_class})
        all_annotations = []
        while True:
            annotations = self.get("/annotation/query", params=params)
            all_annotations += annotations["data"]
            if len(annotations["data"]) < params["limit"]:
                break
            else:
                params["offset"] = annotations["pagination"]["next_offset"]
        return all_annotations

    def get_annotations_by_organisation(self, organisation_id, from_date, to_date):
        params = HDict({"to_date": to_date, "from_date": from_date, "limit": 100,
                        "offset": 0, "organisation_id": organisation_id})
        all_annotations = []
        while True:
            annotations = self.get("/annotation/query", params=params)
            all_annotations += annotations["data"]
            if len(annotations["data"]) < params["limit"]:
                break
            else:
                params["offset"] = annotations["pagination"]["next_offset"]
        return all_annotations

    def get_annotation_definition(self):
        return self.get("/annotation/definition")

    def insert_animal_annotation(self, animal_id, ts, end_ts, classes=None, attributes=None):
        p = HDict({"animal_id": animal_id, "ts": ts,
                   "end_ts": end_ts, "classes": classes,
                   "attributes": attributes})
        res = self.put("/annotation/animal", json=p)
        return res

    def update_annotation(self, annotation_id, ts=None, end_ts=None, classes=None, attributes=None):
        p = HDict({"annotation_id": annotation_id, "ts": ts,
                   "end_ts": end_ts, "classes": classes,
                   "attributes": attributes})
        if ts is not None:
            p["ts"] = ts
        if end_ts is not None:
            p["end_ts"] = end_ts
        if classes is not None:
            p["classes"] = classes
        if attributes is not None:
            p["attributes"] = attributes
        res = self.post("/annotation/id", json=p)
        return res

    def insert_testset(self, name, meta_data, annotation_ids):
        p = HDict({"name": name, "meta_data": meta_data,
                   "annotation_ids": annotation_ids})
        res = self.put("/annotation/testset", json=p, timeout=25)
        return res

    def update_testset(self, testset_id, annotation_ids):
        p = HDict({"testset_id": testset_id, "annotation_ids": annotation_ids})
        res = self.post("/annotation/testset", json=p)
        return res

    def get_testset_by_id(self, testset_id):
        params = HDict({"testset_id": testset_id})
        res = self.get("/annotation/testset", params=params)
        return res

    def get_testset_by_name(self, name):
        params = HDict({"name": name})
        res = self.get("/annotation/testset/by_name", params=params)
        return res

    @Memoize
    def get_timezone_for_organisation_id(self, organisation_id):
        res = self.get_organisation_by_id(organisation_id)
        if res:
            return res.get("timezone", None)
        return None

    def get_file_state(self, file_id):
        return self.get("/user/files/{}/state".format(file_id))

    def get_download_link(self, file_id):
        return self.to_url("/user/files/{}/download".format(file_id))


class LowLevelInternAPI(BaseAPI):
    def __init__(self, endpoint, api_key=None, tz_aware=True):
        """Initialize a new low level intern API client instance.
        """
        if not endpoint:
            raise ValueError("Endpoint needed for low level API")
        super(LowLevelInternAPI, self).__init__(
            endpoint, api_key=api_key, tz_aware=tz_aware)

    def get_status(self):
        return self._api_status()

    def _api_status(self):
        res = self.get("/", params={"foo": "bar"})
        return res

    def healthy(self):
        try:
            assert(self._api_status())
        except Exception as e:
            logging.error("Status Not Ok: %s", e)
            return False
        else:
            return True

    def insertSensorData(self, device_id, metric, data):
        d = [{"device_id": device_id, "metric": metric,
              "data": list(data)}]
        return self.insertSensorDataBulk(d)[0]

    def insertSensorDataBulk(self, sensordata):
        data = HDict({"sensordata": list(sensordata)})
        for s in sensordata:
            d = s["data"]
            for point in d:
                if not isinstance(point[0], (int, float)):
                    raise ValueError("Invalid TS Point: %s of metric %s",
                                     (point, s["metric"]))
                if not isinstance(point[1], (int, float)):
                    raise ValueError("Invalid VALUE Point: %s of metric %s",
                                     (point, s["metric"]))
        res = self.put("/sensordatabulk", json=data, timeout=25)
        return res

    def updateSensorData(self, device_id, metric, data):
        d = [{"device_id": device_id, "metric": metric,
              "data": list(data)}]
        return self.updateSensorDataBulk(d)[0]

    def updateSensorDataBulk(self, sensordata):
        data = HDict({"sensordata": list(sensordata)})
        for s in sensordata:
            d = s["data"]
            for point in d:
                if not isinstance(point[0], (int, float)):
                    raise ValueError("Invalid TS Point: %s", point)
                if not isinstance(point[1], (int, float)):
                    raise ValueError("Invalid VALUE Point: %s", point)
        res = self.post("/sensordatabulk", json=data, timeout=25)
        return res

    def getSensorData(self, device_id, metric, from_date, to_date):
        return self.getSensorDataBulk(device_id, [metric],
                                      from_date, to_date)[0]

    def getSensorDataRange(self, device_id, metric):
        params = HDict({"device_id": device_id, "metric": metric})
        res = self.get("/sensordatarange", params=params)
        return res

    def getSensorDataBulk(self, device_id, metrics, from_date, to_date):
        params = HDict({"device_id": device_id, "metrics": list(metrics),
                        "from_date": from_date, "to_date": to_date})
        res = self.get("/sensordatabulk", params=params, timeout=15)
        return res

    def getLastSensorData(self, device_id, metric):
        return self.getLastSensorDataBulk(device_id, [metric])[0]

    def getLastSensorDataBulk(self, device_id, metrics):
        params = HDict({"device_id": device_id, "metrics": list(metrics)})
        res = self.get("/lastsensordata", params=params)
        return res

    def insertEvent(self, device_id, event_type, timestamp, value,
                    metadata, level=10, disable_notifications=False):
        hooks = 1 if disable_notifications else 0
        metadata["value"] = value
        p = HDict({"device_id": device_id, "metadata": dict(metadata),
                   "event_type": event_type, "level": level,
                   "timestamp": timestamp, "disable_hooks": hooks})
        res = self.put("/event", json=p)
        return res

    def updateEventMeta(self, device_id, _id, event_meta):
        p = HDict({"event_id": _id, "metadata": event_meta})
        res = self.post("/event", json=p)
        return res

    def getLastEventTimestamps(self, device_id):
        p = HDict({"device_id": device_id})
        res = self.get("/lasteventtimestamps", params=p)
        return res

    def setDeviceMeta(self, device_id, metadata):
        p = HDict({"device_id": device_id, "metadata": dict(metadata),
                   "namespace": "anthill"})
        res = self.post("/devicemetadata", json=p)
        return res

    def getSensorInfo(self, device_id):
        p = HDict({"device_id": device_id})
        res = self.get("/sensorinfo", params=p)
        return res

    def deleteEvent(self, event_id):
        p = HDict({"event_id": event_id})
        res = self.delete("/event", params=p)
        return res

    def getDevice(self, device_id, with_animal=True, with_organisation=True,
                  with_allmeta=True):
        data = HDict({"device_id": device_id,
                      "with_animal": 1 if with_animal else 0,
                      "with_organisation": 1 if with_organisation else 0,
                      "with_allmeta": 1 if with_allmeta else 0})
        res = self.get("/device", params=data)
        return res

    def getOrganisation(self, organisation_id):
        p = HDict({"organisation_id": organisation_id})
        res = self.get("/organisation/by_id", params=p, version="v1")
        return res

    def getUser(self, user_id):
        p = HDict({"user_id": user_id})
        res = self.get("/user/by_id", params=p, version="v1")
        return res

    def query_organisations(self, name_search_string=None, partner_id=None,
                            active_test_package=None):
        params = HDict({"name_search_string": name_search_string, "limit": 100,
                        "offset": 0, "partner_id": partner_id,
                        "active_test_package": active_test_package})
        all_res = []
        while True:
            res = self.get("/organisation/list", params=params, version="v1")
            all_res += res["data"]
            if len(res["data"]) < params["limit"]:
                break
            else:
                params["offset"] = res["pagination"]["next_offset"]
        return all_res

    def query_accounts(self, name_search_string=None, partner_id=None):
        params = HDict({"name_search_string": name_search_string, "limit": 100,
                        "offset": 0, "partner_id": partner_id})
        all_res = []
        while True:
            res = self.get("/account/list", params=params, version="v1")
            all_res += res["data"]
            if len(res["data"]) < params["limit"]:
                break
            else:
                params["offset"] = res["pagination"]["next_offset"]
        return all_res

    def get_account(self, account_id):
        res = self.get("/account/{}".format(account_id), version="v1")
        return res

    def get_partner_list(self):
        res = self.get("/account/partner_list", version="v1")
        return res

    def create_billing_report(self, partner_id):
        res = self.get("/account/{}/billing_report".format(partner_id), version="v1")
        return res

    def update_account_infos(self, account_id, partner_id=None,
                             account_nr=None, owner_id=None,
                             billing_emails=None):
        p = HDict({"partner_id": partner_id,
                   "account_nr": account_nr,
                   "owner_id": owner_id,
                   "billing_emails": billing_emails})
        res = self.put("/account/{}/internal_information".format(account_id),
                       json=p, version="v1")
        return res

    def getAnimal(self, animal_id):
        p = HDict({"animal_id": animal_id})
        res = self.get("/animal", params=p)
        return res

    def getLastUnconfirmedLactDate(self, lactation_id):
        p = HDict({"lactation_id": lactation_id})
        res = self.get("/animal/lactation_history_confirmed", version="v1", params=p)
        return res

    def update_organisation_partner(self, organisation_id, partner_id):
        p = HDict({"organisation_id": organisation_id,
                   "partner_id": partner_id})
        res = self.post("/organisation/partner_id", json=p, version="v1")
        return res

    def update_organisation_infos(self, organisation_id, partner_id=None,
                                  service_model_mode=None, country_code=None):
        p = HDict({"service_model_mode": service_model_mode,
                   "partner_id": partner_id,
                   "country_code": country_code})
        if country_code is not None:
            raise RuntimeError("country_code not supported")
        res = self.put("/organisation/{}/internal_information".format(organisation_id),
                       json=p, version="v1")
        return res

    def activate_test_package(self, organisation_id, end_date):
        p = HDict({"end_date": end_date.isoformat()})
        res = self.put("/organisation/{}/activate_test_package".format(organisation_id),
                       json=p, version="v1")
        return res

    def get_devices_seen(self, device_id, hours_back=24, return_sum=True, to_ts=None):
        p = HDict({"device_id": device_id, "hours_back": int(hours_back)})
        if return_sum:
            p["return_sum"] = 1
        else:
            p["return_sum"] = 0
        if to_ts:
            p["to_ts"] = int(to_ts)
        res = self.get("/devicesonline", params=p)
        return res

    def getNodeInfos(self, device_id, from_date, to_date):
        p = HDict({"device_id": device_id, "from_date": int(
            from_date), "to_date": int(to_date)})
        res = self.get("/nodeinfobulk", params=p)
        return res

    def getUploads(self, device_id, from_date, to_date):
        p = HDict({"device_id": device_id, "from_date": int(
            from_date), "to_date": int(to_date)})
        res = self.get("/anthilluploadbulk", params=p)
        return res

    def lastProductionDevices(self, device_id=None, skip=0, limit=10):
        p = HDict({"skip": int(skip), "limit": int(limit)})
        if device_id:
            p["device_id"] = device_id
        res = self.get("/productionevents", params=p)
        return res

    def query_users(self, email_search_string=None):
        params = HDict({"email_search_string": email_search_string, "limit": 100,
                        "offset": 0})
        all_res = []
        while True:
            res = self.get("/user/list", params=params, version="v1")
            all_res += res["data"]
            if len(res["data"]) < params["limit"]:
                break
            else:
                params["offset"] = res["pagination"]["next_offset"]
        return all_res

    def get_hidden_shares(self, user_id):
        params = HDict({"user_id": user_id})
        res = self.get("/user/hidden_shares_by_user",
                       params=params, version="v1")
        return res

    def delete_hidden_share(self, share_id):
        params = HDict({"share_id": share_id})
        res = self.delete("/user/hidden_share", params=params, version="v1")
        return res

    def create_hidden_share(self, organisation_id, user_id):
        params = HDict({"organisation_id": organisation_id,
                        "user_id": user_id})
        res = self.put("/user/hidden_share", json=params, version="v1")
        return res

    def activate_user(self, email):
        p = HDict({"user_email": email})
        res = self.put("/user/activate", json=p, version="v1")
        return res

    def search_devices(self, search_string):
        p = HDict({"search_string": search_string})
        res = self.get("/devicesearch", params=p)
        return res

    def get_device_uploads(self, from_ts, to_ts, device_id):
        params = HDict({
            "device_id": device_id,
            "from_date": from_ts,
            "to_date": to_ts
        })
        return self.get("/anthilluploadbulk", params=params)

    def get_animals_by_organisation(self, organisation_id):
        p = HDict({"organisation_id": organisation_id})
        res = self.get("/animallist", params=p)
        return res

    def move_device(self, device_id, organisation_id):
        p = HDict({"organisation_id": organisation_id, "device_id": device_id})
        res = self.post("/organisation/move_device", json=p, version="v1")
        return res

    def deactivate_device(self, device_id, activation_code):
        p = HDict({"device_id": device_id, "activation_code": activation_code})
        res = self.post("/organisation/deactivate_device", json=p, version="v1")
        return res

    def move_animal(self, animal_id, organisation_id):
        p = HDict({"animal_id": animal_id, "organisation_id": organisation_id})
        res = self.post("/organisation/move_animal", json=p, version="v1")
        return res

    def set_device_defect(self, device_id, defect_date, defect_info):
        p = HDict({"defect_date": defect_date.isoformat(),
                   "defect_info": defect_info})
        res = self.put("/devices/{}/defect".format(device_id),
                       json=p, version="v1")
        return res

    def getGroupSensorDataBulk(self, group_id, metrics, from_date, to_date):
        params = HDict({"group_id": group_id, "metrics": list(metrics),
                        "from_date": from_date, "to_date": to_date})
        res = self.get("/groupsensordatabulk", params=params, timeout=15)
        return res

    def insertGroupSensorDataBulk(self, sensordata):
        data = HDict({"sensordata": list(sensordata)})
        for s in sensordata:
            d = s["data"]
            for point in d:
                if not isinstance(point[0], (int, float)):
                    raise ValueError("Invalid TS Point: %s of metric %s",
                                     (point, s["metric"]))
                if not isinstance(point[1], (int, float)):
                    raise ValueError("Invalid VALUE Point: %s of metric %s",
                                     (point, s["metric"]))
        res = self.put("/groupsensordatabulk", json=data, timeout=25)
        return res


class LowLevelInternAPIV2(BaseAPI):
    def __init__(self, endpoint, api_key=None, tz_aware=True):
        """Initialize a new low level intern API client instance.
        """
        if not endpoint:
            raise ValueError("Endpoint needed for low level API")
        super().__init__(
            endpoint, api_key=api_key, tz_aware=tz_aware)

    def create_device_update(self, name, update_type, update_content,
                             information):
        data = {
            "name": name,
            "update_type": update_type,
            "update_content": update_content,
            "information": information,
            "create_ts": pendulum.now().isoformat()
        }
        return self.post("/devices/device_updates", json=data, timeout=25)

    def schedule_device_update(self, device_id, device_update_id):
        data = {"device_update_id": device_update_id}
        return self.post(f"/devices/{device_id}/events/update_schedule", json=data, timeout=25)
