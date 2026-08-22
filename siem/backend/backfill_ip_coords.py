"""
Backfill script: fetch coordinates for existing IP intelligence records
that don't have latitude/longitude populated.
Run: python backfill_ip_coords.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import requests
import time
from datetime import datetime
from app import create_app
from app.database import db
from app.models.ip_intelligence import IPIntelligence

def backfill():
    app = create_app()
    with app.app_context():
        # Find public IPs without coordinates
        ips = IPIntelligence.query.filter(
            IPIntelligence.is_private == False,
            IPIntelligence.latitude.is_(None)
        ).all()

        print(f'[Backfill] Found {len(ips)} public IPs without coordinates')

        for ip_record in ips:
            try:
                resp = requests.get(
                    f'http://ip-api.com/json/{ip_record.ip_address}?fields=status,lat,lon,country,countryCode,regionName,city,isp,org,as,timezone',
                    timeout=3.0
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get('status') == 'success':
                        ip_record.latitude = data.get('lat')
                        ip_record.longitude = data.get('lon')
                        ip_record.country = data.get('country', ip_record.country)
                        ip_record.country_code = data.get('countryCode', ip_record.country_code)
                        ip_record.region = data.get('regionName', ip_record.region)
                        ip_record.city = data.get('city', ip_record.city)
                        ip_record.isp = data.get('isp', ip_record.isp)
                        ip_record.org = data.get('org', ip_record.org)
                        ip_record.asn = data.get('as', ip_record.asn)
                        ip_record.timezone = data.get('timezone', ip_record.timezone)
                        ip_record.raw_json = data
                        ip_record.updated_at = datetime.utcnow()
                        print(f'[Backfill] {ip_record.ip_address}: {ip_record.city}, {ip_record.country} ({ip_record.latitude}, {ip_record.longitude})')
                    else:
                        print(f'[Backfill] {ip_record.ip_address}: lookup failed ({data.get("message")})')
                time.sleep(0.5)  # Rate limit
            except Exception as e:
                print(f'[Backfill] {ip_record.ip_address}: error - {e}')

        db.session.commit()
        print(f'[Backfill] Done. Updated {len(ips)} records.')

if __name__ == '__main__':
    backfill()
