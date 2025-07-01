"""
Configuration for Hong Kong A&E Dashboard
Hospital locations, districts, and settings
"""

# Hospital configuration with coordinates and details
HOSPITAL_CONFIG = {
    "Alice Ho Miu Ling Nethersole Hospital": {
        "district": "New Territories",
        "region": "Tai Po",
        "coordinates": [22.4505, 114.1634],
        "cluster": "New Territories East"
    },
    "Caritas Medical Centre": {
        "district": "Kowloon",
        "region": "Sham Shui Po",
        "coordinates": [22.3406, 114.1533],
        "cluster": "Kowloon West"
    },
    "Kwong Wah Hospital": {
        "district": "Kowloon",
        "region": "Yau Tsim Mong",
        "coordinates": [22.3118, 114.1703],
        "cluster": "Kowloon Central"
    },
    "North District Hospital": {
        "district": "New Territories",
        "region": "North",
        "coordinates": [22.4969, 114.1289],
        "cluster": "New Territories East"
    },
    "North Lantau Hospital": {
        "district": "New Territories",
        "region": "Islands",
        "coordinates": [22.3289, 113.9436],
        "cluster": "New Territories West"
    },
    "Pamela Youde Nethersole Eastern Hospital": {
        "district": "Hong Kong Island",
        "region": "Chai Wan",
        "coordinates": [22.2615, 114.2374],
        "cluster": "Hong Kong East"
    },
    "Pok Oi Hospital": {
        "district": "New Territories",
        "region": "Yuen Long",
        "coordinates": [22.4455, 114.0378],
        "cluster": "New Territories West"
    },
    "Prince of Wales Hospital": {
        "district": "New Territories",
        "region": "Sha Tin",
        "coordinates": [22.3734, 114.2014],
        "cluster": "New Territories East"
    },
    "Princess Margaret Hospital": {
        "district": "Kowloon",
        "region": "Lai Chi Kok",
        "coordinates": [22.3387, 114.1463],
        "cluster": "Kowloon West"
    },
    "Queen Elizabeth Hospital": {
        "district": "Kowloon",
        "region": "Yau Tsim Mong",
        "coordinates": [22.3089, 114.1747],
        "cluster": "Kowloon Central"
    },
    "Queen Mary Hospital": {
        "district": "Hong Kong Island",
        "region": "Southern",
        "coordinates": [22.2693, 114.1347],
        "cluster": "Hong Kong West"
    },
    "Ruttonjee Hospital": {
        "district": "Hong Kong Island",
        "region": "Wan Chai",
        "coordinates": [22.2766, 114.1947],
        "cluster": "Hong Kong East"
    },
    "St John Hospital": {  # ← MISSING HOSPITAL ADDED
        "district": "Hong Kong Island",
        "region": "Central & Western",
        "coordinates": [22.2827, 114.1436],
        "cluster": "Hong Kong West"
    },
    "Tin Shui Wai Hospital": {
        "district": "New Territories",
        "region": "Yuen Long",
        "coordinates": [22.4583, 114.0075],
        "cluster": "New Territories West"
    },
    "Tseung Kwan O Hospital": {
        "district": "New Territories",
        "region": "Sai Kung",
        "coordinates": [22.3075, 114.2598],
        "cluster": "New Territories East"
    },
    "Tuen Mun Hospital": {
        "district": "New Territories",
        "region": "Tuen Mun",
        "coordinates": [22.4058, 113.9769],
        "cluster": "New Territories West"
    },
    "United Christian Hospital": {
        "district": "Kowloon",
        "region": "Kwun Tong",
        "coordinates": [22.3189, 114.2297],
        "cluster": "Kowloon East"
    },
    "Yan Chai Hospital": {
        "district": "New Territories",
        "region": "Tsuen Wan",
        "coordinates": [22.3675, 114.1089],
        "cluster": "New Territories West"
    }
}

# Color scheme for severity levels - Updated with better colors
SEVERITY_COLORS = {
    "low": "#00D4AA",      # Teal green
    "medium": "#FFB347",   # Orange
    "high": "#FF6B6B",     # Coral red
    "critical": "#DC143C"  # Crimson
}

# Enhanced color scheme for charts and visualizations
CHART_COLORS = {
    "primary": "#1f77b4",      # Blue
    "secondary": "#ff7f0e",    # Orange
    "success": "#2ca02c",      # Green
    "warning": "#d62728",      # Red
    "info": "#9467bd",         # Purple
    "light": "#8c564b",        # Brown
    "dark": "#e377c2",         # Pink
    "muted": "#7f7f7f"         # Gray
}

# Color palette for wait time categories
WAIT_TIME_COLORS = {
    "Under 1 hour": "#00D4AA",     # Teal green
    "1-2 hours": "#FFB347",        # Orange
    "2-3 hours": "#FF6B6B",        # Coral red
    "3-4 hours": "#DC143C",        # Crimson
    "Over 4 hours": "#8B0000",     # Dark red
    "30-60 minutes": "#00D4AA",    # Teal green
    "1 hour": "#FFB347",           # Orange
    "2 hours": "#FF6B6B",          # Coral red
    "90 minutes": "#FFB347",       # Orange
    "45 minutes": "#00D4AA",       # Teal green
    "2.5 hours": "#FF6B6B",        # Coral red
    "3.5 hours": "#DC143C",        # Crimson
    "Over 5 hours": "#8B0000"      # Dark red
}

# Map settings
MAP_CONFIG = {
    "center_lat": 22.3193,
    "center_lon": 114.1694,
    "zoom": 10,
    "height": 500
}

# Dashboard settings
DASHBOARD_CONFIG = {
    "refresh_interval": 900,  # 15 minutes
    "page_title": "Hong Kong A&E Wait Times",
    "page_icon": "🏥"
}

# Wait time categories for parsing and display - Updated with better colors
WAIT_TIME_CATEGORIES = {
    "Under 1 hour": {"numeric": 30, "color": "#00D4AA"},
    "1-2 hours": {"numeric": 90, "color": "#FFB347"},
    "2-3 hours": {"numeric": 150, "color": "#FF6B6B"},
    "3-4 hours": {"numeric": 210, "color": "#DC143C"},
    "Over 4 hours": {"numeric": 300, "color": "#8B0000"},
    "30-60 minutes": {"numeric": 45, "color": "#00D4AA"},
    "1 hour": {"numeric": 60, "color": "#FFB347"},
    "2 hours": {"numeric": 120, "color": "#FF6B6B"},
    "90 minutes": {"numeric": 90, "color": "#FFB347"},
    "45 minutes": {"numeric": 45, "color": "#00D4AA"},
    "2.5 hours": {"numeric": 150, "color": "#FF6B6B"},
    "3.5 hours": {"numeric": 210, "color": "#DC143C"},
    "Over 5 hours": {"numeric": 330, "color": "#8B0000"}
}

# Hospital regions for filtering
HOSPITAL_REGIONS = {
    "Hong Kong Island": [
        "Pamela Youde Nethersole Eastern Hospital",
        "Ruttonjee Hospital",
        "St John Hospital",
        "Queen Mary Hospital"
    ],
    "Kowloon": [
        "Kwong Wah Hospital",
        "Queen Elizabeth Hospital",
        "United Christian Hospital",
        "Caritas Medical Centre",
        "Princess Margaret Hospital",
        "Yan Chai Hospital"
    ],
    "New Territories": [
        "Alice Ho Miu Ling Nethersole Hospital",
        "North District Hospital",
        "Prince of Wales Hospital",
        "Pok Oi Hospital",
        "Tin Shui Wai Hospital",
        "Tuen Mun Hospital",
        "North Lantau Hospital",
        "Tseung Kwan O Hospital"
    ]
}

