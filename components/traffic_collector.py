"""
Traffic data collection module for Hong Kong A&E Dashboard
Handles traffic conditions and route planning with Mapbox integration
"""

import requests
import streamlit as st
from typing import Dict, List, Tuple, Optional
import json
import random
import datetime
from geopy.geocoders import Nominatim
import time

# Try to import polyline, fallback if not available
try:
    import polyline
    POLYLINE_AVAILABLE = True
except ImportError:
    POLYLINE_AVAILABLE = False
    st.warning("⚠️ Polyline library not available. Route visualization will be limited.")

def get_traffic_data():
    """
    Get current traffic conditions
    Returns mock data for now - replace with real API later
    """
    
    traffic_points = [
        {
            'location': 'Central District', 
            'status': random.choice(['Light', 'Moderate', 'Heavy']),
            'details': 'Main business district - expect higher traffic during peak hours'
        },
        {
            'location': 'Causeway Bay', 
            'status': random.choice(['Light', 'Moderate', 'Heavy']),
            'details': 'Shopping area - congested on weekends'
        },
        {
            'location': 'Tsim Sha Tsui', 
            'status': random.choice(['Light', 'Moderate', 'Heavy']),
            'details': 'Tourist area - variable traffic conditions'
        },
        {
            'location': 'Mong Kok', 
            'status': random.choice(['Light', 'Moderate', 'Heavy']),
            'details': 'Dense urban area - frequently congested'
        },
        {
            'location': 'Wan Chai', 
            'status': random.choice(['Light', 'Moderate', 'Heavy']),
            'details': 'Mixed commercial/residential - moderate traffic'
        },
        {
            'location': 'Cross Harbour Tunnel', 
            'status': random.choice(['Moderate', 'Heavy', 'Severe']),
            'details': 'Major bottleneck - expect delays during peak hours'
        },
        {
            'location': 'Western Harbour Crossing', 
            'status': random.choice(['Light', 'Moderate', 'Heavy']),
            'details': 'Alternative tunnel route'
        },
        {
            'location': 'Tuen Mun Highway', 
            'status': random.choice(['Light', 'Moderate', 'Heavy']),
            'details': 'Major highway to New Territories'
        }
    ]
    
    return {
        'traffic_points': traffic_points,
        'last_updated': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
        'status': 'success',
        'data_source': 'Simulated Traffic Data'
    }

def get_route_info(start_location, end_location):
    """
    Get route information between two locations for emergency transport
    Essential for A&E dashboard route planning
    """
    
    # Calculate simulated realistic travel times based on Hong Kong geography
    base_time = random.randint(8, 35)
    base_distance = random.randint(3, 15)
    
    routes = [
        {
            'route_id': 1,
            'name': f'Express Route via {random.choice(["Central", "Admiralty", "Wan Chai"])}',
            'distance': f"{base_distance} km",
            'duration': f"{base_time} mins",
            'traffic_status': random.choice(['Light', 'Moderate', 'Heavy']),
            'toll_cost': f"HK${random.randint(5, 25)}" if random.choice([True, False]) else "Free",
            'description': f"Fastest route from {start_location} to {end_location}",
            'waypoints': [start_location, random.choice(['Central', 'Admiralty', 'Wan Chai']), end_location],
            'emergency_lane': True,
            'route_type': 'highway'
        },
        {
            'route_id': 2,
            'name': f'Alternative Route via {random.choice(["Causeway Bay", "North Point", "Quarry Bay"])}',
            'distance': f"{base_distance + random.randint(2, 8)} km",
            'duration': f"{base_time + random.randint(5, 15)} mins", 
            'traffic_status': random.choice(['Light', 'Moderate', 'Heavy']),
            'toll_cost': f"HK${random.randint(0, 15)}" if random.choice([True, False]) else "Free",
            'description': f"Secondary route avoiding main traffic",
            'waypoints': [start_location, random.choice(['Causeway Bay', 'North Point']), end_location],
            'emergency_lane': random.choice([True, False]),
            'route_type': 'surface'
        },
        {
            'route_id': 3,
            'name': 'Emergency Priority Route',
            'distance': f"{max(1, base_distance - 2)} km",
            'duration': f"{max(5, int(base_time * 0.7))} mins",
            'traffic_status': 'Priority',
            'toll_cost': "Free (Emergency)",
            'description': f"Dedicated emergency vehicle route with traffic priority",
            'waypoints': [start_location, 'Emergency Lane', end_location],
            'emergency_lane': True,
            'route_type': 'emergency'
        }
    ]
    
    return {
        'start_location': start_location,
        'end_location': end_location,
        'routes': routes,
        'total_routes': len(routes),
        'last_updated': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'status': 'success',
        'emergency_mode': True
    }


class TrafficRouteCollector:
    """
    Traffic Route Collector class for Hong Kong A&E Dashboard
    Handles real traffic data and route planning with Mapbox integration
    """
    
    def __init__(self, mapbox_token=None):
        """Initialize with Mapbox API token"""
        self.mapbox_token = mapbox_token or st.secrets.get("MAPBOX_TOKEN", "")
        self.geocoder = Nominatim(user_agent="hk_hospital_dashboard")
        
        # Hardcoded hospital coordinates for accurate routing
        self.hospital_locations = {
            "Pamela Youde Nethersole Eastern Hospital": {"lat": 22.26918, "lon": 114.23643},
            "Ruttonjee Hospital": {"lat": 22.275909, "lon": 114.17529},
            "St John Hospital": {"lat": 22.208059, "lon": 114.03151},
            "Queen Mary Hospital": {"lat": 22.2704, "lon": 114.13117},
            "Kwong Wah Hospital": {"lat": 22.31429, "lon": 114.1721},
            "Queen Elizabeth Hospital": {"lat": 22.30886, "lon": 114.17519},
            "Tseung Kwan O Hospital": {"lat": 22.317964, "lon": 114.27021},
            "United Christian Hospital": {"lat": 22.322291, "lon": 114.2279},
            "Caritas Medical Centre": {"lat": 22.340629, "lon": 114.15231},
            "North Lantau Hospital": {"lat": 22.282571, "lon": 113.93914},
            "Princess Margaret Hospital": {"lat": 22.340057, "lon": 114.1347},
            "Yan Chai Hospital": {"lat": 22.369548, "lon": 114.11956},
            "Alice Ho Miu Ling Nethersole Hospital": {"lat": 22.458696, "lon": 114.17479},
            "North District Hospital": {"lat": 22.496832, "lon": 114.12456},
            "Prince of Wales Hospital": {"lat": 22.379939, "lon": 114.20129},
            "Pok Oi Hospital": {"lat": 22.44523, "lon": 114.04159},
            "Tin Shui Wai Hospital": {"lat": 22.458704, "lon": 113.99585},
            "Tuen Mun Hospital": {"lat": 22.40708, "lon": 113.97621}
        }
        
    def geocode_location(self, location_name):
        """Convert location name to coordinates using Mapbox Geocoding API, fallback to Nominatim"""
        try:
            # Try Mapbox Geocoding API first
            url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{location_name}.json"
            params = {
                'access_token': self.mapbox_token,
                'country': 'HK',
                'limit': 1
            }
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('features'):
                    coordinates = data['features'][0]['geometry']['coordinates']
                    return [coordinates[1], coordinates[0]]  # [lat, lon]
            # Fallback to Nominatim if Mapbox fails
            location_query = f"{location_name}, Hong Kong"
            location = self.geocoder.geocode(location_query, timeout=10)
            if location:
                return [location.latitude, location.longitude]
            location = self.geocoder.geocode(location_name, timeout=10)
            if location:
                return [location.latitude, location.longitude]
            return None
        except Exception as e:
            return None
    
    def get_mapbox_route_with_traffic(self, start_coords, end_coords):
        """Get route with traffic data from Mapbox"""
        try:
            # Mapbox Directions API with traffic
            url = f"https://api.mapbox.com/directions/v5/mapbox/driving-traffic/{start_coords[1]},{start_coords[0]};{end_coords[1]},{end_coords[0]}"
            
            params = {
                'access_token': self.mapbox_token,
                'geometries': 'geojson',
                'annotations': 'duration,distance,speed',
                'overview': 'full',
                'steps': 'true',
                'alternatives': 'true',  # Get alternative routes
                'continue_straight': 'false'
            }
            
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except Exception as e:
            return None
    
    def calculate_traffic_condition(self, route):
        """Calculate traffic condition based on Mapbox's real-time traffic data"""
        try:
            # Get the legs data which contains traffic annotations
            legs = route.get('legs', [])
            if not legs:
                return "unknown", "⚪", "Traffic condition unknown"
            
            leg = legs[0]  # Use first leg
            
            # Get traffic annotations from Mapbox
            annotations = leg.get('annotation', {})
            duration_with_traffic = leg.get('duration', 0)  # Current duration with traffic
            distance = leg.get('distance', 0) / 1000  # km
            
            if distance <= 0:
                return "unknown", "⚪", "Traffic condition unknown"
            
            # Mapbox provides speed data in annotations
            # We can use this to determine if there's significant traffic impact
            speed_data = annotations.get('speed', [])
            
            if speed_data:
                # Calculate average speed from Mapbox data
                avg_speed = sum(speed_data) / len(speed_data) if speed_data else 0
                
                # Convert to km/h (Mapbox speed is in m/s)
                avg_speed_kmh = avg_speed * 3.6
                
                # Determine traffic condition based on actual speed vs expected
                if avg_speed_kmh >= 40:
                    return "smooth", "🟢", "Good traffic conditions"
                elif avg_speed_kmh >= 25:
                    return "moderate", "🟡", "Moderate traffic, allow extra time"
                elif avg_speed_kmh >= 15:
                    return "congested", "🟠", "Heavy traffic, significant delays"
                else:
                    return "jammed", "🔴", "Severe congestion, consider alternatives"
            
            # Fallback: Use duration comparison if speed data not available
            # Mapbox provides duration with and without traffic
            duration_no_traffic = annotations.get('duration', [duration_with_traffic])
            if isinstance(duration_no_traffic, list):
                duration_no_traffic = sum(duration_no_traffic) / len(duration_no_traffic)
            
            if duration_no_traffic > 0:
                traffic_ratio = duration_with_traffic / duration_no_traffic
                
                if traffic_ratio <= 1.1:
                    return "smooth", "🟢", "Good traffic conditions"
                elif traffic_ratio <= 1.3:
                    return "moderate", "🟡", "Moderate traffic, allow extra time"
                elif traffic_ratio <= 1.6:
                    return "congested", "🟠", "Heavy traffic, significant delays"
                else:
                    return "jammed", "🔴", "Severe congestion, consider alternatives"
            
            # If no traffic data available, assume moderate
            return "moderate", "🟡", "Traffic conditions unknown"
                
        except Exception as e:
            return "unknown", "⚪", "Traffic condition unknown"
    
    def decode_polyline_to_coords(self, geometry):
        """Convert GeoJSON geometry to coordinate list"""
        try:
            if geometry.get('type') == 'LineString':
                # GeoJSON coordinates are [lon, lat], we need [lat, lon]
                return [[coord[1], coord[0]] for coord in geometry['coordinates']]
            return []
        except Exception as e:
            return []
    
    def get_route_info(self, start_location: str, end_location: str):
        """Use the existing function for backward compatibility"""
        return get_route_info(start_location, end_location)
    
    def get_traffic_conditions(self, route_id: str = None):
        """Get current traffic conditions - FIXED METHOD NAME"""
        return get_traffic_data()
    
    def find_fastest_route_to_hospital(self, user_location: str, hospital_name: str):
        """Find fastest route to hospital using Mapbox Directions API if available"""
        try:
            # Geocode user location
            start_coords = self.geocode_location(user_location)
            
            # Use hardcoded hospital coordinates instead of geocoding
            hospital_coords = self.hospital_locations.get(hospital_name)
            if not start_coords or not hospital_coords:
                return None
            end_coords = [hospital_coords['lat'], hospital_coords['lon']]

            # Try Mapbox Directions API
            mapbox_data = self.get_mapbox_route_with_traffic(start_coords, end_coords)
            if mapbox_data and 'routes' in mapbox_data and len(mapbox_data['routes']) > 0:
                # Use the first (fastest) route
                main_route = mapbox_data['routes'][0]
                polyline_str = main_route['geometry']
                duration_sec = main_route['duration']
                distance_m = main_route['distance']
                summary = main_route.get('legs', [{}])[0].get('summary', '')
                traffic_condition, emoji, description = self.calculate_traffic_condition(main_route)
                return {
                    'user_location': user_location,
                    'hospital': hospital_name,
                    'fastest_route': {
                        'polyline': polyline_str,
                        'duration': f"{int(duration_sec // 60)} min",
                        'distance': f"{distance_m/1000:.1f} km",
                        'traffic_status': traffic_condition.title(),
                        'traffic_emoji': emoji,
                        'traffic_description': description,
                        'name': summary or 'Main Route',
                        'description': description,
                        'emergency_lane': False  # Not available from API
                    },
                    'all_routes': [
                        {
                            'polyline': r['geometry'],
                            'duration': f"{int(r['duration'] // 60)} min",
                            'distance': f"{r['distance']/1000:.1f} km",
                            'traffic_status': self.calculate_traffic_condition(r)[0].title(),
                            'traffic_emoji': self.calculate_traffic_condition(r)[1],
                            'traffic_description': self.calculate_traffic_condition(r)[2],
                            'name': r.get('legs', [{}])[0].get('summary', '') or f"Route {i+1}",
                            'description': self.calculate_traffic_condition(r)[2],
                            'emergency_lane': False
                        } for i, r in enumerate(mapbox_data['routes'])
                    ],
                    'traffic_conditions': None,
                    'estimated_arrival': f"{int(duration_sec // 60)} min",
                    'emergency_priority': False,
                    'last_updated': None
                }
            # Fallback to mock if Mapbox fails
            route_data = self.get_route_info(user_location, hospital_name)
            traffic_data = self.get_traffic_conditions()
            # Find the fastest route (Emergency Route has priority)
            fastest_route = None
            min_duration = float('inf')
            for route in route_data['routes']:
                duration_str = route['duration'].replace(' mins', '').strip()
                try:
                    duration = int(duration_str)
                except ValueError:
                    duration = 30  # Default fallback
                if route['traffic_status'] == 'Priority':
                    duration = int(duration * 0.7)
                if duration < min_duration:
                    min_duration = duration
                    fastest_route = route
            return {
                'user_location': user_location,
                'hospital': hospital_name,
                'fastest_route': fastest_route,
                'all_routes': route_data['routes'],
                'traffic_conditions': traffic_data,
                'estimated_arrival': f"{int(min_duration)} minutes",
                'emergency_priority': True,
                'last_updated': route_data['last_updated']
            }
        except Exception as e:
            return None
    
    def get_transport_options(self, user_location: str, hospital_name: str):
        """Get alternative transport options to hospital"""
        try:
            base_time = random.randint(15, 45)
            
            transport_options = [
                {
                    'type': 'taxi',
                    'name': 'Taxi (Red)',
                    'duration': f"{base_time} mins",
                    'cost': f"HK${random.randint(80, 200)}",
                    'availability': 'High',
                    'notes': 'Fastest option, available 24/7'
                },
                {
                    'type': 'taxi',
                    'name': 'Taxi (Green - NT)',
                    'duration': f"{base_time + 5} mins",
                    'cost': f"HK${random.randint(60, 150)}",
                    'availability': 'Medium',
                    'notes': 'For New Territories destinations'
                },
                {
                    'type': 'bus',
                    'name': 'Public Bus',
                    'duration': f"{base_time + 15} mins",
                    'cost': f"HK${random.randint(5, 15)}",
                    'availability': 'Schedule dependent',
                    'notes': 'Most economical option'
                },
                {
                    'type': 'mtr',
                    'name': 'MTR + Bus/Taxi',
                    'duration': f"{base_time + 10} mins",
                    'cost': f"HK${random.randint(20, 60)}",
                    'availability': 'High',
                    'notes': 'Reliable, may require transfers'
                }
            ]
            
            # Add ambulance option for emergencies
            if random.choice([True, False]):
                transport_options.insert(0, {
                    'type': 'ambulance',
                    'name': 'Emergency Ambulance',
                    'duration': f"{max(5, base_time - 10)} mins",
                    'cost': 'Free (Emergency)',
                    'availability': 'Emergency only',
                    'notes': 'Call 999 for life-threatening emergencies'
                })
            
            return transport_options
            
        except Exception as e:
            return []
    
    def get_traffic_alerts(self):
        """Get current traffic alerts and incidents"""
        try:
            # Simulate realistic Hong Kong traffic incidents
            incidents = []
            
            # Random incidents based on common Hong Kong traffic issues
            possible_incidents = [
                {
                    'location': 'Cross Harbour Tunnel',
                    'description': 'Heavy traffic due to peak hour congestion',
                    'severity': 'Medium',
                    'estimated_delay': '15-20 minutes'
                },
                {
                    'location': 'Island Eastern Corridor',
                    'description': 'Lane closure for maintenance work',
                    'severity': 'High',
                    'estimated_delay': '25-30 minutes'
                },
                {
                    'location': 'Tuen Mun Highway',
                    'description': 'Minor accident cleared, residual delays',
                    'severity': 'Low',
                    'estimated_delay': '5-10 minutes'
                },
                {
                    'location': 'Central District',
                    'description': 'Road closure for public event',
                    'severity': 'Medium',
                    'estimated_delay': '10-15 minutes'
                },
                {
                    'location': 'Western Harbour Crossing',
                    'description': 'Reduced capacity due to vehicle breakdown',
                    'severity': 'High',
                    'estimated_delay': '20-25 minutes'
                }
            ]
            
            # Randomly select 0-3 incidents
            num_incidents = random.randint(0, 3)
            incidents = random.sample(possible_incidents, min(num_incidents, len(possible_incidents)))
            
            return {
                'incidents': incidents,
                'total_incidents': len(incidents),
                'last_updated': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
                'status': 'active'
            }
            
        except Exception as e:
            return {'incidents': [], 'total_incidents': 0, 'status': 'error'}
    
    def get_hospital_accessibility(self, hospital_list):
        """Get accessibility for multiple hospitals"""
        
        accessibility_data = {}
        for hospital in hospital_list:
            accessibility_data[hospital] = {
                'average_travel_time': f"{random.randint(15, 45)} minutes",
                'traffic_rating': random.choice(['Excellent', 'Good', 'Fair', 'Poor']),
                'emergency_access': True,
                'parking_availability': f"{random.randint(20, 80)}%",
                'ambulance_priority': True,
                'wheelchair_accessible': True,
                'public_transport_access': random.choice(['Excellent', 'Good', 'Limited']),
                'last_updated': datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
            }
        
        return accessibility_data
    
    def get_emergency_routes(self, current_location: str):
        """Get all emergency routes from current location"""
        
        # Hong Kong major hospitals
        major_hospitals = [
            'Queen Mary Hospital',
            'Prince of Wales Hospital', 
            'Queen Elizabeth Hospital',
            'Tuen Mun Hospital',
            'United Christian Hospital',
            'Pamela Youde Nethersole Eastern Hospital'
        ]
        
        emergency_routes = []
        for hospital in major_hospitals:
            route_info = self.find_fastest_route_to_hospital(current_location, hospital)
            if route_info and route_info['fastest_route']:
                emergency_routes.append({
                    'hospital': hospital,
                    'fastest_time': route_info['estimated_arrival'],
                    'route_name': route_info['fastest_route']['name'],
                    'emergency_lane_available': route_info['fastest_route']['emergency_lane'],
                    'priority_status': 'HIGH',
                    'distance': route_info['fastest_route']['distance'],
                    'traffic_status': route_info['fastest_route']['traffic_status']
                })
        
        # Sort by fastest time
        try:
            emergency_routes.sort(key=lambda x: int(x['fastest_time'].replace(' minutes', '')))
        except:
            pass  # Keep original order if sorting fails
        
        return {
            'current_location': current_location,
            'emergency_routes': emergency_routes,
            'total_hospitals': len(emergency_routes),
            'nearest_hospital': emergency_routes[0] if emergency_routes else None,
            'status': 'emergency_ready',
            'last_updated': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def get_real_time_eta(self, user_location: str, hospital_name: str):
        """Get real-time ETA with traffic considerations"""
        try:
            route_info = self.find_fastest_route_to_hospital(user_location, hospital_name)
            if not route_info:
                return None
            
            fastest_route = route_info['fastest_route']
            base_time = int(fastest_route['duration'].replace(' mins', ''))
            
            # Apply traffic multipliers
            traffic_multipliers = {
                'Light': 1.0,
                'Moderate': 1.3,
                'Heavy': 1.6,
                'Severe': 2.0,
                'Priority': 0.7  # Emergency vehicles
            }
            
            traffic_status = fastest_route['traffic_status']
            multiplier = traffic_multipliers.get(traffic_status, 1.0)
            adjusted_time = int(base_time * multiplier)
            
            return {
                'hospital': hospital_name,
                'base_eta': f"{base_time} minutes",
                'traffic_adjusted_eta': f"{adjusted_time} minutes",
                'traffic_status': traffic_status,
                'confidence': 'High' if traffic_status != 'Severe' else 'Medium',
                'last_updated': datetime.datetime.now().strftime('%H:%M')
            }
            
        except Exception as e:
            return None
    
    def get_route_color(self, traffic_condition):
        """Get route color based on traffic condition"""
        # Normalize the traffic condition to lowercase for comparison
        condition = str(traffic_condition).lower()
        
        color_map = {
            "smooth": "#00D4AA",      # Green
            "light": "#00D4AA",       # Green (alternative name)
            "moderate": "#FFB347",    # Orange/Yellow
            "heavy": "#FF6B6B",       # Red
            "congested": "#FF6B6B",   # Red (alternative name)
            "jammed": "#8B0000",      # Dark Red
            "severe": "#8B0000",      # Dark Red (alternative name)
            "unknown": "#4575b4",     # Blue
            "priority": "#00D4AA"     # Green for emergency priority
        }
        return color_map.get(condition, "#4575b4")
