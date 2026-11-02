import json
import threading
import urllib.error
import urllib.request

import pytest

from routeopt.cli import build_parser
from routeopt.web import RequestError, make_server, solve_request


def test_solve_request_generated_orders() -> None:
    result = solve_request({"n": 15, "seed": 2, "capacity": 25, "solver": "cluster"})
    assert sorted(i for r in result["routes"] for i in r) == list(range(1, 16))
    assert all(load <= 25 for load in result["loads"])
    assert result["distance"] > 0


def test_solve_request_from_csv_text() -> None:
    csv_text = "id,x,y,demand\n7,10,10,3\n9,20,5,4\n"
    result = solve_request({"csv": csv_text, "capacity": 10, "solver": "greedy"})
    assert [o["id"] for o in result["orders"]] == [1, 2]  # renumbered


@pytest.mark.parametrize(
    "payload",
    [
        [],
        {"solver": "nope"},
        {"solver": "exact", "n": 20},
        {"n": 600},
        {"capacity": 0},
        {"csv": "id,x\n1,2\n"},
        {"depot": [1]},
        {"n": "abc"},
    ],
)
def test_solve_request_rejects_bad_input(payload: object) -> None:
    with pytest.raises(RequestError):
        solve_request(payload)


def test_http_server_round_trip() -> None:
    server = make_server("127.0.0.1", 0)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"
    try:
        with urllib.request.urlopen(base + "/") as page:
            assert b"Delivery Route Optimizer" in page.read()

        def post(path: str, body: bytes) -> tuple[int, dict[str, object]]:
            req = urllib.request.Request(base + path, data=body, method="POST")
            try:
                with urllib.request.urlopen(req) as resp:
                    return resp.status, json.loads(resp.read())
            except urllib.error.HTTPError as err:
                return err.code, json.loads(err.read())

        status, data = post("/api/solve", json.dumps({"n": 10, "capacity": 20}).encode())
        assert status == 200 and data["routes"]
        assert post("/api/solve", b"{not json")[0] == 400
        assert post("/api/solve", json.dumps({"solver": "x"}).encode())[0] == 400
        assert post("/other", b"{}")[0] == 404
        with pytest.raises(urllib.error.HTTPError):
            urllib.request.urlopen(base + "/missing")
    finally:
        server.shutdown()
        server.server_close()


def test_serve_command_is_registered() -> None:
    args = build_parser().parse_args(["serve", "--port", "9000"])
    assert (args.command, args.port, args.host) == ("serve", 9000, "127.0.0.1")
