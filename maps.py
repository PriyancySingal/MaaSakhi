# ─────────────────────────────────────────────────────────────────
# MaaSakhi — maps.py
# Google Maps integration:
#   • Geocode village/address → lat/lng
#   • Build navigation links for ASHA alerts
#   • Build static map image URLs for WhatsApp messages
#   • Store coordinates back to DB
#   • Village-level distance calculation (ASHA assignment)
# ─────────────────────────────────────────────────────────────────

import os
import math
import urllib.parse
import requests

GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")

# ── Endpoints ──────────────────────────────────────────────────────
GEOCODE_URL    = "https://maps.googleapis.com/maps/api/geocode/json"
STATIC_MAP_URL = "https://maps.googleapis.com/maps/api/staticmap"
DISTANCE_URL   = "https://maps.googleapis.com/maps/api/distancematrix/json"


# ─────────────────────────────────────────────────────────────────
# GEOCODING
# ─────────────────────────────────────────────────────────────────

def geocode_address(address: str, village: str = "", district: str = "") -> dict | None:
    """
    Convert a free-text address / village name to lat/lng.

    Priority: full address → village → village + district

    Returns:
        {
            "lat":       float,
            "lng":       float,
            "formatted": str,   # Google's formatted address
            "place_id":  str
        }
        or None if geocoding fails / no API key.
    """
    if not GOOGLE_MAPS_API_KEY:
        print("maps.py: GOOGLE_MAPS_API_KEY not set — skipping geocode")
        return None

    # Build query strings in priority order
    candidates = []
    if address:
        candidates.append(f"{address}, India")
    if village and district:
        candidates.append(f"{village}, {district}, India")
    if village:
        candidates.append(f"{village}, India")

    for query in candidates:
        try:
            resp = requests.get(
                GEOCODE_URL,
                params={"address": query, "key": GOOGLE_MAPS_API_KEY},
                timeout=5
            )
            data = resp.json()

            if data.get("status") == "OK" and data.get("results"):
                result   = data["results"][0]
                location = result["geometry"]["location"]
                return {
                    "lat":       location["lat"],
                    "lng":       location["lng"],
                    "formatted": result.get("formatted_address", query),
                    "place_id":  result.get("place_id", "")
                }
        except Exception as e:
            print(f"maps.py geocode error for '{query}': {e}")
            continue

    return None


def geocode_village(village_name: str, district: str = "") -> dict | None:
    """
    Convenience wrapper — geocode a village name.
    Returns same dict as geocode_address or None.
    """
    return geocode_address("", village=village_name, district=district)


# ─────────────────────────────────────────────────────────────────
# NAVIGATION LINKS
# ─────────────────────────────────────────────────────────────────

def build_navigation_link(
    address: str = "",
    village: str = "",
    lat: float   = None,
    lng: float   = None
) -> str:
    """
    Build a Google Maps navigation URL for ASHA to open on her phone.

    Uses lat/lng if available (more precise), falls back to address string.

    Returns a URL string (always valid even without an API key).
    """
    if lat is not None and lng is not None:
        # Coordinate-based — most precise
        return (
            f"https://www.google.com/maps/dir/"
            f"?api=1&destination={lat},{lng}&travelmode=driving"
        )

    # Text-based
    location = address or village or ""
    if not location:
        return ""

    encoded = urllib.parse.quote(f"{location}, India")
    return (
        f"https://www.google.com/maps/dir/"
        f"?api=1&destination={encoded}&travelmode=driving"
    )


def build_maps_embed_url(lat: float, lng: float, zoom: int = 14) -> str:
    """
    Build a Google Maps embed URL for dashboards (iframes).
    Requires an API key.
    """
    if not GOOGLE_MAPS_API_KEY:
        return ""
    return (
        f"https://www.google.com/maps/embed/v1/place"
        f"?key={GOOGLE_MAPS_API_KEY}"
        f"&q={lat},{lng}"
        f"&zoom={zoom}"
    )


# ─────────────────────────────────────────────────────────────────
# STATIC MAP IMAGE  (for WhatsApp messages)
# ─────────────────────────────────────────────────────────────────

def build_static_map_url(
    lat: float = None,
    lng: float = None,
    address: str = "",
    zoom: int    = 15,
    width: int   = 600,
    height: int  = 300,
    marker_color: str = "red"
) -> str:
    """
    Build a Google Static Maps API URL showing a pin at the patient's location.
    Returned URL can be sent in a WhatsApp media message.

    Returns "" if no API key or no location.
    """
    if not GOOGLE_MAPS_API_KEY:
        return ""

    if lat is not None and lng is not None:
        center  = f"{lat},{lng}"
        markers = f"color:{marker_color}|{lat},{lng}"
    elif address:
        encoded = urllib.parse.quote(f"{address}, India")
        center  = encoded
        markers = f"color:{marker_color}|{encoded}"
    else:
        return ""

    params = {
        "center":  center,
        "zoom":    zoom,
        "size":    f"{width}x{height}",
        "markers": markers,
        "key":     GOOGLE_MAPS_API_KEY,
        "scale":   2,           # retina
        "maptype": "roadmap"
    }
    return STATIC_MAP_URL + "?" + urllib.parse.urlencode(params)


# ─────────────────────────────────────────────────────────────────
# DISTANCE HELPERS
# ─────────────────────────────────────────────────────────────────

def haversine_distance(lat1: float, lng1: float,
                       lat2: float, lng2: float) -> float:
    """
    Straight-line distance between two lat/lng points in kilometres.
    Uses the Haversine formula — no API call needed.
    """
    R  = 6371.0  # Earth radius km
    φ1 = math.radians(lat1)
    φ2 = math.radians(lat2)
    Δφ = math.radians(lat2 - lat1)
    Δλ = math.radians(lng2 - lng1)

    a = (math.sin(Δφ / 2) ** 2
         + math.cos(φ1) * math.cos(φ2) * math.sin(Δλ / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def road_distance_km(
    origin_lat: float, origin_lng: float,
    dest_lat:   float, dest_lng:   float
) -> float | None:
    """
    Road distance in km using Google Distance Matrix API.
    Falls back to haversine if no API key or request fails.
    """
    if not GOOGLE_MAPS_API_KEY:
        return haversine_distance(origin_lat, origin_lng, dest_lat, dest_lng)
    try:
        resp = requests.get(
            DISTANCE_URL,
            params={
                "origins":      f"{origin_lat},{origin_lng}",
                "destinations": f"{dest_lat},{dest_lng}",
                "units":        "metric",
                "key":          GOOGLE_MAPS_API_KEY
            },
            timeout=5
        )
        data = resp.json()
        element = (
            data.get("rows", [{}])[0]
                .get("elements", [{}])[0]
        )
        if element.get("status") == "OK":
            return element["distance"]["value"] / 1000.0   # metres → km
    except Exception as e:
        print(f"maps.py road distance error: {e}")
    return haversine_distance(origin_lat, origin_lng, dest_lat, dest_lng)


# ─────────────────────────────────────────────────────────────────
# NEAREST HEALTH FACILITY FINDER
# ─────────────────────────────────────────────────────────────────

def find_nearest_health_facility(lat: float, lng: float) -> dict | None:
    """
    Find the nearest PHC / hospital to a given coordinate using
    Google Places Nearby Search.

    Returns:
        {
            "name":     str,
            "address":  str,
            "lat":      float,
            "lng":      float,
            "distance_km": float,
            "maps_url": str
        }
        or None.
    """
    if not GOOGLE_MAPS_API_KEY:
        return None
    try:
        resp = requests.get(
            "https://maps.googleapis.com/maps/api/place/nearbysearch/json",
            params={
                "location": f"{lat},{lng}",
                "radius":   10000,          # 10 km
                "type":     "hospital",
                "keyword":  "PHC CHC government hospital",
                "key":      GOOGLE_MAPS_API_KEY
            },
            timeout=5
        )
        data    = resp.json()
        results = data.get("results", [])

        if not results:
            return None

        best    = results[0]
        f_loc   = best["geometry"]["location"]
        dist_km = haversine_distance(lat, lng, f_loc["lat"], f_loc["lng"])

        return {
            "name":        best.get("name", "Health Facility"),
            "address":     best.get("vicinity", ""),
            "lat":         f_loc["lat"],
            "lng":         f_loc["lng"],
            "distance_km": round(dist_km, 1),
            "maps_url":    build_navigation_link(
                               lat=f_loc["lat"], lng=f_loc["lng"]
                           )
        }
    except Exception as e:
        print(f"maps.py find facility error: {e}")
        return None


# ─────────────────────────────────────────────────────────────────
# DB INTEGRATION — store coords on patient / ASHA worker
# ─────────────────────────────────────────────────────────────────

def geocode_and_store_patient(phone: str, address: str, village: str) -> dict | None:
    """
    Geocode a patient's location and write lat/lng to the DB.
    Call this during patient registration (get_address step in app.py).

    Returns geo dict or None.
    """
    try:
        from database import engine
        from sqlalchemy import text as sqlt
    except ImportError:
        return None

    if not engine:
        return None

    geo = geocode_address(address, village=village)
    if not geo:
        return None

    try:
        with engine.connect() as conn:
            # Add columns if they don't exist yet
            conn.execute(sqlt(
                "ALTER TABLE patients ADD COLUMN IF NOT EXISTS latitude FLOAT"
            ))
            conn.execute(sqlt(
                "ALTER TABLE patients ADD COLUMN IF NOT EXISTS longitude FLOAT"
            ))
            conn.execute(sqlt(
                "ALTER TABLE patients ADD COLUMN IF NOT EXISTS maps_url TEXT"
            ))
            nav_url = build_navigation_link(
                address=address, village=village,
                lat=geo["lat"], lng=geo["lng"]
            )
            conn.execute(sqlt("""
                UPDATE patients
                SET latitude  = :lat,
                    longitude = :lng,
                    maps_url  = :url
                WHERE phone = :phone
            """), {
                "lat":   geo["lat"],
                "lng":   geo["lng"],
                "url":   nav_url,
                "phone": phone
            })
            conn.commit()
    except Exception as e:
        print(f"maps.py store patient coords error: {e}")

    return geo


def geocode_and_store_asha(asha_id: str, village: str, district: str = "") -> dict | None:
    """
    Geocode an ASHA worker's village and write lat/lng to the DB.
    Call this when adding a new ASHA worker in admin panel.
    """
    try:
        from database import engine
        from sqlalchemy import text as sqlt
    except ImportError:
        return None

    if not engine:
        return None

    geo = geocode_village(village, district=district)
    if not geo:
        return None

    try:
        with engine.connect() as conn:
            conn.execute(sqlt(
                "ALTER TABLE asha_workers ADD COLUMN IF NOT EXISTS latitude FLOAT"
            ))
            conn.execute(sqlt(
                "ALTER TABLE asha_workers ADD COLUMN IF NOT EXISTS longitude FLOAT"
            ))
            conn.execute(sqlt("""
                UPDATE asha_workers
                SET latitude  = :lat,
                    longitude = :lng
                WHERE asha_id = :id
            """), {"lat": geo["lat"], "lng": geo["lng"], "id": asha_id})
            conn.commit()
    except Exception as e:
        print(f"maps.py store ASHA coords error: {e}")

    return geo


# ─────────────────────────────────────────────────────────────────
# ALL-IN-ONE ALERT ENRICHMENT
# Called from app.py when a RED alert fires
# ─────────────────────────────────────────────────────────────────

def enrich_alert_with_maps(
    phone:   str,
    address: str,
    village: str
) -> dict:
    """
    Given a patient's address/village:
      1. Geocode to lat/lng (and store to DB)
      2. Build navigation link
      3. Build static map URL (for WhatsApp image)
      4. Find nearest health facility

    Returns a dict with all map data — always safe to call even
    if geocoding fails (returns empty strings in that case).
    """
    result = {
        "lat":           None,
        "lng":           None,
        "maps_link":     build_navigation_link(address=address, village=village),
        "static_map":    "",
        "nearest_phc":   None
    }

    geo = geocode_and_store_patient(phone, address, village)
    if geo:
        result["lat"]        = geo["lat"]
        result["lng"]        = geo["lng"]
        result["maps_link"]  = build_navigation_link(
            address=address, village=village,
            lat=geo["lat"], lng=geo["lng"]
        )
        result["static_map"] = build_static_map_url(
            lat=geo["lat"], lng=geo["lng"]
        )
        result["nearest_phc"] = find_nearest_health_facility(
            geo["lat"], geo["lng"]
        )

    return result


# ─────────────────────────────────────────────────────────────────
# VILLAGE RISK HEATMAP DATA  (Month 3 analytics)
# ─────────────────────────────────────────────────────────────────

def get_village_coords_map() -> dict:
    """
    Returns a dict of {village_name: {"lat": float, "lng": float}}
    by reading stored coordinates from the DB for all patients.

    Used by the admin analytics heatmap — no extra API calls needed
    because coords are already stored at registration.
    """
    result = {}
    try:
        from database import engine
        from sqlalchemy import text as sqlt
        if not engine:
            return result
        with engine.connect() as conn:
            rows = conn.execute(sqlt("""
                SELECT DISTINCT ON (village)
                    village, latitude, longitude
                FROM patients
                WHERE village IS NOT NULL
                  AND latitude IS NOT NULL
                  AND longitude IS NOT NULL
                ORDER BY village, created_at DESC
            """)).fetchall()
            for r in rows:
                if r.village:
                    result[r.village] = {
                        "lat": r.latitude,
                        "lng": r.longitude
                    }
    except Exception as e:
        print(f"maps.py get_village_coords_map error: {e}")
    return result


# ─────────────────────────────────────────────────────────────────
# QUICK SELF-TEST  (python maps.py)
# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== MaaSakhi maps.py self-test ===\n")

    test_village = "Rampur, Rajasthan"
    print(f"Geocoding: '{test_village}'")
    geo = geocode_village(test_village)
    if geo:
        print(f"  lat={geo['lat']}, lng={geo['lng']}")
        print(f"  Formatted: {geo['formatted']}")
        nav = build_navigation_link(lat=geo["lat"], lng=geo["lng"])
        print(f"  Nav link: {nav}")
        smap = build_static_map_url(lat=geo["lat"], lng=geo["lng"])
        print(f"  Static map URL: {smap[:80]}...")
        dist = haversine_distance(geo["lat"], geo["lng"], 26.9124, 75.7873)
        print(f"  Haversine to Jaipur: {dist:.1f} km")
    else:
        print("  Geocoding skipped (no API key or network error)")

    print("\nNavigation link (text-based fallback):")
    print(" ", build_navigation_link(address="Near Govt School, Ward 4, Rampur"))

    print("\nSelf-test complete.")