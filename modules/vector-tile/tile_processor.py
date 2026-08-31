"""
Vector Tile Telemetry Module
Parses telemetry logs data and structures spatial coordinate payloads.
"""
import json

def format_telemetry_vector(node_id, metric, status, coords=(0.0, 0.0)):
    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": list(coords)
        },
        "properties": {
            "node_id": node_id,
            "metric": metric,
            "status": status
        }
    }
