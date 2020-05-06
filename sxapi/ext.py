#!/usr/bin/python
# coding: utf8

import logging

from flask import current_app
from flask import _app_ctx_stack as stack

from . import API, LowLevelAPI


logger = logging.getLogger(__name__)


class FlaskSX(object):
    def __init__(self, app=None):
        """
        Initialize this extension.

        :param obj app: The Flask application (optional).
        """
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """
        Initialize this extension.

        :param obj app: The Flask application.
        """
        self.init_settings(app)

    def init_settings(self, app):
        """Initialize all of the extension settings."""
        app.config.setdefault('SMAXTEC_API_EMAIL', None)
        app.config.setdefault('SMAXTEC_API_PASSWORD', None)
        app.config.setdefault('SMAXTEC_API_PUBLIC_ENDPOINT', None)
        app.config.setdefault('SMAXTEC_API_PRIVATE_ENDPOINT', None)
        app.config.setdefault('SMAXTEC_API_KEY', None)
        app.config.setdefault('SMAXTEC_API_TZ_AWARE', True)

    @property
    def highlevel(self):
        """
        Our high level API session.

        This will be lazily created if this is the first time this is being
        accessed. This connection is reused for performance.
        """
        ctx = stack.top
        if ctx is not None:
            if not hasattr(ctx, 'sx_high'):
                ctx.sx_high = API(email=current_app.config["SMAXTEC_API_EMAIL"],
                                  password=current_app.config["SMAXTEC_API_PASSWORD"],
                                  api_key=current_app.config["SMAXTEC_API_KEY"],
                                  endpoint=current_app.config["SMAXTEC_API_PUBLIC_ENDPOINT"],
                                  tz_aware=current_app.config["SMAXTEC_API_TZ_AWARE"])
            return ctx.sx_high
        raise RuntimeError("No App Context")

    @property
    def lowlevel(self):
        """
        Our low level API session.

        This will be lazily created if this is the first time this is being
        accessed. This connection is reused for performance.
        """
        ctx = stack.top
        if ctx is not None:
            if not hasattr(ctx, 'sx_low'):
                ctx.sx_low = LowLevelAPI(private_endpoint=current_app.config["SMAXTEC_API_PRIVATE_ENDPOINT"],
                                         password=current_app.config["SMAXTEC_API_PASSWORD"],
                                         email=current_app.config["SMAXTEC_API_EMAIL"],
                                         api_key=current_app.config["SMAXTEC_API_KEY"],
                                         public_endpoint=current_app.config["SMAXTEC_API_PUBLIC_ENDPOINT"],
                                         tz_aware=current_app.config["SMAXTEC_API_TZ_AWARE"])
            return ctx.sx_low
        raise RuntimeError("No App Context")

    @property
    def status(self):
        return self.highlevel.status

    @property
    def user(self):
        return self.highlevel.user

    @property
    def organisations(self):
        return self.highlevel.organisations

    def get_animal_object(self, animal_id):
        return self.highlevel.get_animal(animal_id)

    def get_organisation_object(self, organisation_id):
        return self.highlevel.get_organisation(organisation_id)

    def get_group_data_bulk(self, group_id, metrics, from_date, to_date):
        return self.lowlevel.getGroupSensorDataBulk(group_id, metrics, from_date, to_date)

    # Find other API calls
    def __getattr__(self, item):
        if "init" in item:
            raise AttributeError("Call to invalid API function: %s" % item)

        ctx = stack.top
        if ctx is None:
            raise RuntimeError("API call outside of Flask Context")

        if hasattr(self.lowlevel, item):
            low = getattr(self.lowlevel, item)
            if callable(low):
                return low

        raise AttributeError("API function not found: %s" % item)
