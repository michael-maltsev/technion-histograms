import argparse
import json
import re
import sys
import time
import urllib.parse

import requests

REQUEST_TIMEOUT = 60

session = requests.session()


def set_proxy(proxy_server: str):
    session.proxies = {
        "http": proxy_server,
        "https": proxy_server,
    }


def send_request_once(query: str, lang: str):
    url = "https://portalex.technion.ac.il/sap/opu/odata/sap/Z_CM_EV_CDIR_DATA_SRV/$batch?sap-client=700"

    headers = {
        "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Brave";v="126"',
        "MaxDataServiceVersion": "2.0",
        "Accept-Language": lang,
        "sec-ch-ua-mobile": "?0",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like"
            " Gecko) Chrome/126.0.0.0 Safari/537.36"
        ),
        "Content-Type": "multipart/mixed;boundary=batch_1d12-afbf-e3c7",
        "Accept": "multipart/mixed",
        "sap-contextid-accept": "header",
        "sap-cancel-on-close": "true",
        "X-Requested-With": "X",
        "DataServiceVersion": "2.0",
        "sec-ch-ua-platform": '"Windows"',
        "Sec-GPC": "1",
        "Origin": "https://portalex.technion.ac.il",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": "https://portalex.technion.ac.il/ovv/",
    }

    data = f"""
--batch_1d12-afbf-e3c7
Content-Type: application/http
Content-Transfer-Encoding: binary

GET {query} HTTP/1.1
sap-cancel-on-close: true
X-Requested-With: X
sap-contextid-accept: header
Accept: application/json
Accept-Language: {lang}
DataServiceVersion: 2.0
MaxDataServiceVersion: 2.0


--batch_1d12-afbf-e3c7--
"""
    data = data.replace("\n", "\r\n")

    response = session.post(url, headers=headers, data=data, timeout=REQUEST_TIMEOUT)
    if response.status_code != 202:
        raise RuntimeError(f"Bad status code: {response.status_code}, expected 202")

    response_chunks = response.text.replace("\r\n", "\n").strip().split("\n\n")
    if len(response_chunks) != 3:
        raise RuntimeError(f"Invalid response: {response_chunks}")

    json_str = response_chunks[2].split("\n", 1)[0]
    return json.loads(json_str)


def send_request(query: str, lang: str = "he"):
    delay = 5
    while True:
        try:
            return send_request_once(query, lang)
        except Exception as e:
            print(f"Error: {e} for {query}", file=sys.stderr)
            time.sleep(delay)
            delay = min(delay * 2, 300)


def get_available_semesters():
    params = {
        "sap-client": "700",
        "$select": "PiqYear,PiqSession",
    }
    raw_data = send_request(f"SemesterSet?{urllib.parse.urlencode(params)}")
    results = raw_data["d"]["results"]
    if not results:
        raise RuntimeError("No semesters found")

    semesters = set()
    for r in results:
        semesters.add((int(r["PiqYear"]), int(r["PiqSession"])))
    return semesters


def get_last_semester():
    semesters = get_available_semesters()
    valid = [(y, s) for y, s in semesters if s in [200, 201, 202]]
    if not valid:
        raise RuntimeError("No valid semesters found")
    return max(valid)


def lookup_by_number(year: int, semester: int, number: str, lang: str):
    number = number.zfill(8)
    params = {
        "sap-client": "700",
        "$filter": f"Peryr eq '{year}' and Perid eq '{semester}' and Otjid eq 'SM{number}'",
        "$select": "Otjid,Name",
    }
    raw_data = send_request(f"SmObjectSet?{urllib.parse.urlencode(params)}", lang)
    results = raw_data["d"]["results"]
    if not results:
        return None
    name = re.sub(r"\s+", " ", results[0]["Name"].strip())
    return name


def lookup_by_name(year: int, semester: int, name: str, exact: bool, lang: str):
    params = {
        "sap-client": "700",
        "$filter": f"Peryr eq '{year}' and Perid eq '{semester}' and substringof('{name.replace("'", "''")}',Name)",
        "$select": "Otjid,Name",
    }
    raw_data = send_request(f"SmObjectSet?{urllib.parse.urlencode(params)}", lang)
    results = raw_data["d"]["results"]

    matches = []
    for r in results:
        course_name = re.sub(r"\s+", " ", r["Name"].strip())
        if exact and name != course_name:
            continue
        course_number = r["Otjid"].removeprefix("SM")
        matches.append((course_number, course_name))
    return matches


def main():
    parser = argparse.ArgumentParser(description="Look up Technion courses by number or name.")
    parser.add_argument("--semester", help="Year-semester, e.g. 2025-200 (default: latest)")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-n", "--number", help="Course number to look up")
    group.add_argument("-s", "--name", help="Course name (or part of it) to search for")
    parser.add_argument("-e", "--exact", action="store_true", help="Exact name match")
    parser.add_argument("--en", action="store_true", help="Use English names")
    args = parser.parse_args()

    available = get_available_semesters()

    if args.semester:
        parts = args.semester.split("-")
        year, semester = int(parts[0]), int(parts[1])
        if (year, semester) not in available:
            print(f"Semester {args.semester} not available.", file=sys.stderr)
            print(f"Available semesters: {', '.join(f'{y}-{s}' for y, s in sorted(available))}", file=sys.stderr)
            sys.exit(1)
    else:
        valid = [(y, s) for y, s in available if s in [200, 201, 202]]
        if not valid:
            print("No valid semesters found.", file=sys.stderr)
            sys.exit(1)
        year, semester = max(valid)

    lang = "en" if args.en else "he"

    if args.number:
        result = lookup_by_number(year, semester, args.number, lang)
        if result is None:
            print(f"Course {args.number} not found.", file=sys.stderr)
            sys.exit(1)
        print(result)
    else:
        results = lookup_by_name(year, semester, args.name, args.exact, lang)
        if not results:
            print(f"No courses matching '{args.name}' found.", file=sys.stderr)
            sys.exit(1)
        for course_number, course_name in results:
            print(f"{course_number} {course_name}")


if __name__ == "__main__":
    main()
