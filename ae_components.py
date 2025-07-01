"""
A&E Dashboard Components
Reusable components for the dashboard with REAL DATA INTEGRATION
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import folium
from streamlit_folium import st_folium
import requests
from datetime import datetime
import polyline
import numpy as np
import re
import os
import glob
import json

# Import from root directory (where streamlit runs from)
from config import WAIT_TIME_CATEGORIES, HOSPITAL_REGIONS, WAIT_TIME_COLORS, CHART_COLORS
from components.traffic_collector import TrafficRouteCollector
from ae_collector import AEDataCollector

def inject_sidebar_style():
    st.markdown(
        """
        <style>
        section[data-testid="stSidebar"] .st-expander > summary {
            font-weight: bold !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def display_sidebar_how_to_use():
    """Display the general How to Use section in the sidebar."""
    with st.sidebar.expander("How to Use", expanded=False):
        st.markdown("""
        ### Real-time waiting times update and route conditions
        
        **What is this data?**
        Real-time waiting time estimates for Emergency Departments 
        across all Hong Kong public hospitals, updated every 15 minutes by the Hospital Authority.
        
        **How to use this dashboard:**
        
        - **Hospital Rankings and Map Location:**
            - View all hospitals ranked by wait time
            - Use controls to sort/filter by wait time, region, or range
            - Click any hospital to highlight it on the map
            - Map shows hospital locations with color-coded wait times
            - Hover over map markers for wait time info
        - **Route Planning to Selected Hospital:**
            - Select a hospital to plan your route
            - Enter your location (e.g., Central, Tsim Sha Tsui)
            - View fastest route with traffic conditions
            - See estimated travel time, distance, and traffic status
            - Expand 'All Available Routes' for alternatives
        
        **Important Notes:**
        - These are estimates for non-urgent cases (triage categories 4-5)
        - Emergency cases are always prioritized
        - Data is provided by Hospital Authority for public reference
        
        **Data Source:** Hospital Authority | **Update Frequency:** Every 15 minutes
        """)

def display_sidebar_info():
    """Display the Hospital Information help section in the sidebar."""
    with st.sidebar.expander("**Hospital Information**", expanded=False):
        st.markdown("""
        ### How to use the Hospital Information section
        
        - **Search:** Use the search bar to find hospitals by name, address, or location (e.g., 'chai wan', 'queen mary', 'pok fu lam').
        - **Details:** View full hospital details including address and telephone number.
        - **Selection:** When you select a hospital from the map or chart, its details are highlighted and shown at the top of this section.
        - **Browse:** Expand the list below the search bar to browse all hospitals.
        
        _This section helps you quickly find and contact any public hospital in Hong Kong._
        """)

def display_last_update(data):
    """Display last update time with refresh status"""
    if not data:
        st.error("❌ No data available")
        return
    
    update_time = data.get('updateTime', 'Unknown')
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.metric("⏰ Last Updated", update_time)
    
    with col2:
        st.metric("🔄 Update Frequency", "Every 15 mins")
    
    with col3:
        if st.button("🔄 Refresh Data", key="refresh_data_btn_main"):
            st.cache_data.clear()  # Clear cache to force refresh
            st.rerun()

def display_sidebar_historical_wait_time():
    """Display a sidebar section for historical wait time info."""
    with st.sidebar.expander("Historical Wait Time", expanded=False):
        st.markdown("""
        View and compare the historical A&E wait time trends for all public hospitals in Hong Kong. Use the chart at the bottom of the dashboard to analyze patterns and select specific hospitals to focus on.
        """)

def create_ranking_controls():
    """Create sorting and filtering controls"""
    st.subheader("⚙️ Display Controls")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        sort_option = st.selectbox(
            "📊 Sort Hospitals By:",
            [
                "Shortest Wait First",
                "Longest Wait First", 
                "Hospital Name (A-Z)",
                "Hospital Name (Z-A)"
            ],
            key="sort_option_select"
        )
    
    with col2:
        region_filter = st.multiselect(
            "🗺️ Filter Hospital by Region:",
            list(HOSPITAL_REGIONS.keys()),
            default=list(HOSPITAL_REGIONS.keys()),
            key="region_filter_multiselect"
        )
    
    with col3:
        wait_filter = st.selectbox(
            "⏱️ Show Waiting Times:",
            [
                "All Wait Times",
                "Under 2 Hours Only", 
                "2-4 Hours Only",
                "Over 4 Hours Only"
            ],
            key="wait_filter_select"
        )
    
    return sort_option, region_filter, wait_filter

def get_hospital_region(hospital_name):
    """Get region for a hospital"""
    for region, hospitals in HOSPITAL_REGIONS.items():
        if hospital_name in hospitals:
            return region
    return "Other"

def apply_wait_time_filter(df, wait_filter):
    """Apply wait time filter to dataframe"""
    if wait_filter == "Under 2 Hours Only":
        return df[df['wait_hours'] < 2]
    elif wait_filter == "2-4 Hours Only":
        return df[(df['wait_hours'] >= 2) & (df['wait_hours'] <= 4)]
    elif wait_filter == "Over 4 Hours Only":
        return df[df['wait_hours'] > 4]
    else:
        return df

def apply_sorting(df, sort_option):
    """Apply sorting to dataframe"""
    if sort_option == "Shortest Wait First":
        return df.sort_values('wait_numeric')
    elif sort_option == "Longest Wait First":
        return df.sort_values('wait_numeric', ascending=False)
    elif sort_option == "Hospital Name (A-Z)":
        return df.sort_values('hospital_name')
    elif sort_option == "Hospital Name (Z-A)":
        return df.sort_values('hospital_name', ascending=False)
    else:
        return df

def parse_wait_time_to_hours(wait_time):
    """Parse wait time string to a numeric value in hours and a normalized label."""
    if not wait_time:
        return ("Unknown", np.nan)
    s = wait_time.lower().strip()
    # Handle 'Over X hours'
    over_match = re.search(r'over\s*(\d+(?:\.\d+)?)\s*hours?', s)
    if over_match:
        hours = float(over_match.group(1))
        return (f"Over {int(hours)} hours", hours)
    # Handle 'Around X hour(s)' or 'About X hour(s)'
    around_match = re.search(r'(around|about)\s*(\d+(?:\.\d+)?)\s*hours?', s)
    if around_match:
        hours = float(around_match.group(2))
        return (f"Around {int(hours)} hour", hours)
    # Handle 'X-Y hours'
    range_match = re.search(r'(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)\s*hours?', s)
    if range_match:
        min_h = float(range_match.group(1))
        max_h = float(range_match.group(2))
        avg_h = (min_h + max_h) / 2
        return (f"{min_h}-{max_h} hours", avg_h)
    # Handle 'X hours'
    hours_match = re.search(r'(\d+(?:\.\d+)?)\s*hours?', s)
    if hours_match:
        hours = float(hours_match.group(1))
        return (f"{int(hours)} hours", hours)
    # Handle 'X minutes'
    minutes_match = re.search(r'(\d+)\s*minutes?', s)
    if minutes_match:
        mins = float(minutes_match.group(1))
        return (f"{int(mins)} minutes", mins / 60)
    # Handle 'X hour Y minutes'
    hour_min_match = re.search(r'(\d+)\s*hours?\s*(\d+)\s*minutes?', s)
    if hour_min_match:
        hours = float(hour_min_match.group(1))
        mins = float(hour_min_match.group(2))
        return (f"{int(hours)}h {int(mins)}m", hours + mins / 60)
    # Handle 'X mins'
    mins_match = re.search(r'(\d+)\s*mins?', s)
    if mins_match:
        mins = float(mins_match.group(1))
        return (f"{int(mins)} minutes", mins / 60)
    # Fallback: try to extract any number
    number_match = re.search(r'(\d+)', s)
    if number_match:
        number = float(number_match.group(1))
        if 'hour' in s or number <= 12:
            return (f"{int(number)} hours", number)
        elif 'min' in s or number > 60:
            return (f"{int(number)} minutes", number / 60)
        else:
            return (f"{int(number)} hours", number)
    return ("Unknown", np.nan)

def parse_wait_time_to_minutes(wait_time):
    """Convert wait time string to minutes (for trend chart)."""
    if not wait_time:
        return None
    s = wait_time.lower().strip()
    # Over X hours
    m = re.search(r'over\s*(\d+(?:\.\d+)?)\s*hours?', s)
    if m:
        return int(float(m.group(1)) * 60 + 1)
    # Around X hour(s)
    m = re.search(r'(around|about)\s*(\d+(?:\.\d+)?)\s*hours?', s)
    if m:
        return int(float(m.group(2)) * 60)
    # X-Y hours
    m = re.search(r'(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)\s*hours?', s)
    if m:
        min_h = float(m.group(1))
        max_h = float(m.group(2))
        return int((min_h + max_h) / 2 * 60)
    # X hours
    m = re.search(r'(\d+(?:\.\d+)?)\s*hours?', s)
    if m:
        return int(float(m.group(1)) * 60)
    # X minutes
    m = re.search(r'(\d+)\s*minutes?', s)
    if m:
        return int(m.group(1))
    # X hour Y minutes
    m = re.search(r'(\d+)\s*hours?\s*(\d+)\s*minutes?', s)
    if m:
        return int(m.group(1)) * 60 + int(m.group(2))
    # X mins
    m = re.search(r'(\d+)\s*mins?', s)
    if m:
        return int(m.group(1))
    # Fallback: any number
    m = re.search(r'(\d+)', s)
    if m:
        n = int(m.group(1))
        if 'hour' in s or n <= 12:
            return n * 60
        elif 'min' in s or n > 60:
            return n
        else:
            return n * 60
    return None

def create_hospital_ranking_chart(data, sort_option, region_filter, wait_filter):
    """Create the main ranking chart with hospital selection buttons"""
    if not data or 'waitTime' not in data:
        st.error("No hospital data available")
        return None
    # Convert to DataFrame - ENHANCED DATA PARSING
    df_data = []
    for hospital_data in data['waitTime']:
        if isinstance(hospital_data, list) and len(hospital_data) >= 2:
            hospital_name = hospital_data[0]
            wait_time = hospital_data[1]
            df_data.append({'hospital_name': hospital_name, 'wait_time': wait_time})
        elif isinstance(hospital_data, dict):
            hospital_name = hospital_data.get('hospName', '')
            wait_time = hospital_data.get('topWait', '')
            if hospital_name and wait_time:
                df_data.append({'hospital_name': hospital_name, 'wait_time': wait_time})
        else:
            continue
    if not df_data:
        st.error("No valid hospital data found")
        return None
    df = pd.DataFrame(df_data)
    # Parse wait time to hours and normalized label
    df[['wait_time_norm', 'wait_hours']] = df['wait_time'].apply(lambda x: pd.Series(parse_wait_time_to_hours(x)))
    # Add numeric values for sorting
    def get_numeric_value(wait_time_norm):
        return WAIT_TIME_CATEGORIES.get(wait_time_norm, {}).get('numeric', 999)
    df['wait_numeric'] = df['wait_time_norm'].apply(get_numeric_value)
    # Add colors with fallback protection - Updated with better colors
    def get_color(wait_time_norm):
        return WAIT_TIME_COLORS.get(wait_time_norm, '#7f7f7f')
    df['color'] = df['wait_time_norm'].apply(get_color)
    # Add regions
    df['region'] = df['hospital_name'].apply(get_hospital_region)
    # Apply filters
    if region_filter:
        df = df[df['region'].isin(region_filter)]
    if wait_filter != "All Wait Times":
        df = apply_wait_time_filter(df, wait_filter)
    # Apply sorting
    if sort_option == "Shortest Wait First":
        df = df.sort_values('wait_hours')
    elif sort_option == "Longest Wait First":
        df = df.sort_values('wait_hours', ascending=False)
    else:
        df = df.sort_values('hospital_name')
    if df.empty:
        st.warning("No hospitals match the selected filters")
        return None
    selected_hospital = st.session_state.get('selected_hospital', None)
    # Use a continuous color scale for bars
    color_scale = px.colors.sequential.YlOrRd
    min_wait = df['wait_hours'].min()
    max_wait = df['wait_hours'].max()
    def get_bar_color(hours):
        if np.isnan(hours):
            return '#4575b4'  # Blue for unknown
        # Align with map legend colors
        if hours <= 1:
            return '#1a9850'  # Green - short wait (≤ 1 hour)
        elif hours <= 2:
            return '#fee08b'  # Yellow - medium wait (1-2 hours)
        elif hours <= 4:
            return '#fd8d3c'  # Orange - long wait (2-4 hours)
        else:
            return '#d73027'  # Red - very long wait (> 4 hours)
    bar_colors = [get_bar_color(h) for h in df['wait_hours']]
    bar_opacity = [1.0 if row['hospital_name'] == selected_hospital else 0.85 for _, row in df.iterrows()]
    bar_line_colors = ['#FF6B35' if row['hospital_name'] == selected_hospital else 'white' for _, row in df.iterrows()]
    bar_line_widths = [3 if row['hospital_name'] == selected_hospital else 1 for _, row in df.iterrows()]
    fig = go.Figure(go.Bar(
        y=df['hospital_name'],
        x=df['wait_hours'],
        orientation='h',
        marker=dict(
            color=bar_colors,
            opacity=bar_opacity,
            line=dict(
                color=bar_line_colors,
                width=bar_line_widths
            )
        ),
        text=df['wait_time'],
        textposition='inside',
        insidetextanchor='middle',
        textfont=dict(color='white', size=14),
        hovertemplate='<b>%{y}</b><br>Wait Time: %{text}<br>Region: %{customdata}<extra></extra>',
        customdata=df['region']
    ))
    fig.update_layout(
        xaxis_title="Estimated Wait Time (Hours)",
        yaxis_title="Hospital",
        height=max(400, len(df) * 25),
        showlegend=False,
        margin=dict(l=0, r=0, t=60, b=0),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Arial, sans-serif")
    )
    fig.update_xaxes(
        gridcolor='rgba(128,128,128,0.2)',
        zerolinecolor='rgba(128,128,128,0.5)',
        title_font=dict(size=14, color='#34495e')
    )
    fig.update_yaxes(
        gridcolor='rgba(128,128,128,0.2)',
        title_font=dict(size=14, color='#34495e')
    )
    st.plotly_chart(fig, use_container_width=True, key="hospital_chart")
    st.markdown("**🎯 Click to Highlight Hospital on Map:**")
    num_hospitals = len(df)
    cols_per_row = 2
    for i in range(0, num_hospitals, cols_per_row):
        cols = st.columns(cols_per_row)
        for j in range(cols_per_row):
            idx = i + j
            if idx < num_hospitals:
                hospital_row = df.iloc[idx]
                hospital_name = hospital_row['hospital_name']
                wait_time = hospital_row['wait_time']
                region = hospital_row['region']
                is_selected = hospital_name == selected_hospital
                with cols[j]:
                    button_emoji = "📍 ✅" if is_selected else "📍"
                    button_label = f"{button_emoji} {hospital_name}"
                    if st.button(
                        button_label, 
                        key=f"select_hospital_{idx}_{hospital_name.replace(' ', '_')}", 
                        help=f"{hospital_name}\nWait: {wait_time} | Region: {region}",
                        type="primary" if is_selected else "secondary"
                    ):
                        if st.session_state.get('selected_hospital') == hospital_name:
                            st.session_state['selected_hospital'] = None
                        else:
                            st.session_state['selected_hospital'] = hospital_name
                        st.rerun()
    if selected_hospital:
        selected_info = df[df['hospital_name'] == selected_hospital]
        if not selected_info.empty:
            hospital_data = selected_info.iloc[0]
            st.success(f"📍 **Selected:** {selected_hospital} | **Wait:** {hospital_data['wait_time']} | **Region:** {hospital_data['region']}")
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("🔄 Clear Selection", type="secondary", key="clear_hospital_selection"):
                    st.session_state['selected_hospital'] = None
                    st.rerun()
    else:
        st.info("💡 Click any hospital button above to highlight it on the map →")
    return df

def create_hospital_map(df, selected_hospital=None):
    """Create simple hospital location map with Folium, style selection, and improved markers"""
    hospital_locations = {
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
    if df is None or df.empty:
        st.warning("No hospital data available for mapping")
        return
    # Map style selection
    style_options = {
        "Minimal": "CartoDB positron",
        "Street": "OpenStreetMap",
        "Dark": "CartoDB dark_matter"
    }
    map_style = st.selectbox(
        "🎨 Map Style:",
        list(style_options.keys()),
        index=0,
        key="hospital_map_style_selector"
    )
    tile_layer = style_options[map_style]
    # Center map on Hong Kong
    center_lat, center_lon = 22.35, 114.15
    m = folium.Map(location=[center_lat, center_lon], zoom_start=11, control_scale=True, tiles=None)
    folium.TileLayer(tile_layer, name=map_style, control=False).add_to(m)
    # Color scale for wait times
    def get_marker_color(wait_time):
        wait_str = str(wait_time).lower().strip()
        
        # Extract numeric value from wait time string
        import re
        
        # Handle "Over X hours" format
        over_match = re.search(r'over\s+(\d+(?:\.\d+)?)\s+hours?', wait_str)
        if over_match:
            hours = float(over_match.group(1))
            if hours <= 1:
                return "#1a9850"  # green - short wait
            elif hours <= 2:
                return "#fee08b"  # yellow - medium wait
            elif hours <= 4:
                return "#fd8d3c"  # orange - long wait
            else:
                return "#d73027"  # red - very long wait
        
        # Handle "Around X hour" format
        around_match = re.search(r'around\s+(\d+(?:\.\d+)?)\s+hours?', wait_str)
        if around_match:
            hours = float(around_match.group(1))
            if hours <= 1:
                return "#1a9850"  # green - short wait
            elif hours <= 2:
                return "#fee08b"  # yellow - medium wait
            elif hours <= 4:
                return "#fd8d3c"  # orange - long wait
            else:
                return "#d73027"  # red - very long wait
        
        # Handle "X hours" format
        hours_match = re.search(r'(\d+(?:\.\d+)?)\s+hours?', wait_str)
        if hours_match:
            hours = float(hours_match.group(1))
            if hours <= 1:
                return "#1a9850"  # green - short wait
            elif hours <= 2:
                return "#fee08b"  # yellow - medium wait
            elif hours <= 4:
                return "#fd8d3c"  # orange - long wait
            else:
                return "#d73027"  # red - very long wait
        
        # Default for unknown formats
        return "#4575b4"  # blue - unknown
    # Add hospital markers as CircleMarker
    for _, row in df.iterrows():
        name = row['hospital_name']
        wait_time = row['wait_time']
        color = get_marker_color(wait_time)
        lat = hospital_locations.get(name, {}).get('lat')
        lon = hospital_locations.get(name, {}).get('lon')
        
        # Check if this is a new hospital with fallback coordinates
        if lat is None and 'fallback_coordinates' in row and row['fallback_coordinates']:
            lat, lon = row['fallback_coordinates']
        
        if lat is None or lon is None:
            continue
            
        is_selected = (name == selected_hospital)
        is_new_hospital = row.get('is_new_hospital', False)
        
        # Use different styling for new hospitals
        if is_new_hospital:
            # New hospital - use normal CircleMarker with estimated location note
            folium.CircleMarker(
                location=[lat, lon],
                radius=12 if is_selected else 8,
                color="#8B008B" if is_selected else color,
                fill=True,
                fill_color=color,
                fill_opacity=0.9 if is_selected else 0.7,
                weight=4 if is_selected else 2,
                popup=folium.Popup(f"<b>🆕 {name}</b><br>Wait: {wait_time}<br><i>Estimated Location</i>", max_width=250),
                tooltip=f"{name} ({wait_time}) - New Hospital"
            ).add_to(m)
        else:
            # Existing hospital - normal CircleMarker
            folium.CircleMarker(
                location=[lat, lon],
                radius=12 if is_selected else 8,
                color="#8B008B" if is_selected else color,
                fill=True,
                fill_color=color,
                fill_opacity=0.9 if is_selected else 0.7,
                weight=4 if is_selected else 2,
                popup=folium.Popup(f"<b>{name}</b><br>Wait: {wait_time}", max_width=250),
                tooltip=f"{name} ({wait_time})"
            ).add_to(m)
    
    st_folium(m, width=700, height=500)
    # Map legend
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **🗺️ Map Legend:**
        - 🟢 **Green:** Short wait (≤ 1 hour)
        - 🟡 **Yellow:** Medium wait (1-2 hours)
        - 🟠 **Orange:** Long wait (2-4 hours)
        - 🔴 **Red:** Very long wait (> 4 hours)
        - 🔵 **Blue:** Unknown (No data provided)
        - 🟣 **Purple border:** Selected hospital
        
        Zoom in and out by scrolling or using the + / - buttons.
        """)
    with col2:
        if selected_hospital:
            st.markdown(f"**📍 Selected Hospital:** {selected_hospital}")
        else:
            st.markdown(f"**📍 Current View:** Showing {len(df)} hospitals")

def create_route_planning_map(df, selected_hospital=None):
    """Create interactive route planning map with Folium"""
    if not selected_hospital:
        st.info("💡 Select a hospital first to plan your route")
        return
    
    # Hospital locations dictionary (same as in create_hospital_map)
    hospital_locations = {
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
    
    st.markdown(f"### 🚗 Route Planning to {selected_hospital}")
    
    st.markdown(
        """
        <div style='background-color:#fff3cd; border-left:6px solid #ffe066; padding:10px; border-radius:6px; margin-bottom:8px;'>
        <b>📢 Tip:</b> Please input the <b>exact address, street name, building, or estate name</b> to search.<br>
        This helps avoid incorrect start points due to similar place names.
        </div>
        """,
        unsafe_allow_html=True
    )

    user_location = st.text_input(
        "📍 Your Current Location:",
        placeholder="e.g., Central, Tsim Sha Tsui, Causeway Bay",
        key=f"route_planning_location_{selected_hospital}"
    )
    
    if user_location:
        # Initialize traffic collector
        traffic_collector = TrafficRouteCollector()
        
        # Get route information
        with st.spinner("🔍 Finding best route..."):
            route_info = traffic_collector.find_fastest_route_to_hospital(user_location, selected_hospital)
        
        if route_info and 'fastest_route' in route_info and 'polyline' in route_info['fastest_route']:
            fastest_route = route_info['fastest_route']
            # Display route information
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("⏱️ Duration", fastest_route['duration'])
            with col2:
                st.metric("📏 Distance", fastest_route['distance'])
            with col3:
                st.metric("🚦 Traffic", f"{fastest_route.get('traffic_emoji', '')} {fastest_route['traffic_status']}")
            with col4:
                st.metric("💰 Cost", fastest_route.get('toll_cost', 'N/A'))
            st.markdown(f"""
            **Route Details:**
            - **Route:** {fastest_route['name']}
            - **Description:** {fastest_route['description']}
            - **Emergency Lane:** {'✅ Available' if fastest_route.get('emergency_lane', False) else '❌ Not Available'}
            """)
            try:
                coords = traffic_collector.decode_polyline_to_coords(fastest_route['polyline'])
                if not coords:
                    st.warning("Could not decode route polyline.")
                    return
                # Folium expects [lat, lon] pairs
                start_lat, start_lon = coords[0]
                # Use hardcoded hospital coordinates instead of route end coordinates
                hospital_coords = hospital_locations.get(selected_hospital)
                if not hospital_coords:
                    st.error(f"Could not find coordinates for {selected_hospital}")
                    return
                end_lat, end_lon = hospital_coords['lat'], hospital_coords['lon']
                # Center map between start and end
                center_lat = (start_lat + end_lat) / 2
                center_lon = (start_lon + end_lon) / 2
                
                # Map style selection for route map
                style_options = {
                    "Minimal": "CartoDB positron",
                    "Street": "OpenStreetMap",
                    "Dark": "CartoDB dark_matter"
                }
                map_style = st.selectbox(
                    "🎨 Route Map Style:",
                    list(style_options.keys()),
                    index=0,
                    key="route_map_style_selector"
                )
                tile_layer = style_options[map_style]
                
                m = folium.Map(location=[center_lat, center_lon], zoom_start=13, control_scale=True, tiles=None)
                folium.TileLayer(tile_layer, name=map_style, control=False).add_to(m)
                
                # Get route color based on traffic condition
                traffic_status = fastest_route.get('traffic_status', 'Unknown')
                route_color = traffic_collector.get_route_color(traffic_status)
                
                # Add route polyline with traffic-based color
                folium.PolyLine(coords, color=route_color, weight=6, opacity=0.8, popup=f"Route - {traffic_status}").add_to(m)
                # Add start marker
                folium.Marker(
                    location=[start_lat, start_lon],
                    popup=f"Start: {user_location}",
                    tooltip="Start",
                    icon=folium.Icon(color='green', icon='play')
                ).add_to(m)
                # Add hospital marker using hardcoded coordinates
                folium.Marker(
                    location=[end_lat, end_lon],
                    popup=f"Hospital: {selected_hospital}",
                    tooltip="Hospital",
                    icon=folium.Icon(color='red', icon='plus')
                ).add_to(m)
                # Display map and legend side by side
                map_col, legend_col = st.columns([4, 1])
                with map_col:
                    st.markdown("### 🗺️ Route Map")
                    st_folium(m, width=700, height=500)
                with legend_col:
                    st.markdown("""
                    <div style='border:1px solid #eee; border-radius:8px; padding:12px; margin-bottom:8px; background:#fafbfc;'>
                    <b>🗺️ Route Color Legend:</b><br>
                    <span style='color:#00D4AA;'>🟢 Green:</span> Smooth traffic (≥40 km/h)<br>
                    <span style='color:#FFB347;'>🟡 Yellow:</span> Moderate (25-40 km/h)<br>
                    <span style='color:#FF6B6B;'>🟠 Orange:</span> Heavy (15-25 km/h)<br>
                    <span style='color:#8B0000;'>🔴 Red:</span> Severe (<15 km/h)<br>
                    <span style='color:#4575b4;'>🔵 Blue:</span> Unknown
                    </div>
                    """, unsafe_allow_html=True)
                
                st.success(f"""
                **✅ Route Found!**
                - **From:** {user_location}
                - **To:** {selected_hospital}
                - **Route Type:** {fastest_route['name']}
                - **Estimated Time:** {fastest_route['duration']}
                - **Distance:** {fastest_route['distance']}
                - **Traffic:** {fastest_route.get('traffic_emoji', '')} {fastest_route['traffic_status']}
                """)
            except Exception as e:
                st.error(f"❌ Error creating route map: {str(e)}")
                st.info("💡 Try entering a different location or check your internet connection.")
            # Show all available routes
            with st.expander("🗺️ All Available Routes", expanded=False):
                for i, route in enumerate(route_info.get('all_routes', []), 1):
                    try:
                        coords = traffic_collector.decode_polyline_to_coords(route['polyline'])
                        if not coords:
                            continue
                        st.markdown(f"""
                        **Route {i}: {route['name']}**
                        - Distance: {route['distance']}
                        - Duration: {route['duration']}
                        - Traffic: {route.get('traffic_emoji', '')} {route['traffic_status']}
                        - Description: {route['description']}
                        """)
                    except Exception:
                        continue
        else:
            st.warning("❌ Unable to find route information. Please check the location name.")
            st.info("💡 Try entering a different location or check your internet connection.")

def create_summary_statistics(df):
    """Create summary statistics section with custom card layout and full name below"""
    if df is None or df.empty:
        return
    
    st.subheader("📊 Summary Statistics")
    
    def short_name(name):
        return name[:18] + "..." if len(name) > 18 else name
    
    shortest_wait = df.loc[df['wait_hours'].idxmin()]
    longest_wait = df.loc[df['wait_hours'].idxmax()]
    avg_wait = df['wait_hours'].mean()
    avg_hours = int(avg_wait)
    avg_mins = int((avg_wait - avg_hours) * 60)
    critical_count = len(df[df['wait_hours'] > 4])  # > 4 hours
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div style='border:1px solid #eee; border-radius:8px; padding:12px; margin-bottom:8px; background:#fafbfc;'>
            <div style='font-size:1.1rem; color:#388e3c; margin-bottom:2px;'>🟢 Shortest Wait</div>
            <div style='font-size:1.1rem; font-weight:bold; color:#222;'>{short_name(shortest_wait['hospital_name'])}</div>
            <div style='font-size:0.9rem; color:#888; margin-bottom:2px;'>{shortest_wait['hospital_name']}</div>
            <div style='font-size:1rem; color:#388e3c; margin-top:2px;'>{shortest_wait['wait_time']}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div style='border:1px solid #eee; border-radius:8px; padding:12px; margin-bottom:8px; background:#fafbfc;'>
            <div style='font-size:1.1rem; color:#d32f2f; margin-bottom:2px;'>🔴 Longest Wait</div>
            <div style='font-size:1.1rem; font-weight:bold; color:#222;'>{short_name(longest_wait['hospital_name'])}</div>
            <div style='font-size:0.9rem; color:#888; margin-bottom:2px;'>{longest_wait['hospital_name']}</div>
            <div style='font-size:1rem; color:#d32f2f; margin-top:2px;'>{longest_wait['wait_time']}</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div style='border:1px solid #eee; border-radius:8px; padding:12px; margin-bottom:8px; background:#fafbfc;'>
            <div style='font-size:1.1rem; color:#1976d2; margin-bottom:2px;'>Averagely to wait</div>
            <div style='font-size:1.3rem; font-weight:bold; color:#222;'>{avg_hours}h {avg_mins}m</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div style='border:1px solid #eee; border-radius:8px; padding:12px; margin-bottom:8px; background:#fafbfc;'>
            <div style='font-size:1.1rem; color:#ff9800; margin-bottom:2px;'>Hospitals with long wait (&gt;4h)</div>
            <div style='font-size:1.3rem; font-weight:bold; color:#222;'>{critical_count} hospitals</div>
        </div>
        """, unsafe_allow_html=True)

def load_hospital_static_info(filepath="hospital_static_info_template.txt"):
    """Load hospital static info from the template file into a list of dicts."""
    hospitals = []
    if not os.path.exists(filepath):
        return hospitals
    with open(filepath, "r", encoding="utf-8") as f:
        block = {}
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("name:"):
                if block:
                    hospitals.append(block)
                    block = {}
                block["name"] = line.replace("name:", "").strip()
            elif line.startswith("address:"):
                block["address"] = line.replace("address:", "").strip()
            elif line.startswith("telephone:"):
                block["telephone"] = line.replace("telephone:", "").strip()
            elif line.startswith("fax:"):
                block["fax"] = line.replace("fax:", "").strip()
        if block:
            hospitals.append(block)
    return hospitals

def display_hospital_info_section(selected_hospital=None):
    """Display a searchable table of hospital info and highlight the selected hospital."""
    hospitals = load_hospital_static_info()
    
    st.subheader("🏥 Hospital Information")
    st.info("💡 **Search Tips**: You can search by hospital name, address, or location (e.g., 'chai wan', 'queen mary', 'pok fu lam').")

    if 'hospital_search' not in st.session_state:
        st.session_state['hospital_search'] = ''

    search = st.text_input(
        "Search hospital by name or address:",
        key="hospital_search",
        value=st.session_state['hospital_search'],
        placeholder="e.g., Queen Mary Hospital, Chai Wan, or 102 Pok Fu Lam Road"
    )

    # Improved search logic
    def improved_fuzzy_match(hospital, search_term):
        if not search_term:
            return True
        search_lower = search_term.lower().strip()
        name = hospital["name"].lower()
        address = hospital["address"].lower()
        # 1. Full phrase match
        if search_lower in name or search_lower in address:
            return True
        # 2. All words (min 3 chars) must be present in name or address
        words = [w for w in search_lower.split() if len(w) >= 3]
        return all(w in name or w in address for w in words)

    filtered = [h for h in hospitals if improved_fuzzy_match(h, search)]

    if selected_hospital and not search:
        selected_info = next((h for h in hospitals if h["name"].strip().lower() == selected_hospital.strip().lower()), None)
        if selected_info:
            st.success(f"📍 **Selected Hospital**: {selected_info['name']}")
            st.markdown(f"""
            <div style='border:2px solid #1976d2; border-radius:8px; padding:10px; margin-bottom:8px; background:#f0f7ff;'>
                <div style='font-size:1.1rem; font-weight:bold; color:#1976d2;'>{selected_info['name']}</div>
                <div style='font-size:1rem; color:#444;'>📍 {selected_info['address']}</div>
                <div style='font-size:1rem; color:#666;'>📞 Tel: {selected_info['telephone']}</div>
                {f"<div style='font-size:1rem; color:#666;'>📠 Fax: {selected_info['fax']}</div>" if selected_info.get('fax') else ''}
            </div>
            """, unsafe_allow_html=True)
    elif search:
        if not filtered:
            st.warning("🔍 No hospitals found matching your search. Try a different keyword.")
        else:
            st.success(f"🔍 Found **{len(filtered)}** hospital(s) matching '{search}':")
            for h in filtered:
                st.markdown(f"""
                <div style='border:2px solid #eee; border-radius:8px; padding:10px; margin-bottom:8px; background:#fafbfc;'>
                    <div style='font-size:1.1rem; font-weight:bold; color:#222;'>{h['name']}</div>
                    <div style='font-size:1rem; color:#444;'>📍 {h['address']}</div>
                    <div style='font-size:1rem; color:#666;'>📞 Tel: {h['telephone']}</div>
                    {f"<div style='font-size:1rem; color:#666;'>📠 Fax: {h['fax']}</div>" if h.get('fax') else ''}
                </div>
                """, unsafe_allow_html=True)
    with st.expander("📋 View All Hospital Details", expanded=False):
        if not search and not selected_hospital:
            st.info("🔍 Enter a search term above to find specific hospitals, or browse all hospitals below.")
        for h in hospitals:
            highlight = h["name"].strip().lower() == selected_hospital.strip().lower() if selected_hospital else False
            st.markdown(f"""
            <div style='border:2px solid {"#1976d2" if highlight else "#eee"}; border-radius:8px; padding:10px; margin-bottom:8px; background:{'#f0f7ff' if highlight else '#fafbfc'};'>
                <div style='font-size:1.1rem; font-weight:bold; color:{'#1976d2' if highlight else '#222'};'>{h['name']}</div>
                <div style='font-size:1rem; color:#444;'>📍 {h['address']}</div>
                <div style='font-size:1rem; color:#666;'>📞 Tel: {h['telephone']}</div>
                {f"<div style='font-size:1rem; color:#666;'>📠 Fax: {h['fax']}</div>" if h.get('fax') else ''}
            </div>
            """, unsafe_allow_html=True)

def create_emergency_insights():
    """Create hospital info section instead of A&E tips."""
    selected_hospital = st.session_state.get('selected_hospital', None)
    display_hospital_info_section(selected_hospital)

def create_mobile_optimization_notice():
    """Create mobile optimization notice"""
    # Check if running on mobile (simplified detection)
    st.markdown("""
    <style>
    @media (max-width: 768px) {
        .mobile-notice {
            background-color: #e3f2fd;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Mobile-friendly tips
    with st.expander("📱 Mobile Tips", expanded=False):
        st.markdown("""
        **Using on Mobile Device:**
        - 🔄 **Rotate screen** for better chart viewing
        - 👆 **Tap and hold** charts to see details
        - 📍 **Use location services** for accurate directions
        - 🔖 **Bookmark** this page for quick access
        - 📞 **Save hospital numbers** to your contacts
        
        **Quick Actions:**
        - 🚨 **Emergency**: Dial 999 immediately
        - 🏥 **Call Hospital**: Numbers provided in traffic section
        - 🗺️ **Get Directions**: Use map integration
        """)

def create_data_export_options():
    """Create data export options"""
    st.subheader("💾 Export Data")
    
    # Get current data
    collector = AEDataCollector()
    data = collector.fetch_current_data()
    
    if not data or 'waitTime' not in data:
        st.warning("No data available for export")
        return
    
    # Prepare export data
    export_data = []
    for hospital_data in data['waitTime']:
        if isinstance(hospital_data, list) and len(hospital_data) >= 2:
            hospital_name = hospital_data[0]
            wait_time = hospital_data[1]
            region = get_hospital_region(hospital_name)
            wait_numeric = WAIT_TIME_CATEGORIES.get(wait_time, {}).get('numeric', 999)
            
            export_data.append({
                'Hospital Name': hospital_name,
                'Wait Time': wait_time,
                'Wait Minutes': wait_numeric,
                'Region': region,
                'Last Updated': data.get('updateTime', 'Unknown'),
                'Export Time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
    
    if export_data:
        export_df = pd.DataFrame(export_data)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # CSV export
            csv_data = export_df.to_csv(index=False)
            st.download_button(
                label="📄 Download CSV",
                data=csv_data,
                file_name=f"hk_ae_wait_times_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                key="download_csv"
            )
        
        with col2:
            # JSON export
            json_data = export_df.to_json(orient='records', indent=2)
            st.download_button(
                label="📋 Download JSON",
                data=json_data,
                file_name=f"hk_ae_wait_times_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json",
                key="download_json"
            )
        
        with col3:
            # Quick share text
            share_text = f"HK A&E Wait Times ({data.get('updateTime', 'Unknown')}):\n"
            for _, row in export_df.iterrows():
                share_text += f"• {row['Hospital Name']}: {row['Wait Time']}\n"
            
            st.download_button(
                label="📤 Share Text",
                data=share_text,
                file_name=f"hk_ae_summary_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain",
                key="download_text"
            )
        
        st.caption("💡 Data exported includes current wait times, regions, and timestamp information.")

# Additional utility functions for enhanced functionality

def get_hospital_contact_info(hospital_name):
    """Get contact information for a hospital"""
    # Hospital contact directory (simplified)
    hospital_contacts = {
        "Queen Mary Hospital": {"phone": "2255 3838", "address": "102 Pokfulam Road, Hong Kong"},
        "Queen Elizabeth Hospital": {"phone": "2958 8888", "address": "30 Gascoigne Road, Kowloon"},
        "Prince of Wales Hospital": {"phone": "2632 2211", "address": "30-32 Ngan Shing Street, Sha Tin"},
        "Pamela Youde Nethersole Eastern Hospital": {"phone": "2595 6111", "address": "3 Lok Man Road, Chai Wan"},
        "United Christian Hospital": {"phone": "2379 9111", "address": "130 Hip Wo Street, Kwun Tong"},
        "Tuen Mun Hospital": {"phone": "2468 5111", "address": "23 Tsing Chung Koon Road, Tuen Mun"},
        # Add more hospitals as needed
    }
    
    return hospital_contacts.get(hospital_name, {"phone": "N/A", "address": "N/A"})

def calculate_distance_to_hospitals(user_location, hospital_list):
    """Calculate approximate distances to hospitals (simplified)"""
    # This would integrate with a real mapping service
    # For now, return simulated distances
    distances = {}
    for hospital in hospital_list:
        # Simulated distance calculation
        distances[hospital] = f"{round(5 + hash(hospital + user_location) % 20, 1)} km"
    
    return distances

def get_emergency_preparedness_tips():
    """Get emergency preparedness tips"""
    return {
        "before_emergency": [
            "Keep emergency contacts readily available",
            "Know the location of nearest hospitals",
            "Keep important medical documents accessible",
            "Have a basic first aid kit at home"
        ],
        "during_emergency": [
            "Stay calm and assess the situation",
            "Call 999 for life-threatening emergencies",
            "Provide clear location information",
            "Follow dispatcher instructions"
        ],
        "hospital_visit": [
            "Bring ID and insurance documents",
            "List current medications and allergies",
            "Have emergency contact information",
            "Be prepared for potential wait times"
        ]
    }

def display_new_hospital_notification(processed_data):
    """Display notification for new hospitals detected"""
    new_hospitals = [h for h in processed_data if h.get('is_new_hospital', False)]
    
    if new_hospitals:
        with st.expander("🆕 New Hospitals Detected", expanded=True):
            st.warning("""
            **New hospitals have been detected in the API data!** 
            
            These hospitals are not yet fully configured in our system. 
            They will appear on maps with estimated locations and may not have complete information.
            """)
            
            for hospital in new_hospitals:
                st.info(f"""
                **{hospital['hospital']}**
                - Wait Time: {hospital['wait_text']}
                - Estimated Region: {hospital.get('fallback_region', 'Unknown')}
                - Status: Using fallback coordinates
                """)
            
            st.markdown("""
            **What this means:**
            - ✅ Wait time data is accurate (from official API)
            - ⚠️ Map location is estimated based on hospital name patterns
            - ⚠️ Route planning may not be accurate
            - ⚠️ Region filtering may not work properly
            
            **To fix this:** Update the `HOSPITAL_CONFIG` in `config.py` with accurate coordinates and details.
            """)

def display_admin_info(collector):
    """Display admin information for new hospitals and configuration updates"""
    changes_summary = collector.get_hospital_changes_summary()
    
    if not changes_summary:
        return
    
    with st.expander("🔧 Admin Information - New Hospitals", expanded=False):
        st.subheader("🏥 New Hospitals Detected")
        
        if changes_summary['new_hospitals']:
            st.warning(f"**{len(changes_summary['new_hospitals'])} new hospital(s) detected**")
            
            # Get configuration updates
            config_updates = collector.get_all_config_updates()
            
            for update in config_updates:
                with st.expander(f"📝 {update['hospital_name']}", expanded=False):
                    st.markdown(f"""
                    **Hospital:** {update['hospital_name']}
                    **Estimated Region:** {update['fallback_region']}
                    **Estimated Coordinates:** {update['fallback_coordinates']}
                    """)
                    
                    st.markdown("**Configuration Snippet:**")
                    st.code(update['config_snippet'], language='python')
                    
                    st.markdown("**Instructions:**")
                    st.markdown(update['instructions'])
                    
                    # Copy button for config snippet
                    if st.button(f"📋 Copy Config for {update['hospital_name']}", key=f"copy_config_{update['hospital_name']}"):
                        st.session_state[f"copied_config_{update['hospital_name']}"] = update['config_snippet']
                        st.success("Configuration copied to clipboard!")
            
            st.markdown("""
            **Next Steps:**
            1. Update `config.py` with the new hospital configurations
            2. Update `ae_collector.py` hospital_name_mapping
            3. Test the dashboard to ensure new hospitals display correctly
            4. Verify coordinates and region information are accurate
            """)
        else:
            st.success("✅ No new hospitals detected")

def display_sidebar_about_me():
    """Display an About Me section in the sidebar."""
    with st.sidebar.expander("About Me", expanded=False):
        st.markdown("""
        **Student name:** Isaac Cheng Wai Bun  
        **Student ID:** bi74bc  
        **Assignment 2.1:** A Domain Specific Data Science Product Development Project: Product Prototype
        """)

def render_ae_dashboard():
    """Main dashboard rendering function"""
    st.title("Hong Kong Government Hospital Emergency Wait Times Dashboard")
    
    @st.cache_resource
    def get_collector():
        return AEDataCollector()
    collector = get_collector()
    with st.spinner("🔄 Fetching latest A&E data..."):
        data = collector.fetch_current_data()
    if not data:
        st.error("❌ Unable to fetch A&E data. Please try again later.")
        return
    
    # Process data to detect new hospitals
    processed_data = collector.process_hospital_data(data)
    
    # Display new hospital notification if any detected
    display_new_hospital_notification(processed_data)
    
    # Display admin information (collapsed by default)
    display_admin_info(collector)
    
    display_last_update(data)
    st.divider()
    sort_option, region_filter, wait_filter = create_ranking_controls()
    st.divider()
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("Emergency wait time by Hospital")
        df = create_hospital_ranking_chart(data, sort_option, region_filter, wait_filter)
    with col2:
        st.subheader("Hospital Locations Map")
        if df is not None:
            selected_hospital = st.session_state.get('selected_hospital', None)
            create_hospital_map(df, selected_hospital)
        else:
            st.warning("No data available for map display")
    if df is not None:
        st.divider()
        create_summary_statistics(df)
        st.divider()
        create_emergency_insights()
        selected_hospital = st.session_state.get('selected_hospital', None)
        if selected_hospital:
            st.divider()
            create_route_planning_map(df, selected_hospital)
        st.divider()

    st.markdown("""
    <div style='font-size:0.95rem; color:#888;'>
    <b>General Disclaimer:</b> This dashboard is a student project for academic purposes only. Data and features are for demonstration and learning, not for real-world medical or emergency use.<br>
    Cheng Wai Bun Isaac @ 2025 CETM Assignment 2.1: A Domain Specific Data Science Product Development Project: Product Prototype
    </div>
    """, unsafe_allow_html=True)

def create_hospital_comparison_tool():
    """Create a tool to compare multiple hospitals"""
    st.subheader("⚖️ Hospital Comparison Tool")
    
    # Get current data
    collector = AEDataCollector()
    data = collector.fetch_current_data()
    
    if not data or 'waitTime' not in data:
        st.error("No hospital data available for comparison")
        return
    
    # Extract hospital names
    hospital_names = [hospital_data[0] for hospital_data in data['waitTime'] 
                     if isinstance(hospital_data, list) and len(hospital_data) >= 2]
    
    # Hospital selection
    col1, col2 = st.columns(2)
    
    with col1:
        selected_hospitals = st.multiselect(
            "🏥 Select Hospitals to Compare:",
            hospital_names,
            default=hospital_names[:3] if len(hospital_names) >= 3 else hospital_names,
            key=f"compare_multiselect_{section if 'section' in locals() else 'main'}"
        )
    
    with col2:
        comparison_metric = st.selectbox(
            "📊 Compare By:",
            ["Wait Time", "Region", "Distance from Location"],
            key=f"compare_metric_{section if 'section' in locals() else 'main'}"
        )
    
    if selected_hospitals:
        # Create comparison dataframe
        comparison_data = []
        for hospital_data in data['waitTime']:
            if isinstance(hospital_data, list) and len(hospital_data) >= 2:
                hospital_name = hospital_data[0]
                if hospital_name in selected_hospitals:
                    wait_time = hospital_data[1]
                    region = get_hospital_region(hospital_name)
                    
                    comparison_data.append({
                        'Hospital': hospital_name,
                        'Wait Time': wait_time,
                        'Region': region,
                        'Wait Minutes': WAIT_TIME_CATEGORIES.get(wait_time, {}).get('numeric', 999)
                    })
        
        if comparison_data:
            comparison_df = pd.DataFrame(comparison_data)
            
            # Display comparison table
            st.dataframe(
                comparison_df[['Hospital', 'Wait Time', 'Region']], 
                use_container_width=True,
                hide_index=True
            )
            
            # Comparison chart
            fig_comparison = px.bar(
                comparison_df,
                x='Hospital',
                y='Wait Minutes',
                color='Wait Minutes',
                color_continuous_scale='RdYlGn_r',
                title=f"Wait Time Comparison - {len(selected_hospitals)} Hospitals"
            )
            
            fig_comparison.update_layout(
                xaxis_tickangle=-45,
                height=400
            )
            
            st.plotly_chart(fig_comparison, use_container_width=True)
            
            # Recommendation
            best_hospital = comparison_df.loc[comparison_df['Wait Minutes'].idxmin()]
            st.success(f"🏆 **Recommended**: {best_hospital['Hospital']} has the shortest wait time ({best_hospital['Wait Time']})")

def create_historical_trends():
    """Create historical trends section (simulated data for demo)"""
    st.subheader("📈 Historical Trends & Patterns")
    
    # Note about data limitations
    st.info("📊 Historical trend analysis based on typical patterns. Real historical data integration coming soon.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Simulated hourly pattern
        hours = list(range(24))
        # Typical A&E pattern: higher during day, peak in evening
        typical_wait_pattern = [
            45, 40, 35, 30, 35, 40, 60, 80, 100, 120,  # 0-9
            140, 160, 150, 140, 130, 140, 160, 180,    # 10-17
            200, 180, 160, 120, 80, 60                 # 18-23
        ]
        
        fig_hourly = px.line(
            x=hours,
            y=typical_wait_pattern,
            title="Typical Daily Wait Time Pattern",
            labels={'x': 'Hour of Day', 'y': 'Average Wait Time (Minutes)'}
        )
        
        fig_hourly.add_hline(
            y=120, 
            line_dash="dash", 
            line_color="red",
            annotation_text="2 Hour Threshold"
        )
        
        st.plotly_chart(fig_hourly, use_container_width=True)
    
    with col2:
        # Simulated weekly pattern
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        weekly_pattern = [120, 100, 95, 110, 140, 160, 130]
        
        fig_weekly = px.bar(
            x=days,
            y=weekly_pattern,
            title="Typical Weekly Wait Time Pattern",
            labels={'x': 'Day of Week', 'y': 'Average Wait Time (Minutes)'},
            color=weekly_pattern,
            color_continuous_scale='RdYlGn_r'
        )
        
        st.plotly_chart(fig_weekly, use_container_width=True)
    
    # Pattern insights
    with st.expander("🔍 Pattern Insights", expanded=False):
        st.markdown("""
        **Daily Patterns:**
        - 🌅 **Early Morning (2-6 AM)**: Shortest wait times
        - 🌞 **Morning (8-11 AM)**: Moderate increase
        - 🌆 **Evening (6-9 PM)**: Peak wait times
        - 🌙 **Late Night (10 PM-1 AM)**: Gradual decrease
        
        **Weekly Patterns:**
        - 📅 **Monday-Wednesday**: Generally shorter waits
        - 📅 **Friday-Saturday**: Highest wait times
        - 📅 **Sunday**: Moderate wait times
        
        **Seasonal Considerations:**
        - ❄️ **Winter**: Higher volumes due to flu season
        - ☀️ **Summer**: Heat-related incidents increase
        - 🎆 **Holidays**: Unpredictable patterns
        """)

def create_mobile_optimization_notice():
    """Create mobile optimization notice"""
    # Check if running on mobile (simplified detection)
    st.markdown("""
    <style>
    @media (max-width: 768px) {
        .mobile-notice {
            background-color: #e3f2fd;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Mobile-friendly tips
    with st.expander("📱 Mobile Tips", expanded=False):
        st.markdown("""
        **Using on Mobile Device:**
        - 🔄 **Rotate screen** for better chart viewing
        - 👆 **Tap and hold** charts to see details
        - 📍 **Use location services** for accurate directions
        - 🔖 **Bookmark** this page for quick access
        - 📞 **Save hospital numbers** to your contacts
        
        **Quick Actions:**
        - 🚨 **Emergency**: Dial 999 immediately
        - 🏥 **Call Hospital**: Numbers provided in traffic section
        - 🗺️ **Get Directions**: Use map integration
        """)

def create_data_export_options():
    """Create data export options"""
    st.subheader("💾 Export Data")
    
    # Get current data
    collector = AEDataCollector()
    data = collector.fetch_current_data()
    
    if not data or 'waitTime' not in data:
        st.warning("No data available for export")
        return
    
    # Prepare export data
    export_data = []
    for hospital_data in data['waitTime']:
        if isinstance(hospital_data, list) and len(hospital_data) >= 2:
            hospital_name = hospital_data[0]
            wait_time = hospital_data[1]
            region = get_hospital_region(hospital_name)
            wait_numeric = WAIT_TIME_CATEGORIES.get(wait_time, {}).get('numeric', 999)
            
            export_data.append({
                'Hospital Name': hospital_name,
                'Wait Time': wait_time,
                'Wait Minutes': wait_numeric,
                'Region': region,
                'Last Updated': data.get('updateTime', 'Unknown'),
                'Export Time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
    
    if export_data:
        export_df = pd.DataFrame(export_data)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # CSV export
            csv_data = export_df.to_csv(index=False)
            st.download_button(
                label="📄 Download CSV",
                data=csv_data,
                file_name=f"hk_ae_wait_times_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                key="download_csv"
            )
        
        with col2:
            # JSON export
            json_data = export_df.to_json(orient='records', indent=2)
            st.download_button(
                label="📋 Download JSON",
                data=json_data,
                file_name=f"hk_ae_wait_times_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json",
                key="download_json"
            )
        
        with col3:
            # Quick share text
            share_text = f"HK A&E Wait Times ({data.get('updateTime', 'Unknown')}):\n"
            for _, row in export_df.iterrows():
                share_text += f"• {row['Hospital Name']}: {row['Wait Time']}\n"
            
            st.download_button(
                label="📤 Share Text",
                data=share_text,
                file_name=f"hk_ae_summary_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain",
                key="download_text"
            )
        
        st.caption("💡 Data exported includes current wait times, regions, and timestamp information.")
