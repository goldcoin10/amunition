import gzip
import json
import requests
from rapidfuzz import fuzz, process
from datetime import datetime, timezone
from . import api_key
from .types import *


def get_operator_list() -> dict[str, str]:
    operators_url: str = "http://api.511.org/transit/operators"
    operators_raw = requests.get(operators_url, params={"api_key": api_key}, timeout=10)
    operators_raw.raise_for_status()

    ret = dict()
    operators = operators_raw.content

    if operators.startswith(b"\x1f\x8b"):
        operators = gzip.decompress(operators)
    operators = json.loads(operators.decode("utf-8-sig"))
    for op in operators:
        if op.get("Name").startswith("511") or op.get("Name").startswith("Regional"):
            pass
        else:
            ret.update({ op.get("PrivateCode"): op.get("ShortName") or op.get("Name")})
    return ret
def get_operator_routes(private_code: str) -> TransitList:
    routes_url: str = "http://api.511.org/transit/lines"
    routes_raw = requests.get(routes_url, params={"api_key": api_key, "operator_id": private_code}, timeout=10)
    routes_raw.raise_for_status()

    ret: TransitList = []
    routes = routes_raw.content
    
    if routes.startswith(b"\x1f\x8b"):
        routes = gzip.decompress(routes)
    routes = json.loads(routes.decode("utf-8-sig"))
    for ro in routes:
        ret.append([ro.get("Id"), ro.get("Name"), ro.get("TransportMode"), private_code])
    return ret
def get_operator_stops(private_code: str) -> TransitList:
    stops_url: str = "http://api.511.org/transit/stops"
    stops_raw = requests.get(stops_url, params={"api_key": api_key, "Operator_id": private_code}, timeout=10)

    ret: TransitList = []
    stops = stops_raw.content

    if stops.startswith(b"\x1f\x8b"):
        stops = gzip.decompress(stops)

    data = json.loads(stops.decode("utf-8-sig"))

    points = (
        data.get("Contents", {})
        .get("dataObjects", {})
        .get("ScheduledStopPoint", [])
    )

    for stop in points:
        ret.append([stop["id"], stop["Name"], private_code])

    return ret

def get_next_bus(stop_id: str, private_code: str) -> TransitList:
    stop_url: str = "http://api.511.org/transit/StopMonitoring"
    stop_raw = requests.get(stop_url, params={"api_key": api_key, "agency": private_code, "stopCode": stop_id}, timeout=10)
    stop_raw.raise_for_status()

    ret: list[list[str]] = []
    stop = stop_raw.content

    if stop.startswith(b"\x1f\x8b"):
        stop = gzip.decompress(stop)
    stop = json.loads(stop.decode("utf-8-sig"))
    visits = (
        stop.get("ServiceDelivery", {})
        .get("StopMonitoringDelivery", {})
        .get("MonitoredStopVisit", {})
    )
    for st in visits[:5]:
        journey = st.get("MonitoredVehicleJourney", {})
        call = journey.get("MonitoredCall", {})
        if bus_time_to_minutes(call.get("ExpectedDepartureTime")) == None:
            expected_departure_min = bus_time_to_minutes(call.get("AimedDepartureTime"))
        else:
            expected_departure_min = bus_time_to_minutes(call.get("ExpectedDepartureTime"))
        ret.append([
            str(stop_id),
            call.get("StopPointName").removeprefix("Metro "),
            str(expected_departure_min),
            journey.get("LineRef"),
            journey.get("PublishedLineName"),
            journey.get("DestinationDisplay") or journey.get("DestinationName")
        ])
    return ret

def get_route_stops(line_id: str, private_code: str) -> TransitList:
    stops_url: str = "http://api.511.org/transit/stops"
    stops_raw = requests.get(stops_url, params={"api_key": api_key, "Operator_id": private_code, "Line_id": line_id}, timeout=10)

    ret: TransitList = []
    stops = stops_raw.content

    if stops.startswith(b"\x1f\x8b"):
        stops = gzip.decompress(stops)

    data = json.loads(stops.decode("utf-8-sig"))
    points = (
        data.get("Contents", {})
        .get("dataObjects", {})
        .get("ScheduledStopPoint", [])
    )

    for stop in points:
        ret.append([stop["id"], stop["Name"], private_code])

    return ret

def bus_time_to_minutes(dep_time: str | None) -> str | None:
    if dep_time == None:
        return None
    cur_dt: datetime = datetime.now(timezone.utc)
    dep_dt: datetime = datetime.fromisoformat(dep_time)
    mins: int = int((dep_dt - cur_dt).total_seconds() // 60)
    if mins < 0:
        return "Departed"
    elif mins > 1 or mins == 0:
        ret = str(f"in {mins} minutes")
    else:
        ret = str(f"in {mins} minute")
    return ret

def query(db: TransitList, query: str, max_r: int = 50) -> TransitList:
    ret: TransitList = []
    if not query.strip():
        ret.append(["No", "Query"])
    else:
        searchable: dict[str, str] = {s[0]: f"{s[0]} {s[1]}" for s in db}
        lookup: dict[str, list[str]] = {s[0]: s for s in db}

        matches = process.extract(
            query,
            searchable,
            scorer=fuzz.WRatio,
            limit=max_r,
            score_cutoff=70,
        )
        ret = [lookup[stop_id] for _, _, stop_id in matches]
        if not ret:
            ret.append(["No", "Results"])
    return ret
