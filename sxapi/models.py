#!/usr/bin/python
# coding: utf8

import pendulum
import datetime
import math

try:
    import pandas as pd
except ImportError:
    pd = None
try:
    import numpy as np
except ImportError:
    np = None


from .helper import fromTS, toTS


class HDict(dict):
    def __hash__(self):
        return hash(frozenset(self.items()))


class APIObject(object):
    def __init__(self, api, _id):
        self.api = api
        self._id = _id
        self._data = None
        self._timezone = None
        self._tz_aware = self.api.tz_aware

    def load(self, data):
        self._data = data

    @property
    def timezone(self):
        return self._timezone

    @classmethod
    def create_from_data(cls, api, data, _id=None, timezone=None):
        if _id is None:
            _id = data["_id"]
        c = cls(api=api, _id=_id)
        if timezone is not None:
            c._timezone = timezone
        c.load(data)
        return c

    def fromTS(self, ts):
        return fromTS(ts, self.timezone, self._tz_aware)

    def toTS(self, dt):
        return toTS(dt)

    def get_data(self):
        raise NotImplementedError("reload not implemented")

    @property
    def data(self):
        if not self._data:
            self._data = self.get_data()
        return self._data

    def __str__(self):
        return "<{}(_id={})>".format(self.__class__.__name__, getattr(self, "_id", "unknown"))

    def __repr__(self):
        return "<{}(_id={})>".format(self.__class__.__name__, getattr(self, "_id", "unknown"))


class DataMixin(object):
    DEFAULT_DAYS_BACK = 30

    def get_measurements(self, metric, from_date=None, to_date=None, days_back=None):
        if days_back is None:
            days_back = self.DEFAULT_DAYS_BACK

        if from_date is None or to_date is None:
            my_to = datetime.datetime.utcnow() + datetime.timedelta(days=1)
            my_from = datetime.datetime.utcnow() - datetime.timedelta(days=days_back)
        else:
            my_to = to_date
            my_from = from_date

        return Sensordata(api=self.api, parent=self, metric=metric,
                          from_date=my_from, to_date=my_to)

    def get_frame(self, metrics, from_date=None, to_date=None, days_back=None):
        if days_back is None:
            days_back = self.DEFAULT_DAYS_BACK

        if from_date is None or to_date is None:
            my_to = datetime.datetime.utcnow() + datetime.timedelta(days=1)
            my_from = datetime.datetime.utcnow() - datetime.timedelta(days=days_back)
        else:
            my_to = to_date
            my_from = from_date

        d = []
        for m in metrics:
            d.append(Sensordata(api=self.api, parent=self, metric=m,
                                from_date=my_from, to_date=my_to).to_series().to_frame())
        return pd.concat(d, join="outer", axis=1)
        # def get_frame(self, metrics, days_back=None):
        #     frames = [self.get_series(x, days_back=days_back).to_frame(name=x) for x in metrics]
        #     frame = pd.concat(frames, join="outer", axis=1)
        #     return frame


class EventMixin(object):
    DEFAULT_DAYS_BACK = 30

    def get_events(self, from_date=None, to_date=None, days_back=None):
        if days_back is None:
            days_back = self.DEFAULT_DAYS_BACK

        if from_date is None or to_date is None:
            my_to = datetime.datetime.utcnow() + datetime.timedelta(days=1)
            my_from = datetime.datetime.utcnow() - datetime.timedelta(days=days_back)
        else:
            my_to = to_date
            my_from = from_date

        return Events(api=self.api, parent=self,
                      from_date=my_from, to_date=my_to)


class Event(APIObject):
    @property
    def event_type(self):
        return self.data["event_type"]

    @property
    def metadata(self):
        return self.data["metadata"]

    @property
    def organisation_id(self):
        return self.data["organisation_id"]

    @property
    def date(self):
        return self.fromTS(self.data["timestamp"])


class Events(object):
    def __init__(self, api, parent, from_date=None, to_date=None):
        self.api = api
        self.parent = parent
        self.from_date = from_date
        self.to_date = to_date
        self._data = {}
        assert isinstance(self.parent, Animal) or isinstance(self.parent, Device)

    @property
    def data(self):
        if not self._data:
            f = toTS(self.from_date)
            t = toTS(self.to_date)
            if isinstance(self.parent, Animal):
                self._data = self.api.get_animal_events(self.parent._id, f, t)
            elif isinstance(self.parent, Device):
                self._data = self.api.get_device_events(self.parent._id, f, t)
            self._data = [
                Event.create_from_data(
                    api=self.api,
                    data=x,
                    timezone=self.parent.timezone
                ) for x in self._data
            ]

            self._data.sort(key=lambda x: x.date)
        return self._data

    def to_series(self):
        return pd.Series([x.event_type for x in self.data],
                         index=np.array([x.date for x in self.data]).astype('datetime64[s]'),
                         name="event")

    def to_list(self):
        return self.data

    def __str__(self):
        return "<{}({})>".format(self.__class__.__name__, getattr(self.parent, "_id", "unknown"))

    def __repr__(self):
        return "<{}({})>".format(self.__class__.__name__, getattr(self.parent, "_id", "unknown"))


class User(APIObject):
    def __init__(self, api, data):
        self.api = api
        self._data = data
        t = self._data.get("type", "unknown")
        if t.lower() == "email":
            self._id = self._data["_id"]
            self.name = self._data["email"]
        else:
            self._id = "{}_user".format(t)
            self.name = "{}_user".format(t)


class Sensordata(object):
    def __init__(self, api, parent, metric, from_date=None, to_date=None):
        self.api = api
        self.parent = parent
        self.metric = metric
        self.from_date = from_date
        self.to_date = to_date
        self._data = {}
        assert isinstance(self.parent, Animal) or isinstance(self.parent, Device)

    @property
    def data(self):
        if not self._data:
            f = toTS(self.from_date)
            t = toTS(self.to_date)
            if isinstance(self.parent, Animal):
                self._data = self.api.get_animal_sensordata(self.parent._id, self.metric, f, t)
            elif isinstance(self.parent, Device):
                self._data = self.api.get_device_sensordata(self.parent._id, self.metric, f, t)
        return self._data

    def to_series(self):
        return pd.Series([x[1] for x in self.data],
                         index=np.array([x[0] for x in self.data]).astype('datetime64[s]'),
                         name=self.metric)

    def __str__(self):
        return "<{}({}.{})>".format(self.__class__.__name__, getattr(self.parent, "_id", "unknown"),
                                    getattr(self, "metric", "unknown"))

    def __repr__(self):
        return "<{}({}.{})>".format(self.__class__.__name__, getattr(self.parent, "_id", "unknown"),
                                    getattr(self, "metric", "unknown"))

    # def get_frame(self, metrics, days_back=None):
    #     frames = [self.get_series(x, days_back=days_back).to_frame(name=x) for x in metrics]
    #     frame = pd.concat(frames, join="outer", axis=1)
    #     return frame


class Organisation(APIObject):
    def __init__(self, api, _id):
        super(Organisation, self).__init__(api, _id)
        self._animals = None
        self._events = None
        self._devices = None

    def get_data(self):
        return self.api.get_organisation_by_id(self._id)

    @property
    def name(self):
        return self.data["name"]

    @property
    def features(self):
        return self.data["features"]

    @property
    def metadata(self):
        return self.data["metadata"]

    def get_device_ids(self):
        return self.data["devices"]

    @property
    def timezone(self):
        return self.data["timezone"]

    def get_animal_ids(self):
        return self.api.get_organisation_animal_ids(self._id)

    @property
    def devices(self):
        if not self._devices:
            self._devices = [Device(api=self.api, _id=x) for x in self.get_device_ids()]
        return self._devices

    @property
    def animals(self):
        if not self._animals:
            self._animals = [Animal(api=self.api, _id=x) for x in self.get_animal_ids()]
        return self._animals


class Device(APIObject, DataMixin, EventMixin):
    def __init__(self, api, _id):
        super(Device, self).__init__(api, _id)
        self._sensordata = None
        self._events = None

    def get_data(self):
        return self.api.get_device_by_id(self._id)

    @property
    def name(self):
        return self.data["name"]

    @property
    def metadata(self):
        return self.data["metadata"]

    @property
    def organisation_id(self):
        return self.data["organisation_id"]


class Lactation(APIObject):
    def __init__(self, api, _id):
        super(Lactation, self).__init__(api, _id)

    @property
    def confirmed(self):
        return self.data["confirmed"]

    @property
    def number(self):
        return self.data["number"]

    @property
    def milk_yield(self):
        return self.data["milk_yield"]

    @property
    def date(self):
        return self.fromTS(self.data["calving_date"])

    def __str__(self):
        return "<{}({})>".format(self.__class__.__name__, self.date)

    def __repr__(self):
        return "<{}({})>".format(self.__class__.__name__, self.date)


class Heat(APIObject):
    def __init__(self, api, _id):
        super(Heat, self).__init__(api, _id)

    @property
    def pregnant(self):
        return self.data["pregnant"]

    @property
    def abort(self):
        return self.data["abort"]

    @property
    def insemination(self):
        return self.data["insemination"]

    @property
    def date(self):
        return self.fromTS(self.data["heat_date"])

    def __str__(self):
        return "<{}({})>".format(self.__class__.__name__, self.date)

    def __repr__(self):
        return "<{}({})>".format(self.__class__.__name__, self.date)


class Animal(APIObject, DataMixin, EventMixin):
    def __init__(self, api, _id):
        super(Animal, self).__init__(api, _id)
        self._sensordata = None
        self._events = None
        self._lactations = None
        self._heats = None

    def get_data(self):
        return self.api.get_animal_by_id(self._id)

    def organisation_id(self):
        return self.data["organisation_id"]

    @property
    def current_dim(self):
        return self.to_dim(pendulum.now(self.timezone))

    def to_dim(self, dt):
        return self.fast_dim_range(dt, dt)[0][1]

    def fast_dim_range(self, from_dt, to_dt, interval=60*60, timestamp=False):
        out = []
        cdt = pendulum.instance(to_dt)

        all_lactations = []
        for lac in self.lactations:
            all_lactations.append(pendulum.instance(lac.date.replace(hour=0, minute=0, second=0, microsecond=0)))

        lac_idx = 1
        while from_dt <= cdt:
            if len(all_lactations) < 1:
                out.append((cdt, -14.5))
                cdt = cdt.subtract(seconds=interval)
                continue
            elif lac_idx >= len(all_lactations):
                dim = math.floor((cdt - all_lactations[-lac_idx]).total_seconds() / (24*60*60))
                if dim < -14:
                    dim = -14.5
                out.append((cdt, dim))
                cdt = cdt.subtract(seconds=interval)
                continue
            elif lac_idx < len(all_lactations):
                dim = math.floor((cdt - all_lactations[-lac_idx]).total_seconds() / (24*60*60))
                while len(all_lactations) > lac_idx and all_lactations[-lac_idx].subtract(days=14) > cdt:
                    lac_idx += 1
                    dim = math.floor((cdt - all_lactations[-lac_idx]).total_seconds() / (24*60*60))
                out.append((cdt, dim))
                cdt = cdt.subtract(seconds=interval)
                continue
            else:
                assert False  # WTF
        if timestamp is True:
            out = [(toTS(ts), v) for ts, v in out]
        return list(reversed(out))

    def dim_range(self, from_dt, to_dt, interval=60*60, timestamp=False):
        return self.fast_dim_range(from_dt, to_dt, interval=interval, timestamp=timestamp)

    # def toDIM(self, dt):
    #     #  get all calving dates, make sure they are sorted by date
    #     closest_calving = None
    #     days14 = datetime.timedelta(days=14)
    #     days120 = datetime.timedelta(days=120)

    #     for lactation in self.lactations:
    #         calving_date = lactation.date
    #         start = calving_date - days14
    #         end = calving_date + days120
    #         if start <= dt <= end:
    #             closest_calving = calving_date
    #     if closest_calving is None:
    #         return -14.5
    #     else:
    #         delta = dt - closest_calving
    #     return delta.days

    # Remove this once it is coming from the animal
    @property
    def timezone(self):
        if self._timezone is None:
            self._timezone = self.api.get_timezone_for_organisation_id(self.data["organisation_id"])
        return self._timezone

    @property
    def name(self):
        return self.data["name"]

    @property
    def mark(self):
        return self.data["mark"]

    @property
    def group_id(self):
        return self.data["group_id"]

    @property
    def tags(self):
        return self.data["tags"]

    @property
    def sensor(self):
        return self.data["sensor"]

    @property
    def metadata(self):
        return self.data["metadata"]

    @property
    def heats(self):
        if not self._heats:
            self._heats = [Heat.create_from_data(api=self.api, data=h, timezone=self.timezone)
                           for h in self.data["heats"]]
            self._heats.sort(key=lambda x: x.date)
        return self._heats

    @property
    def lactations(self):
        if not self._lactations:
            self._lactations = [Lactation.create_from_data(api=self.api, data=h, timezone=self.timezone)
                                for h in self.data["lactations"]]
            self._lactations.sort(key=lambda x: x.date)
        return self._lactations

    @property
    def events(self):
        if not self._events:
            self._events = self.api.get_animal_events(self._id)
        return self._events


class Annotation(APIObject):
    def __init__(self, api, _id):
        super(Annotation, self).__init__(api, _id)

    def get_data(self):
        return self.api.get_annotation_by_id(self._id)

    @property
    def end_timestamp(self):
        return self.data["end_ts"]

    @property
    def reference_type(self):
        return self.data["reference_type"]

    @property
    def timestamp(self):
        return self.data["ts"]

    @property
    def attributes(self):
        return self.data["attributes"]

    @property
    def classes(self):
        return self.data["classes"]


class TestSet(APIObject):
    def __init__(self, api, _id):
        super(TestSet, self).__init__(api, _id)

    def get_data(self):
        return self.api.get_testset_by_id(self._id)

    @property
    def name(self):
        return self.data["name"]

    @property
    def meta_data(self):
        return self.data["meta_data"]

    @property
    def annotations(self):
        return self.data["annotations"]
