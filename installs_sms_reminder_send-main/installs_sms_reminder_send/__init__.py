import os

from notification import Opsgenie
from log import get_logger
from settings import Settings

config = Settings()

logger = get_logger('installs_sms_reminder_send')

opsgenie = Opsgenie(opsgenie_api_key=config.opsgenie_api_key)