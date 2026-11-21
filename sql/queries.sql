-- 1. Incidents and escalation rate by region
SELECT c.region,
       COUNT(*) AS incidents,
       ROUND(100.0 * AVG(i.escalated), 1) AS pct_escalated
FROM incidents i
JOIN countries c ON c.country = i.country
GROUP BY c.region
ORDER BY incidents DESC;

-- 2. Exposure: incidents with the most travellers in the country at the time
SELECT i.incident_id, i.country, i.incident_date, i.incident_type, i.severity,
       COUNT(DISTINCT t.traveller_id) AS travellers_exposed
FROM incidents i
JOIN trips t
  ON t.country = i.country
 AND i.incident_date BETWEEN t.start_date AND t.end_date
GROUP BY i.incident_id
ORDER BY travellers_exposed DESC, i.severity DESC
LIMIT 10;

-- 3. Exposure by client: how many of each client's travellers were caught up in incidents?
SELECT tr.client,
       COUNT(*) AS exposures,
       COUNT(DISTINCT tr.traveller_id) AS travellers_affected,
       SUM(CASE WHEN i.severity >= 4 THEN 1 ELSE 0 END) AS high_severity_exposures
FROM incidents i
JOIN trips t
  ON t.country = i.country
 AND i.incident_date BETWEEN t.start_date AND t.end_date
JOIN travellers tr ON tr.traveller_id = t.traveller_id
GROUP BY tr.client
ORDER BY exposures DESC;

-- 4. Escalation rate by incident type
SELECT incident_type,
       COUNT(*) AS incidents,
       ROUND(100.0 * AVG(escalated), 1) AS pct_escalated
FROM incidents
GROUP BY incident_type
ORDER BY pct_escalated DESC;

-- 5. Escalation rate by severity
SELECT severity,
       COUNT(*) AS incidents,
       ROUND(100.0 * AVG(escalated), 1) AS pct_escalated
FROM incidents
GROUP BY severity
ORDER BY severity;

-- 6. Hotspots: countries with the most high-severity incidents (severity 4-5)
SELECT i.country, c.risk_level,
       COUNT(*) AS high_severity_incidents
FROM incidents i
JOIN countries c ON c.country = i.country
WHERE i.severity >= 4
GROUP BY i.country
ORDER BY high_severity_incidents DESC
LIMIT 10;

-- 7. How many incidents had no travellers exposed? (LEFT JOIN keeps incidents with no match)
SELECT CASE WHEN t.trip_id IS NULL THEN 'No travellers exposed'
            ELSE 'Travellers exposed' END AS exposure,
       COUNT(DISTINCT i.incident_id) AS incidents
FROM incidents i
LEFT JOIN trips t
  ON t.country = i.country
 AND i.incident_date BETWEEN t.start_date AND t.end_date
GROUP BY exposure;

-- 8. Data quality check: any rows with missing or impossible values?
SELECT
  (SELECT COUNT(*) FROM trips WHERE end_date < start_date OR country IS NULL) AS bad_trips,
  (SELECT COUNT(*) FROM incidents WHERE severity NOT BETWEEN 1 AND 5 OR country IS NULL) AS bad_incidents;