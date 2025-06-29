"""
A&E Data Collector
Fetches real-time emergency department waiting times from Hong Kong Hospital Authority
Enhanced with fallback data and better error handling
"""

import requests
import json
from datetime import datetime, timedelta
import re
import streamlit as st
import random
import time

class AEDataCollector:
    def __init__(self):
        self.base_url = "https://www.ha.org.hk/opendata/aed/aedwtdata-en.json"
        self.backup_url = "https://www.ha.org.hk/visitor/ha_visitor_index.asp?Content_ID=10045&Lang=ENG&Dimension=100&Parent_ID=10044"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache'
        })
        
        # Cache for storing last successful data
        self.last_successful_data = None
        self.last_fetch_time = None
        self.cache_duration = 300  # 5 minutes cache
        
        # Hospital mapping for consistency
        self.hospital_name_mapping = {
            'Pamela Youde Nethersole Eastern Hospital': 'Pamela Youde Nethersole Eastern Hospital',
            'Ruttonjee Hospital': 'Ruttonjee Hospital', 
            'St John Hospital': 'St John Hospital',
            'Queen Mary Hospital': 'Queen Mary Hospital',
            'Kwong Wah Hospital': 'Kwong Wah Hospital',
            'Queen Elizabeth Hospital': 'Queen Elizabeth Hospital',
            'Tseung Kwan O Hospital': 'Tseung Kwan O Hospital',
            'United Christian Hospital': 'United Christian Hospital',
            'Caritas Medical Centre': 'Caritas Medical Centre',
            'North Lantau Hospital': 'North Lantau Hospital',
            'Princess Margaret Hospital': 'Princess Margaret Hospital',
            'Yan Chai Hospital': 'Yan Chai Hospital',
            'Alice Ho Miu Ling Nethersole Hospital': 'Alice Ho Miu Ling Nethersole Hospital',
            'North District Hospital': 'North District Hospital',
            'Prince of Wales Hospital': 'Prince of Wales Hospital',
            'Pok Oi Hospital': 'Pok Oi Hospital',
            'Tin Shui Wai Hospital': 'Tin Shui Wai Hospital',
            'Tuen Mun Hospital': 'Tuen Mun Hospital'
        }
        
        # Dynamic hospital tracking
        self.new_hospitals_detected = set()
        self.hospital_change_log = []
    
    def is_cache_valid(self):
        """Check if cached data is still valid"""
        if not self.last_fetch_time or not self.last_successful_data:
            return False
        
        time_diff = datetime.now() - self.last_fetch_time
        return time_diff.total_seconds() < self.cache_duration
    
    def fetch_current_data(self):
        """Fetch current A&E waiting times with enhanced error handling"""
        
        # Return cached data if still valid
        if self.is_cache_valid():
            return self.last_successful_data
        
        try:
            # Add random delay to avoid rate limiting
            time.sleep(random.uniform(0.5, 1.5))
            
            response = self.session.get(self.base_url, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            # Validate data structure
            if self.validate_data_structure(data):
                # Detect new hospitals
                new_hospitals = self.detect_new_hospitals(data)
                if new_hospitals:
                    st.info(f"🏥 New hospitals detected: {', '.join(new_hospitals)}")
                
                self.last_successful_data = data
                self.last_fetch_time = datetime.now()
                return data
            else:
                st.warning("⚠️ Received invalid data structure from API")
                return self.get_fallback_data()
                
        except requests.exceptions.Timeout:
            st.warning("⏱️ Request timeout - using fallback data")
            return self.get_fallback_data()
            
        except requests.exceptions.ConnectionError:
            st.warning("🌐 Connection error - using fallback data")
            return self.get_fallback_data()
            
        except requests.exceptions.HTTPError as e:
            st.warning(f"🚫 HTTP error {e.response.status_code} - using fallback data")
            return self.get_fallback_data()
            
        except json.JSONDecodeError as e:
            st.warning("📄 Invalid JSON response - using fallback data")
            return self.get_fallback_data()
            
        except Exception as e:
            st.error(f"❌ Unexpected error: {str(e)}")
            return self.get_fallback_data()
    
    def validate_data_structure(self, data):
        """Validate that the API response has expected structure"""
        if not isinstance(data, dict):
            return False
        
        if 'waitTime' not in data:
            return False
            
        if not isinstance(data['waitTime'], list):
            return False
            
        # Check if at least one hospital has required fields
        # Handle both list format [hospital_name, wait_time] and dict format {'hospName': name, 'topWait': wait_time}
        for hospital in data['waitTime']:
            if isinstance(hospital, dict) and 'hospName' in hospital:
                return True
            elif isinstance(hospital, list) and len(hospital) >= 2:
                return True
                
        return False
    
    def get_fallback_data(self):
        """Generate realistic fallback data when API is unavailable"""
        
        # Return cached data if available
        if self.last_successful_data:
            return self.last_successful_data
        
        # Generate realistic simulated data
        hospitals = list(self.hospital_name_mapping.keys())
        wait_times = [
            "1-2 hours", "2-3 hours", "3-4 hours", "Over 4 hours",
            "30-60 minutes", "1 hour", "2 hours", "90 minutes",
            "45 minutes", "2.5 hours", "3.5 hours", "Over 5 hours"
        ]
        
        fallback_data = {
            'waitTime': [],
            'updateTime': datetime.now().strftime('%d/%m/%Y %H:%M'),
            'remark': 'Simulated data - API temporarily unavailable'
        }
        
        for hospital in hospitals:
            fallback_data['waitTime'].append({
                'hospName': hospital,
                'topWait': random.choice(wait_times),
                'remark': 'Estimated wait time'
            })
        
        return fallback_data
    
    def parse_wait_time(self, wait_text):
        """Parse wait time text to minutes with enhanced patterns"""
        if not wait_text or wait_text.lower().strip() in ['', 'n/a', 'not available', 'nil', '-']:
            return 0
        
        # Clean and normalize the text
        wait_text = wait_text.strip().lower()
        wait_text = re.sub(r'\s+', ' ', wait_text)  # Normalize whitespace
        
        # Handle "over X hours" format
        over_match = re.search(r'over\s+(\d+(?:\.\d+)?)\s+hours?', wait_text)
        if over_match:
            hours = float(over_match.group(1))
            return int(hours * 60 + 30)  # Add 30 minutes as conservative estimate
        
        # Handle "more than X hours" format
        more_than_match = re.search(r'more\s+than\s+(\d+(?:\.\d+)?)\s+hours?', wait_text)
        if more_than_match:
            hours = float(more_than_match.group(1))
            return int(hours * 60 + 15)
        
        # Handle "X-Y hours" format
        range_match = re.search(r'(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)\s+hours?', wait_text)
        if range_match:
            min_hours = float(range_match.group(1))
            max_hours = float(range_match.group(2))
            avg_hours = (min_hours + max_hours) / 2
            return int(avg_hours * 60)
        
        # Handle "X.Y hours" format (decimal hours)
        decimal_hours_match = re.search(r'(\d+\.\d+)\s+hours?', wait_text)
        if decimal_hours_match:
            hours = float(decimal_hours_match.group(1))
            return int(hours * 60)
        
        # Handle "X hours" format
        hours_match = re.search(r'(\d+)\s+hours?', wait_text)
        if hours_match:
            hours = int(hours_match.group(1))
            return hours * 60
        
        # Handle "X minutes" format
        minutes_match = re.search(r'(\d+)\s+minutes?', wait_text)
        if minutes_match:
            return int(minutes_match.group(1))
        
        # Handle "X hour Y minutes" format
        hour_min_match = re.search(r'(\d+)\s+hours?\s+(\d+)\s+minutes?', wait_text)
        if hour_min_match:
            hours = int(hour_min_match.group(1))
            minutes = int(hour_min_match.group(2))
            return hours * 60 + minutes
        
        # Handle "X mins" format
        mins_match = re.search(r'(\d+)\s+mins?', wait_text)
        if mins_match:
            return int(mins_match.group(1))
        
        # Handle "X hr" format
        hr_match = re.search(r'(\d+)\s+hrs?', wait_text)
        if hr_match:
            return int(hr_match.group(1)) * 60
        
        # Handle fractions like "1/2 hour", "1.5 hours"
        fraction_match = re.search(r'(\d+)/(\d+)\s+hours?', wait_text)
        if fraction_match:
            numerator = int(fraction_match.group(1))
            denominator = int(fraction_match.group(2))
            hours = numerator / denominator
            return int(hours * 60)
        
        # Default case - try to extract any number
        number_match = re.search(r'(\d+)', wait_text)
        if number_match:
            number = int(number_match.group(1))
            # Smart interpretation based on context
            if 'hour' in wait_text or number <= 12:
                return number * 60  # Assume hours
            elif 'min' in wait_text or number > 60:
                return number  # Assume minutes
            else:
                return number * 60  # Default to hours for ambiguous cases
        
        # If no pattern matches, return a default value
        return 120  # 2 hours default for unparseable wait times
    
    def get_severity_level(self, wait_minutes):
        """Categorize wait time severity with more granular levels"""
        if wait_minutes <= 30:
            return 'excellent'
        elif wait_minutes <= 60:
            return 'good'
        elif wait_minutes <= 120:
            return 'moderate'
        elif wait_minutes <= 180:
            return 'high'
        elif wait_minutes <= 300:
            return 'severe'
        else:
            return 'critical'
    
    def get_severity_color(self, severity):
        """Get color code for severity level"""
        colors = {
            'excellent': '#00C851',  # Green
            'good': '#39C0ED',       # Light Blue
            'moderate': '#ffbb33',   # Orange
            'high': '#FF8800',       # Dark Orange
            'severe': '#FF4444',     # Red
            'critical': '#CC0000'    # Dark Red
        }
        return colors.get(severity, '#666666')
    
    def get_severity_emoji(self, severity):
        """Get emoji for severity level"""
        emojis = {
            'excellent': '🟢',
            'good': '🔵', 
            'moderate': '🟡',
            'high': '🟠',
            'severe': '🔴',
            'critical': '⚫'
        }
        return emojis.get(severity, '⚪')
    
    def process_hospital_data(self, data):
        """Process raw API data into structured format with enhanced information"""
        if not data or 'waitTime' not in data:
            return []
        
        processed = []
        current_time = datetime.now()
        
        for hospital_data in data['waitTime']:
            hosp_name = hospital_data.get('hospName', '').strip()
            wait_text = hospital_data.get('topWait', '').strip()
            
            if hosp_name and wait_text:
                # Normalize hospital name
                normalized_name = self.hospital_name_mapping.get(hosp_name, hosp_name)
                
                # Check if this is a new hospital
                is_new_hospital = hosp_name not in self.hospital_name_mapping
                
                wait_minutes = self.parse_wait_time(wait_text)
                severity = self.get_severity_level(wait_minutes)
                
                # Calculate estimated service time
                estimated_service_time = current_time + timedelta(minutes=wait_minutes)
                
                # Get fallback data for new hospitals
                fallback_coords = self.get_fallback_coordinates(hosp_name) if is_new_hospital else None
                fallback_region = self.get_fallback_region(hosp_name) if is_new_hospital else None
                
                processed.append({
                    'hospital': normalized_name,
                    'original_name': hosp_name,  # Keep original name for reference
                    'wait_text': wait_text,
                    'wait_minutes': wait_minutes,
                    'wait_hours': round(wait_minutes / 60, 1),
                    'severity': severity,
                    'severity_color': self.get_severity_color(severity),
                    'severity_emoji': self.get_severity_emoji(severity),
                    'estimated_service_time': estimated_service_time.strftime('%H:%M'),
                    'last_updated': data.get('updateTime', 'Unknown'),
                    'data_source': 'HA Official' if 'remark' not in data else 'Estimated',
                    'remark': hospital_data.get('remark', ''),
                    'is_new_hospital': is_new_hospital,
                    'fallback_coordinates': fallback_coords,
                    'fallback_region': fallback_region
                })
        
        # Sort by wait time (shortest first)
        processed.sort(key=lambda x: x['wait_minutes'])
        
        return processed
    
    def get_statistics(self, processed_data):
        """Calculate statistics from processed hospital data"""
        if not processed_data:
            return {}
        
        wait_times = [h['wait_minutes'] for h in processed_data]
        
        return {
            'total_hospitals': len(processed_data),
            'average_wait': round(sum(wait_times) / len(wait_times), 1),
            'shortest_wait': min(wait_times),
            'longest_wait': max(wait_times),
            'median_wait': sorted(wait_times)[len(wait_times) // 2],
            'hospitals_under_1hr': len([w for w in wait_times if w <= 60]),
            'hospitals_over_3hr': len([w for w in wait_times if w > 180]),
            'severity_distribution': {
                severity: len([h for h in processed_data if h['severity'] == severity])
                for severity in ['excellent', 'good', 'moderate', 'high', 'severe', 'critical']
            }
        }
    
    def get_best_options(self, processed_data, limit=5):
        """Get hospitals with shortest wait times"""
        if not processed_data:
            return []
        
        # Already sorted by wait time in process_hospital_data
        return processed_data[:limit]
    
    def get_hospital_by_name(self, processed_data, hospital_name):
        """Get specific hospital data by name"""
        for hospital in processed_data:
            if hospital_name.lower() in hospital['hospital'].lower():
                return hospital
        return None
    
    def refresh_data(self):
        """Force refresh data (bypass cache)"""
        self.last_fetch_time = None
        self.last_successful_data = None
        return self.fetch_current_data()
    
    def get_data_freshness(self):
        """Get information about data freshness"""
        if not self.last_fetch_time:
            return "No data fetched yet"
        
        time_diff = datetime.now() - self.last_fetch_time
        minutes_ago = int(time_diff.total_seconds() / 60)
        
        if minutes_ago < 1:
            return "Just now"
        elif minutes_ago < 60:
            return f"{minutes_ago} minute{'s' if minutes_ago != 1 else ''} ago"
        else:
            hours_ago = int(minutes_ago / 60)
            return f"{hours_ago} hour{'s' if hours_ago != 1 else ''} ago"
    
    def detect_new_hospitals(self, api_data):
        """Detect new hospitals in API data that aren't in our mapping"""
        if not api_data or 'waitTime' not in api_data:
            return []
        
        new_hospitals = []
        for hospital_data in api_data['waitTime']:
            hosp_name = hospital_data.get('hospName', '').strip()
            if hosp_name and hosp_name not in self.hospital_name_mapping:
                new_hospitals.append(hosp_name)
                self.new_hospitals_detected.add(hosp_name)
                
                # Log the new hospital detection
                self.hospital_change_log.append({
                    'timestamp': datetime.now().isoformat(),
                    'type': 'new_hospital',
                    'hospital_name': hosp_name,
                    'action': 'detected'
                })
        
        return new_hospitals
    
    def get_fallback_coordinates(self, hospital_name):
        """Generate fallback coordinates for new hospitals based on name patterns"""
        # HK Island hospitals (typically in southern part)
        if any(keyword in hospital_name.lower() for keyword in ['eastern', 'ruttonjee', 'st john', 'queen mary']):
            return [22.2693, 114.1347]  # Central HK Island
        
        # Kowloon hospitals
        elif any(keyword in hospital_name.lower() for keyword in ['kwong wah', 'queen elizabeth', 'united christian', 'caritas', 'princess margaret', 'yan chai']):
            return [22.3118, 114.1703]  # Central Kowloon
        
        # New Territories hospitals
        elif any(keyword in hospital_name.lower() for keyword in ['alice ho', 'north district', 'prince of wales', 'pok oi', 'tin shui wai', 'tuen mun', 'north lantau', 'tseung kwan o']):
            return [22.3734, 114.2014]  # Central New Territories
        
        # Default to Hong Kong center
        else:
            return [22.3193, 114.1694]  # Hong Kong center
    
    def get_fallback_region(self, hospital_name):
        """Determine region for new hospitals based on name patterns"""
        # HK Island
        if any(keyword in hospital_name.lower() for keyword in ['eastern', 'ruttonjee', 'st john', 'queen mary']):
            return 'Hong Kong Island'
        
        # Kowloon
        elif any(keyword in hospital_name.lower() for keyword in ['kwong wah', 'queen elizabeth', 'united christian', 'caritas', 'princess margaret', 'yan chai']):
            return 'Kowloon'
        
        # New Territories
        elif any(keyword in hospital_name.lower() for keyword in ['alice ho', 'north district', 'prince of wales', 'pok oi', 'tin shui wai', 'tuen mun', 'north lantau', 'tseung kwan o']):
            return 'New Territories'
        
        # Default
        else:
            return 'Other'
    
    def get_hospital_changes_summary(self):
        """Get summary of hospital changes detected"""
        if not self.hospital_change_log:
            return None
        
        return {
            'new_hospitals': list(self.new_hospitals_detected),
            'total_changes': len(self.hospital_change_log),
            'last_change': self.hospital_change_log[-1] if self.hospital_change_log else None,
            'change_log': self.hospital_change_log[-10:]  # Last 10 changes
        }
    
    def generate_config_update(self, hospital_name):
        """Generate configuration snippet for a new hospital"""
        fallback_coords = self.get_fallback_coordinates(hospital_name)
        fallback_region = self.get_fallback_region(hospital_name)
        
        # Determine district based on region
        district_mapping = {
            'Hong Kong Island': 'Hong Kong Island',
            'Kowloon': 'Kowloon', 
            'New Territories': 'New Territories',
            'Other': 'Hong Kong Island'  # Default
        }
        
        district = district_mapping.get(fallback_region, 'Hong Kong Island')
        
        config_snippet = f'''    "{hospital_name}": {{
        "district": "{district}",
        "region": "Unknown",  # Update with actual region
        "coordinates": {fallback_coords},  # Update with actual coordinates
        "cluster": "{fallback_region}"
    }},'''
        
        return {
            'hospital_name': hospital_name,
            'config_snippet': config_snippet,
            'fallback_coordinates': fallback_coords,
            'fallback_region': fallback_region,
            'district': district,
            'instructions': f"""
            To add {hospital_name} to the system:
            
            1. Add the above config snippet to HOSPITAL_CONFIG in config.py
            2. Update the coordinates with the actual hospital location
            3. Update the region with the actual district/region
            4. Add the hospital to the appropriate HOSPITAL_REGIONS list
            5. Add the hospital to hospital_name_mapping in ae_collector.py
            """
        }
    
    def get_all_config_updates(self):
        """Get configuration updates for all new hospitals"""
        updates = []
        for hospital_name in self.new_hospitals_detected:
            updates.append(self.generate_config_update(hospital_name))
        return updates
