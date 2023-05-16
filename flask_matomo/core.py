import typing
import urllib.parse
from threading import Thread

import httpx
from flask import current_app, g, request

from . import MatomoError


class Matomo(object):
    """The Matomo object provides the central interface for interacting with Matomo.

    Args:
        app (Flask object): created with Flask(__name__)
        matomo_url (str): url to Matomo installation
        id_site (int): id of the site that should be tracked on Matomo
        token_auth (str): token that can be found in the area API in the settings of Matomo
        base_url (str): url to the site that should be tracked
    """

    def __init__(
        self,
        app=None,
        *,
        matomo_url: str,
        id_site=None,
        token_auth=None,
        base_url=None,
        client=None,
    ):
        self.app = app
        self.matomo_url = matomo_url
        self.id_site = id_site
        self.token_auth = token_auth
        self.base_url = base_url.strip("/") if base_url else base_url
        self.ignored_ua_prefixes = []
        self.ignored_routes: typing.List[str] = []
        self.routes_details: typing.Dict[str, typing.Dict[str, str]] = {}
        self.client = client or httpx.Client()

        if not matomo_url:
            raise ValueError("matomo_url has to be set")
        if type(id_site) != int:
            raise ValueError("id_site has to be an integer")
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Initialize app"""
        app.before_request(self.before_request)
        app.teardown_request(self.teardown_request)

    def before_request(self):
        """Exectued before every request, parses details about request"""
        # Don't track track request, if user used ignore() decorator for route
        if str(request.url_rule) in self.ignored_routes:
            return
        if any(
            str(request.user_agent).startswith(ua_prefix)
            for ua_prefix in self.ignored_ua_prefixes
        ):
            return

        if self.base_url:
            url = self.base_url + request.path
        else:
            url = request.url

        if request.url_rule:
            action_name = str(request.url_rule)
        else:
            action_name = "Not Found"

        user_agent = request.user_agent
        # If request was forwarded (e.g. by a proxy), then get origin IP from
        # HTTP_X_FORWARDED_FOR. If this header field doesn't exist, return
        # remote_addr.
        ip_address = request.environ.get("HTTP_X_FORWARDED_FOR", request.remote_addr)

        keyword_arguments = {
            "action_name": action_name,
            "url": url,
            "user_agent": user_agent,
            "ip_address": ip_address,
        }

        # Overwrite action_name, if it was configured with config()
        if self.routes_details.get(action_name) and self.routes_details.get(action_name).get(
            "action_name"
        ):
            keyword_arguments["action_name"] = self.routes_details.get(action_name).get(
                "action_name"
            )

        # Create new thread with request, because otherwise the original request will be blocked
        # Thread(target=self.track, kwargs=keyword_arguments).start()
        g.flask_matomo = keyword_arguments

    def teardown_request(self, exc: typing.Optional[Exception] = None) -> None:
        keyword_arguments = g.get("flask_matomo", {})

        self.track(**keyword_arguments)

    def track(self, action_name, url, user_agent=None, id=None, ip_address=None):  # noqa: A002
        """Send request to Matomo

        Args:
            action_name (str): name of the site
            url (str): url to track
            user_agent (str): User-Agent of request
            id (str): id of user
            ip_address (str): ip address of request
        """
        data = {
            "idsite": str(self.id_site),
            "rec": "1",
            "ua": user_agent,
            "action_name": action_name,
            "url": url,
            # "_id": id,
            "token_auth": self.token_auth,
            "cip": ip_address,
        }
        tracking_params = urllib.parse.urlencode(data)
        tracking_url = f"{self.matomo_url}?{tracking_params}"
        print(f"calling {tracking_url}")
        r = self.client.get(tracking_url)

        if r.status_code >= 300:
            raise MatomoError(r.text)

    def ignore(self):
        """Ignore a route and don't track it

        Args:
            action_name (str): name of the site
            url (str): url to track
            user_agent (str): User-Agent of request
            id (str): id of user
            ip_address (str): ip address of request

        Examples:
            @app.route("/admin")
            @matomo.ignore()
            def admin():
                return render_template("admin.html")
        """

        def wrap(f):
            self.ignored_routes.append(f.__name__)
            return f

        return wrap

    def details(self, action_name=None):
        """Set details like action_name for a route

        Args:
            action_name (str): name of the site

        Examples:
            @app.route("/users")
            @matomo.details(action_name="Users")
            def all_users():
                return render_template("users.html")
        """

        def wrap(f):
            self.routes_details[f.__name__] = {"action_name": action_name}
            return f

        return wrap
