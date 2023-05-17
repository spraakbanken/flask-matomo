import typing
from dataclasses import dataclass
from unittest import mock
from urllib.parse import parse_qs, urlsplit

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
    print(f"{matomo_client!r}")
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

    # async def custom_var(request: Request):
    #     if "state" not in request.scope:
    #         request.scope["state"] = {}
    #     request.scope["state"]["asgi_matomo"] = {
    #         "e_a": "Playing",
    #         "pf_srv": "123",
    #         "cvar": {"anything": "goes"},
    #     }
    #     return PlainTextResponse("custom_var")

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
    # app.add_route("/set/custom/var", custom_var)
    # app.add_route("/baz", baz, methods=["POST"])
    return app


@pytest.fixture(name="app")
def fixture_app(matomo_client, settings: dict) -> Flask:
    return create_app(matomo_client, settings)


@pytest.fixture(name="expected_q")
def fixture_expected_q(settings: dict) -> dict:
    return {
        "idsite": [str(settings["idsite"])],
        "url": ["http://testserver"],
        # "apiv": ["1"],
        # "lang": ["None"]
        "rec": ["1"],
        "ua": ["python-httpx/0.24.0"],
        "cip": ["127.0.0.1"],
        "token_auth": ["FAKE_TOKEN"],
        # "send_image": ["0"],
        # "cvar": ['{"http_status_code": 200, "http_method": "GET"}'],
    }


@pytest.fixture(name="client")
def fixture_client(app: Flask) -> typing.Generator[httpx.Client, None, None]:
    with httpx.Client(app=app, base_url="http://testserver") as client:
        yield client


def assert_query_string(url: str, expected_q: dict) -> None:
    urlparts = urlsplit(url[6:-2])
    q = parse_qs(urlparts.query)
    # assert q.pop("rand") is not None
    # assert q.pop("gt_ms") is not None

    assert q == expected_q


def test_matomo_client_gets_called_on_get_foo(client, matomo_client, expected_q: dict):
    response = client.get("/foo")
    assert response.status_code == 200

    matomo_client.get.assert_called()  # get.assert_called()

    expected_q["url"][0] += "/foo"
    expected_q["action_name"] = ["/foo"]
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
