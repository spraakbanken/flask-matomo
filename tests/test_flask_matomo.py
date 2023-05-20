import copy
import json
import typing
from dataclasses import dataclass
from unittest import mock
from urllib.parse import parse_qs, urlsplit

import flask
import httpx
import pytest
from flask import Flask

from flask_matomo import Matomo


@pytest.fixture(name="matomo_client")
def fixture_matomo_client():
    client = mock.Mock(spec=httpx.Client)
    # session.mount("mock://", requests_mocker)
    # requests_mocker.register_uri("GET", "mock://testserver")

    @dataclass
    class Response:
        status_code: int

    client.get = mock.Mock(return_value=Response(status_code=204))
    return client


@pytest.fixture(name="settings", scope="session")
def fixture_settings() -> dict:
    return {"idsite": 1, "base_url": "http://testserver", "token_auth": "FAKE_TOKEN"}


def create_app(matomo_client, settings: dict) -> Flask:
    app = Flask(__name__)

    app.config.update({"TESTING": True})
    matomo = Matomo(
        app,
        client=matomo_client,
        matomo_url="http://trackingserver",
        id_site=settings["idsite"],
        token_auth=settings["token_auth"],
        ignored_routes=["/health"],
        # exclude_patterns=[".*/old.*"],
    )

    @app.route("/foo")
    def foo():
        return "foo"

    @app.route("/health")
    def health_fn():
        return "ok"

    @app.route("/heartbeat")
    @matomo.ignore()
    def heartbeat():
        return "ok"

    # async def old(request):
    #     return PlainTextResponse("old")

    @app.route("/set/custom/var")
    def custom_var():
        if "flask_matomo" not in flask.g:
            flask.g.flask_matomo = {"tracking": True}
        flask.g.flask_matomo["custom_tracking_data"] = {
            "e_a": "Playing",
            "pf_srv": "123",
            "cvar": {"anything": "goes"},
        }
        return "custom_var"

    @app.route("/bor")
    @matomo.details(action_name="Foo-Bor")
    def bor():
        return "foo-bor"

    # async def bar(request):
    #     raise HTTPException(status_code=400, detail="bar")

    # async def baz(request):
    #     data = await request.json()
    #     return JSONResponse({"data": data})

    # app.add_route("/bar", bar)
    # app.add_route("/some/old/path", old)
    # app.add_route("/old/path", old)
    # app.add_route("/really/old", old)
    # app.add_route("/baz", baz, methods=["POST"])
    return app


@pytest.fixture(name="app")
def fixture_app(matomo_client, settings: dict) -> Flask:
    return create_app(matomo_client, settings)


@pytest.fixture(name="app_wo_token")
def fixture_app_wo_token(matomo_client, settings: dict) -> Flask:
    new_settings = copy.deepcopy(settings)
    new_settings["token_auth"] = None
    return create_app(matomo_client, new_settings)


@pytest.fixture(name="expected_q")
def fixture_expected_q(settings: dict) -> dict:
    return {
        "idsite": [str(settings["idsite"])],
        "url": ["http://testserver"],
        "apiv": ["1"],
        # "lang": ["None"]
        "rec": ["1"],
        # "ua": ["python-httpx/0.24.0"],
        "cip": ["127.0.0.1"],
        "token_auth": ["FAKE_TOKEN"],
        "send_image": ["0"],
        "cvar": ['{"http_status_code": 200, "http_method": "GET"}'],
    }


@pytest.fixture(name="client")
def fixture_client(app: Flask) -> typing.Generator[httpx.Client, None, None]:
    with httpx.Client(app=app, base_url="http://testserver") as client:
        yield client


@pytest.fixture(name="client_wo_token")
def fixture_client_wo_token(app_wo_token: Flask) -> typing.Generator[httpx.Client, None, None]:
    with httpx.Client(app=app_wo_token, base_url="http://testserver") as client:
        yield client


def assert_query_string(url: str, expected_q: dict) -> None:
    urlparts = urlsplit(url[6:-2])
    q = parse_qs(urlparts.query)
    assert q.pop("rand") is not None
    assert q.pop("gt_ms") is not None
    assert q.pop("ua")[0].startswith("python-httpx")
    cvar = q.pop("cvar")[0]
    expected_cvar = expected_q.pop("cvar")[0]

    assert q == expected_q
    assert json.loads(cvar) == json.loads(expected_cvar)


def test_matomo_client_gets_called_on_get_foo(client, matomo_client, expected_q: dict):
    response = client.get("/foo")
    assert response.status_code == 200

    matomo_client.get.assert_called()  # get.assert_called()

    expected_q["url"][0] += "/foo"
    expected_q["action_name"] = ["/foo"]
    assert_query_string(str(matomo_client.get.call_args), expected_q)


def test_middleware_works_without_token(client_wo_token, matomo_client, expected_q: dict):
    response = client_wo_token.get("/foo")
    assert response.status_code == 200

    matomo_client.get.assert_called()  # get.assert_called()

    expected_q["url"][0] += "/foo"
    expected_q["action_name"] = ["/foo"]
    del expected_q["cip"]
    del expected_q["token_auth"]
    assert_query_string(str(matomo_client.get.call_args), expected_q)


def test_lang_gets_tracked_if_accept_language_is_set(client, matomo_client, expected_q: dict):
    response = client.get("/foo", headers={"accept-language": "sv"})
    assert response.status_code == 200

    matomo_client.get.assert_called()  # get.assert_called()

    expected_q["url"][0] += "/foo"
    expected_q["action_name"] = ["/foo"]
    expected_q["lang"] = ["sv"]
    assert_query_string(str(matomo_client.get.call_args), expected_q)


def test_x_forwarded_for_changes_ip(client, matomo_client, expected_q: dict):
    forwarded_ip = "127.0.0.2"
    response = client.get("/foo", headers={"x-forwarded-for": forwarded_ip})
    assert response.status_code == 200

    matomo_client.get.assert_called()  # get.assert_called()

    expected_q["url"][0] += "/foo"
    expected_q["action_name"] = ["/foo"]
    expected_q["cip"] = [forwarded_ip]
    assert_query_string(str(matomo_client.get.call_args), expected_q)


def test_matomo_client_doesnt_gets_called_on_get_health(
    client: httpx.Client,
    matomo_client,
):
    response = client.get("/health")
    assert response.status_code == 200

    matomo_client.get.assert_not_called()


def test_matomo_client_doesnt_gets_called_on_get_heartbeat(
    client: httpx.Client,
    matomo_client,
):
    response = client.get("/heartbeat")
    assert response.status_code == 200

    matomo_client.get.assert_not_called()


def test_matomo_details_updates_action_name(client, matomo_client, expected_q: dict):
    response = client.get("/bor")
    assert response.status_code == 200

    matomo_client.get.assert_called()  # get.assert_called()

    expected_q["url"][0] += "/bor"
    expected_q["action_name"] = ["Foo-Bor"]
    assert_query_string(str(matomo_client.get.call_args), expected_q)


def test_matomo_client_gets_called_on_get_custom_var(
    client: httpx.Client, matomo_client, expected_q: dict
):
    response = client.get("/set/custom/var")
    assert response.status_code == 200

    matomo_client.get.assert_called()

    expected_q["url"][0] += "/set/custom/var"
    expected_q["action_name"] = ["/set/custom/var"]
    expected_q["e_a"] = ["Playing"]
    expected_q["pf_srv"] = ["123"]
    expected_q["cvar"] = ['{"http_status_code": 200, "http_method": "GET", "anything": "goes"}']

    assert_query_string(str(matomo_client.get.call_args), expected_q)
