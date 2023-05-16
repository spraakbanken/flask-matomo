import logging

logger = logging.getLogger("flask_matomo")


class MatomoError(Exception):
    pass


from flask_matomo.core import Matomo

__all__ = ["Matomo", "MatomoError"]
