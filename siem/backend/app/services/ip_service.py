import ipaddress
import math
import requests
from datetime import datetime, timedelta
from app.database import db
from app.models.ip_intelligence import IPIntelligence

# Cache duration in hours
GEO_CACHE_HOURS = 24

def is_private_ip(ip_str):
    """Check if IP address is private, loopback, or local link."""
    try:
        ip_obj = ipaddress.ip_address(ip_str)
        return ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_str in ['127.0.0.1', 'localhost', '::1']
    except ValueError:
        return True

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate approximate distance in km between two geographic coordinates."""
    if not all([lat1, lon1, lat2, lon2]):
        return None
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))

def get_ip_intelligence(ip_address):
    """
    Retrieves or fetches cached IP geolocation intelligence.
    Handles private IPs, API errors, and caching gracefully.
    """
    if not ip_address or ip_address in ['unknown', 'None', '']:
        return {
            'ip_address': '0.0.0.0',
            'country': 'Unknown',
            'country_code': 'XX',
            'region': 'N/A',
            'city': 'N/A',
            'latitude': None,
            'longitude': None,
            'isp': 'N/A',
            'org': 'N/A',
            'asn': 'N/A',
            'timezone': 'N/A',
            'is_private': True,
            'is_malicious_flag': False
        }

    # 1. Check local DB cache
    cached = IPIntelligence.query.filter_by(ip_address=ip_address).first()
    if cached:
        if cached.updated_at and (datetime.utcnow() - cached.updated_at) < timedelta(hours=GEO_CACHE_HOURS):
            return cached.to_dict()

    # 2. Check if private / RFC 1918 / loopback
    if is_private_ip(ip_address):
        ip_info = cached or IPIntelligence(ip_address=ip_address)
        ip_info.country = 'Private Network'
        ip_info.country_code = 'PRIV'
        ip_info.region = 'Local Intranet'
        ip_info.city = 'Localhost / LAN'
        ip_info.latitude = None
        ip_info.longitude = None
        ip_info.isp = 'Internal Subnet'
        ip_info.org = 'Authorized Lab Network'
        ip_info.asn = 'N/A'
        ip_info.timezone = 'N/A'
        ip_info.is_private = True
        ip_info.is_malicious_flag = False
        ip_info.raw_json = {'type': 'private_ip'}
        ip_info.updated_at = datetime.utcnow()
        if not cached:
            db.session.add(ip_info)
        db.session.commit()
        return ip_info.to_dict()

    # 3. Public IP: External GeoIP Lookup
    try:
        response = requests.get(
            f'http://ip-api.com/json/{ip_address}?fields=status,message,country,countryCode,regionName,city,lat,lon,isp,org,as,query,timezone',
            timeout=3.0
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                ip_info = cached or IPIntelligence(ip_address=ip_address)
                ip_info.country = data.get('country', 'Unknown')
                ip_info.country_code = data.get('countryCode', 'XX')
                ip_info.region = data.get('regionName', 'Unknown')
                ip_info.city = data.get('city', 'Unknown')
                ip_info.latitude = data.get('lat')
                ip_info.longitude = data.get('lon')
                ip_info.isp = data.get('isp', 'Unknown')
                ip_info.org = data.get('org', 'Unknown')
                ip_info.asn = data.get('as', 'N/A')
                ip_info.timezone = data.get('timezone', 'N/A')
                ip_info.is_private = False
                ip_info.is_malicious_flag = False
                ip_info.raw_json = data
                ip_info.updated_at = datetime.utcnow()
                if not cached:
                    db.session.add(ip_info)
                db.session.commit()
                return ip_info.to_dict()
    except Exception as err:
        print(f"[IP Intelligence] External lookup failed for {ip_address}: {err}")

    # Fallback on API failure
    fallback = {
        'ip_address': ip_address,
        'country': 'Unavailable',
        'country_code': 'UN',
        'region': 'Unknown',
        'city': 'Unknown',
        'latitude': None,
        'longitude': None,
        'isp': 'Unknown',
        'org': 'Unknown',
        'asn': 'N/A',
        'timezone': 'N/A',
        'is_private': False,
        'is_malicious_flag': False
    }
    return fallback
