def calculate_transparent_risk_score(alert_data, ml_anomaly_score=0.0, ip_info=None, extra_factors=None):
    """
    Calculates a transparent composite risk score (0.0 to 100.0)
    and provides explicit factor breakdown showing why the score was assigned.
    """
    score = 0.0
    breakdown = []

    # 1. Base Severity Weighting (Weight: 25 pts)
    severity = alert_data.get('severity', 'MEDIUM').upper()
    if severity == 'CRITICAL':
        score += 35.0
        breakdown.append({'factor': 'Severity Rating (CRITICAL)', 'points': 35.0, 'detail': 'Critical alert classification assigned by detection engine.'})
    elif severity == 'HIGH':
        score += 25.0
        breakdown.append({'factor': 'Severity Rating (HIGH)', 'points': 25.0, 'detail': 'High severity threat rule triggered.'})
    elif severity == 'MEDIUM':
        score += 15.0
        breakdown.append({'factor': 'Severity Rating (MEDIUM)', 'points': 15.0, 'detail': 'Medium threat indicator detected.'})
    else:
        score += 5.0
        breakdown.append({'factor': 'Severity Rating (LOW)', 'points': 5.0, 'detail': 'Low priority security telemetry.'})

    # 2. Event Volume & Frequency Factor (Weight: up to 20 pts)
    evidence = alert_data.get('evidence', [])
    evt_count = len(evidence)
    if evt_count >= 10:
        score += 20.0
        breakdown.append({'factor': 'Event Burst Volume', 'points': 20.0, 'detail': f'Large burst of correlated events ({evt_count} events in evidence).'})
    elif evt_count >= 5:
        score += 12.0
        breakdown.append({'factor': 'Event Volume', 'points': 12.0, 'detail': f'Multiple correlated security events ({evt_count} events).'})
    elif evt_count > 1:
        score += 5.0
        breakdown.append({'factor': 'Repeated Activity', 'points': 5.0, 'detail': f'{evt_count} events correlated.'})

    # 3. Successful Login After Failure (Account Compromise Signal) (Weight: 20 pts)
    factors = alert_data.get('factors', {})
    if factors.get('compromise_flag') or 'Compromise' in alert_data.get('title', ''):
        score += 20.0
        breakdown.append({'factor': 'Post-Failure Authentication', 'points': 20.0, 'detail': 'Successful login immediately preceded by multiple failed authentication attempts.'})

    # 4. New / Unusual Source IP (Weight: 10 pts)
    if factors.get('is_new_source') or factors.get('new_ip'):
        score += 10.0
        breakdown.append({'factor': 'New Login Source', 'points': 10.0, 'detail': 'Source IP address not previously registered for this account.'})

    # 5. IP Intelligence / Location Risk (Weight: 10 pts)
    if ip_info:
        if ip_info.get('is_malicious_flag'):
            score += 15.0
            breakdown.append({'factor': 'Known Malicious IP Reputation', 'points': 15.0, 'detail': 'IP address flagged in threat intelligence feeds.'})
        elif not ip_info.get('is_private'):
            score += 5.0
            breakdown.append({'factor': 'Public Internet IP Source', 'points': 5.0, 'detail': f"External public IP source: {ip_info.get('country', 'Unknown Country')}"})

    # 6. ML Anomaly Score Integration (Weight: up to 20 pts)
    if ml_anomaly_score > 0.0:
        ml_pts = round(ml_anomaly_score * 20.0, 1)
        score += ml_pts
        breakdown.append({
            'factor': 'Machine Learning Anomaly Score',
            'points': ml_pts,
            'detail': f'Isolation Forest behavioral anomaly model output score: {round(ml_anomaly_score * 100, 1)}%'
        })

    # 7. Geographic Risk Factors (Weight: up to 15 pts)
    if extra_factors:
        if extra_factors.get('new_country'):
            score += 15.0
            breakdown.append({
                'factor': 'New Geographic Source',
                'points': 15.0,
                'detail': f'User authenticated from a new country: {extra_factors["new_country"]}'
            })
        if extra_factors.get('impossible_travel'):
            score += 10.0
            breakdown.append({
                'factor': 'Impossible Travel Detected',
                'points': 10.0,
                'detail': f'Physically implausible geographic movement: {extra_factors.get("speed_kmh", "?")} km/h'
            })
        if extra_factors.get('geo_country') and not extra_factors.get('new_country'):
            score += 3.0
            breakdown.append({
                'factor': 'Geographic Context',
                'points': 3.0,
                'detail': f'IP geolocation: {extra_factors.get("geo_city", "Unknown")}, {extra_factors["geo_country"]}'
            })

    final_score = round(min(100.0, max(0.0, score)), 1)

    reasoning_summary = {
        'final_risk_score': final_score,
        'risk_category': 'CRITICAL' if final_score >= 85 else ('HIGH' if final_score >= 65 else ('MEDIUM' if final_score >= 35 else 'LOW')),
        'breakdown': breakdown,
        'summary_text': f"Assigned composite risk score of {final_score}/100 based on {len(breakdown)} threat factors."
    }

    return final_score, reasoning_summary
