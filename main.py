"""
Hong Kong A&E Wait Times Dashboard
Real-time emergency department waiting times across Hong Kong hospitals
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

# Import our modules
from ae_collector import AEDataCollector
from config import HOSPITAL_CONFIG, SEVERITY_COLORS, MAP_CONFIG, WAIT_TIME_COLORS, CHART_COLORS
from components.ae_components import render_ae_dashboard, create_emergency_insights, display_sidebar_info, display_sidebar_how_to_use, display_sidebar_about_me, inject_sidebar_style

# Set Mapbox token from Streamlit secrets
if "MAPBOX_TOKEN" in st.secrets:
    px.set_mapbox_access_token(st.secrets["MAPBOX_TOKEN"])
else:
    st.warning("⚠️ Mapbox token not found in secrets. Map features may be limited.")

# Page configuration
st.set_page_config(
    page_title="Hong Kong A&E Wait Times",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Initialize data collector
@st.cache_resource
def get_collector():
    return AEDataCollector()

collector = get_collector()

# Main dashboard
def main():
    inject_sidebar_style()
    display_sidebar_how_to_use()
    display_sidebar_info()
    display_sidebar_about_me()
    render_ae_dashboard()
    

def create_hospital_ranking_view(df):
    """Create hospital ranking chart view"""
    st.subheader("🏥 Hospital Wait Time Rankings")
    
    # Sorting options
    col1, col2 = st.columns(2)
    with col1:
        sort_by = st.selectbox(
            "Sort by:",
            ["Wait Time", "Region"],
            key="main_sort_by_selectbox"
        )
    
    with col2:
        region_filter = st.multiselect(
            "Filter by Region:",
            df['region'].unique() if 'region' in df.columns else [],
            default=df['region'].unique() if 'region' in df.columns else [],
            key="main_region_multiselect"
        )
    
    # Apply filters
    filtered_df = df.copy()
    if region_filter and 'region' in df.columns:
        filtered_df = filtered_df[filtered_df['region'].isin(region_filter)]
    
    # Apply sorting
    if sort_by == "Wait Time":
        filtered_df = filtered_df.sort_values('wait_time')
    elif sort_by == "Region":
        filtered_df = filtered_df.sort_values('region')
    
    # Create horizontal bar chart
    fig = go.Figure(go.Bar(
        y=filtered_df['name'],
        x=filtered_df['wait_time'],
        orientation='h',
        marker=dict(
            color=[SEVERITY_COLORS.get(sev, '#808080') for sev in filtered_df['severity']],
            opacity=0.8
        ),
        text=filtered_df['wait_text'],
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>Wait Time: %{text}<br>Minutes: %{x}<extra></extra>'
    ))
    
    fig.update_layout(
        title="Emergency Department Wait Times",
        xaxis_title="Wait Time (Minutes)",
        yaxis_title="Hospital",
        height=max(400, len(filtered_df) * 30),
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Summary statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        shortest_wait = filtered_df.loc[filtered_df['wait_time'].idxmin()]
        st.metric("🟢 Shortest Wait", 
                 shortest_wait['name'][:20] + "..." if len(shortest_wait['name']) > 20 else shortest_wait['name'],
                 f"{shortest_wait['wait_time']} min")
    
    with col2:
        longest_wait = filtered_df.loc[filtered_df['wait_time'].idxmax()]
        st.metric("🔴 Longest Wait", 
                 longest_wait['name'][:20] + "..." if len(longest_wait['name']) > 20 else longest_wait['name'],
                 f"{longest_wait['wait_time']} min")
    
    with col3:
        avg_wait = filtered_df['wait_time'].mean()
        st.metric("📊 Average Wait", f"{avg_wait:.0f} min")
    
    with col4:
        critical_count = len(filtered_df[filtered_df['wait_time'] > 240])  # > 4 hours
        st.metric("⚠️ Critical (>4h)", f"{critical_count} hospitals")

def create_map_view(df):
    """Create interactive map view"""
    st.subheader("🗺️ Hospital Locations & Wait Times")
    
    # Filter out hospitals without coordinates
    map_df = df[(df['lat'] != 0) & (df['lon'] != 0)].copy()
    
    if map_df.empty:
        st.warning("No hospital location data available")
        return
    
    # Create map
    fig = px.scatter_mapbox(
        map_df,
        lat="lat",
        lon="lon",
        hover_name="name",
        hover_data={"wait_text": True, "severity": True, "lat": False, "lon": False},
        color="wait_time",
        color_continuous_scale="RdYlGn_r",
        size_max=20,
        zoom=MAP_CONFIG["zoom"],
        center={"lat": MAP_CONFIG["center_lat"], "lon": MAP_CONFIG["center_lon"]},
        mapbox_style="carto-positron"
    )
    
    fig.update_layout(
        height=600,
        margin={"r":0,"t":0,"l":0,"b":0}
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Map legend
    st.markdown("""
    **Map Legend:**
    - 🟢 Green: Short wait times (< 2 hours)
    - 🟡 Yellow: Moderate wait times (2-4 hours)
    - 🔴 Red: Long wait times (> 4 hours)
    """)

def create_analytics_view(df):
    """Create analytics and insights view"""
    st.subheader("📈 Wait Time Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Wait time distribution
        fig_hist = px.histogram(
            df, 
            x="wait_time", 
            nbins=20,
            title="Wait Time Distribution",
            labels={"wait_time": "Wait Time (Minutes)", "count": "Number of Hospitals"}
        )
        fig_hist.update_traces(marker_color='lightblue', opacity=0.7)
        st.plotly_chart(fig_hist, use_container_width=True)
    
    with col2:
        # Severity distribution
        severity_counts = df['severity'].value_counts()
        fig_pie = px.pie(
            values=severity_counts.values,
            names=severity_counts.index,
            title="Wait Time Severity Distribution",
            color_discrete_map=SEVERITY_COLORS
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    # Regional analysis (if region data available)
    if 'region' in df.columns:
        st.subheader("🌏 Regional Analysis")
        
        regional_stats = df.groupby('region').agg({
            'wait_time': ['mean', 'min', 'max', 'count']
        }).round(1)
        
        regional_stats.columns = ['Avg Wait (min)', 'Min Wait (min)', 'Max Wait (min)', 'Hospital Count']
        
        st.dataframe(regional_stats, use_container_width=True)
    
    # Time-based insights
    st.subheader("⏰ Current Insights")
    
    current_hour = datetime.now().hour
    
    if 8 <= current_hour <= 18:
        st.info("🌅 **Peak Hours**: Currently in daytime hours. Wait times may be higher due to increased patient volume.")
    elif 18 <= current_hour <= 22:
        st.warning("🌆 **Evening Rush**: Evening hours often see increased emergency visits.")
    else:
        st.success("🌙 **Off-Peak**: Overnight hours typically have shorter wait times.")
    
    # Recommendations
    st.subheader("💡 Recommendations")
    
    shortest_wait_hospitals = df.nsmallest(3, 'wait_time')
    
    st.markdown("**🎯 Shortest Wait Times Right Now:**")
    for idx, hospital in shortest_wait_hospitals.iterrows():
        st.markdown(f"- **{hospital['name']}**: {hospital['wait_text']}")
    
    # Emergency reminder
    st.error("""
    🚨 **Important Reminder**: 
    - These wait times are for non-urgent cases (triage categories 4-5)
    - Life-threatening emergencies are always treated immediately
    - If you're experiencing a medical emergency, call 999 or go to the nearest A&E immediately
    """)

if __name__ == "__main__":
    main()
