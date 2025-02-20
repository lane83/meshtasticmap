#!/usr/bin/env python3
import meshtastic
from meshtastic.tcp_interface import TCPInterface
from pubsub import pub
import folium
import time
import sys
import signal
import logging
import json
from datetime import datetime

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

ENCRYPTED_CHANNEL = 1
CHANNEL_NAME = "Private"
HOST = "0.0.0.0"
PORT = 4403

interface = None
node_locations = {}
map_html = "node_map.html"

def signal_handler(sig, frame):
    logger.info("Shutting down gracefully...")
    if interface:
        interface.close()
    sys.exit(0)

def update_map():
    try:
        center_lat = 39.8283
        center_lon = -98.5795
        
        if node_locations:
            latest = list(node_locations.values())[-1]
            center_lat = latest['lat']
            center_lon = latest['lon']
        
        m = folium.Map(location=[center_lat, center_lon], zoom_start=4)
        
        for node_id, location in node_locations.items():
            folium.Marker(
                location=[location['lat'], location['lon']],
                popup=f"Node: {node_id}<br>Last Updated: {location['timestamp']}<br>Channel: {CHANNEL_NAME}",
                tooltip=f"Node {node_id}"
            ).add_to(m)
        
        m.save(map_html)
        logger.info(f"Map updated: {map_html}")
    except Exception as e:
        logger.error(f"Error updating map: {str(e)}")

def safe_json_dump(obj):
    """Convert packet to JSON-safe format"""
    if isinstance(obj, bytes):
        return obj.hex()
    if isinstance(obj, dict):
        return {k: safe_json_dump(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [safe_json_dump(i) for i in obj]
    return obj

def on_message(packet, interface):
    """Handle all incoming messages"""
    try:
        logger.debug(f"Raw packet received: {safe_json_dump(packet)}")
        
        if 'decoded' not in packet:
            return
            
        decoded = packet.get('decoded', {})
        portnum = str(decoded.get('portnum', ''))
        
        logger.debug(f"Message type (portnum): {portnum}")
        
        # Log all important packet fields
        logger.debug(f"Channel: {decoded.get('channel')}")
        logger.debug(f"From: {packet.get('fromId', packet.get('from', 'unknown'))}")
        logger.debug(f"To: {packet.get('toId', packet.get('to', 'unknown'))}")
        
        # Handle position data
        if 'position' in decoded:
            position = decoded['position']
            logger.info(f"Position data received: {position}")
            
            node_id = packet.get('fromId', packet.get('from', 'unknown'))
            lat = position.get('latitude')
            lon = position.get('longitude')
            
            if lat is not None and lon is not None:
                logger.info(f"Valid position: lat={lat}, lon={lon}")
                node_locations[node_id] = {
                    'lat': lat,
                    'lon': lon,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'channel': CHANNEL_NAME
                }
                update_map()
            else:
                logger.warning("Position data missing coordinates")
                
        elif 'user' in decoded:
            # Log user data for debugging
            logger.info(f"User data received: {decoded['user']}")
            
        elif 'telemetry' in decoded:
            # Log telemetry data for debugging
            logger.debug("Telemetry data received")
            
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        logger.error(f"Problem packet: {safe_json_dump(packet)}")

def main():
    global interface
    
    try:
        interface = TCPInterface(HOST)
        
        # Subscribe to all relevant message types
        pub.subscribe(on_message, "meshtastic.receive")
        pub.subscribe(on_message, "meshtastic.receive.position")
        pub.subscribe(on_message, "meshtastic.receive.user")
        pub.subscribe(on_message, "meshtastic.receive.text")
        
        logger.info(f"Connected to radio at {HOST}:{PORT}")
        logger.info(f"Tracking locations on channel {ENCRYPTED_CHANNEL} ({CHANNEL_NAME})")
        logger.info(f"Map will be saved to {map_html}")
        logger.info("Waiting for position messages...")
        
        # Create initial empty map
        update_map()
        
        while True:
            time.sleep(1)
            
    except ConnectionRefusedError:
        logger.error(f"Connection refused to {HOST}:{PORT}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
        if interface:
            interface.close()
        sys.exit(1)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    main()
