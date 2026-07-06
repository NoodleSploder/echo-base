"""Human-readable lookups for SAME header fields.

Event codes and state FIPS codes are small, stable, official tables
(NWS/EAS spec) and are embedded in full. County-level FIPS codes are
not: there are ~3,200 US counties/equivalents, and embedding that full
database is disproportionate to a decoder that -- per the diary --
hasn't decoded a single real over-the-air packet yet in this
environment. County codes are shown numerically instead of guessing at
a partial table that would be wrong as often as it's right.
"""
from __future__ import annotations

# Same-word (SAME) event codes -- see https://www.weather.gov/nwr/eventcodes
EVENT_CODES: dict[str, str] = {
    "ADR": "Administrative Message",
    "AVA": "Avalanche Watch",
    "AVW": "Avalanche Warning",
    "BZW": "Blizzard Warning",
    "CAE": "Child Abduction Emergency",
    "CDW": "Civil Danger Warning",
    "CEM": "Civil Emergency Message",
    "CFA": "Coastal Flood Watch",
    "CFW": "Coastal Flood Warning",
    "DSW": "Dust Storm Warning",
    "EAN": "Emergency Action Notification",
    "EAT": "Emergency Action Termination",
    "EQW": "Earthquake Warning",
    "EVI": "Evacuation Immediate",
    "EWW": "Extreme Wind Warning",
    "FFA": "Flash Flood Watch",
    "FFS": "Flash Flood Statement",
    "FFW": "Flash Flood Warning",
    "FLA": "Flood Watch",
    "FLS": "Flood Statement",
    "FLW": "Flood Warning",
    "FRW": "Fire Warning",
    "FSW": "Flash Freeze Warning",
    "FZW": "Freeze Warning",
    "HMW": "Hazardous Materials Warning",
    "HUA": "Hurricane Watch",
    "HUW": "Hurricane Warning",
    "HWA": "High Wind Watch",
    "HWW": "High Wind Warning",
    "LAE": "Local Area Emergency",
    "LEW": "Law Enforcement Warning",
    "NIC": "National Information Center",
    "NMN": "Network Message Notification",
    "NPT": "National Periodic Test",
    "NUW": "Nuclear Power Plant Warning",
    "POS": "Power Outage",
    "RHW": "Radiological Hazard Warning",
    "RMT": "Required Monthly Test",
    "RWT": "Required Weekly Test",
    "SPS": "Special Weather Statement",
    "SPW": "Shelter in Place Warning",
    "SVA": "Severe Thunderstorm Watch",
    "SVR": "Severe Thunderstorm Warning",
    "SVS": "Severe Weather Statement",
    "TOA": "Tornado Watch",
    "TOE": "911 Telephone Outage Emergency",
    "TOR": "Tornado Warning",
    "TRA": "Tropical Storm Watch",
    "TRW": "Tropical Storm Warning",
    "TSA": "Tsunami Watch",
    "TSW": "Tsunami Warning",
    "VOW": "Volcano Warning",
    "WSA": "Winter Storm Watch",
    "WSW": "Winter Storm Warning",
}

# Location code's leading digit: geographic subdivision of the county/zone.
SUBDIVISION_NAMES: dict[str, str] = {
    "0": "",  # entire county/area -- no qualifier needed
    "1": "Northwest",
    "2": "North",
    "3": "Northeast",
    "4": "West",
    "5": "Central",
    "6": "East",
    "7": "Southwest",
    "8": "South",
    "9": "Southeast",
}

# State/territory FIPS codes (the SS in a PSSCCC location code).
STATE_FIPS: dict[str, str] = {
    "01": "Alabama", "02": "Alaska", "04": "Arizona", "05": "Arkansas",
    "06": "California", "08": "Colorado", "09": "Connecticut", "10": "Delaware",
    "11": "District of Columbia", "12": "Florida", "13": "Georgia", "15": "Hawaii",
    "16": "Idaho", "17": "Illinois", "18": "Indiana", "19": "Iowa",
    "20": "Kansas", "21": "Kentucky", "22": "Louisiana", "23": "Maine",
    "24": "Maryland", "25": "Massachusetts", "26": "Michigan", "27": "Minnesota",
    "28": "Mississippi", "29": "Missouri", "30": "Montana", "31": "Nebraska",
    "32": "Nevada", "33": "New Hampshire", "34": "New Jersey", "35": "New Mexico",
    "36": "New York", "37": "North Carolina", "38": "North Dakota", "39": "Ohio",
    "40": "Oklahoma", "41": "Oregon", "42": "Pennsylvania", "44": "Rhode Island",
    "45": "South Carolina", "46": "South Dakota", "47": "Tennessee", "48": "Texas",
    "49": "Utah", "50": "Vermont", "51": "Virginia", "53": "Washington",
    "54": "West Virginia", "55": "Wisconsin", "56": "Wyoming", "60": "American Samoa",
    "66": "Guam", "69": "Northern Mariana Islands", "72": "Puerto Rico",
    "78": "U.S. Virgin Islands",
}  # fmt: skip


def describe_event(event_code: str) -> str:
    return EVENT_CODES.get(event_code, event_code)


def describe_location(location_code: str) -> str:
    """Formats a 6-digit "PSSCCC" location code, e.g. "0" + "06" + "037"
    -> "Los Angeles area" isn't derivable without a county database, so
    this returns "County 037, California" -- state name resolved, county
    left numeric rather than guessed."""
    if len(location_code) != 6 or not location_code.isdigit():
        return location_code

    subdivision, state_fips, county_fips = (
        location_code[0],
        location_code[1:3],
        location_code[3:6],
    )
    state = STATE_FIPS.get(state_fips, f"FIPS state {state_fips}")
    prefix = SUBDIVISION_NAMES.get(subdivision, "")
    county = f"County {county_fips}"
    described = f"{prefix} {county}, {state}".strip()
    return " ".join(described.split())  # collapse the double space when prefix is empty
