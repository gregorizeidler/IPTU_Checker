import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database import get_all_records
import os

st.set_page_config(page_title="IPTU Checker", page_icon="🛰️", layout="wide")

st.title("🛰️ IPTU Checker: Satellite-Based Land Analysis")
st.markdown("### Property Tax Verification System")

# Load data
try:
    df = get_all_records()
    
    if df.empty:
        st.warning("⚠️ No data available. Run the analysis first:")
        st.code("python src/main.py", language="bash")
        st.stop()
    
    # Sidebar filters
    st.sidebar.header("🔍 Filters")
    status_filter = st.sidebar.multiselect(
        "Status",
        options=df['status'].unique(),
        default=df['status'].unique()
    )
    
    # Filter data
    filtered_df = df[df['status'].isin(status_filter)]
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Properties", len(filtered_df))
    
    with col2:
        compliant = len(filtered_df[filtered_df['status'] == 'compliant'])
        st.metric("✅ Compliant", compliant)
    
    with col3:
        underdeclared = len(filtered_df[filtered_df['status'] == 'underdeclared'])
        st.metric("⚠️ Underdeclared", underdeclared, delta=f"{underdeclared} cases")
    
    with col4:
        overdeclared = len(filtered_df[filtered_df['status'] == 'overdeclared'])
        st.metric("💰 Overdeclared", overdeclared)
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Status Distribution")
        status_counts = filtered_df['status'].value_counts()
        fig_pie = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            color=status_counts.index,
            color_discrete_map={
                'compliant': '#00CC96',
                'underdeclared': '#EF553B',
                'overdeclared': '#FFA15A'
            }
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        st.subheader("📈 Difference Distribution")
        fig_hist = px.histogram(
            filtered_df,
            x='percent_difference',
            nbins=20,
            labels={'percent_difference': 'Difference (%)'},
            color='status',
            color_discrete_map={
                'compliant': '#00CC96',
                'underdeclared': '#EF553B',
                'overdeclared': '#FFA15A'
            }
        )
        st.plotly_chart(fig_hist, use_container_width=True)
    
    # Area comparison
    st.subheader("📏 Registered vs Measured Area")
    fig_scatter = px.scatter(
        filtered_df,
        x='registered_area',
        y='real_area',
        color='status',
        hover_data=['address', 'percent_difference'],
        labels={
            'registered_area': 'Registered Area (m²)',
            'real_area': 'Measured Area (m²)'
        },
        color_discrete_map={
            'compliant': '#00CC96',
            'underdeclared': '#EF553B',
            'overdeclared': '#FFA15A'
        }
    )
    # Add diagonal line (perfect match)
    max_val = max(filtered_df['registered_area'].max(), filtered_df['real_area'].max())
    fig_scatter.add_trace(go.Scatter(
        x=[0, max_val],
        y=[0, max_val],
        mode='lines',
        line=dict(dash='dash', color='gray'),
        name='Perfect Match',
        showlegend=True
    ))
    st.plotly_chart(fig_scatter, use_container_width=True)
    
    # Interactive Map with Plotly
    if 'latitude' in filtered_df.columns and 'longitude' in filtered_df.columns:
        st.subheader("🗺️ Interactive Property Map")
        map_df = filtered_df[['latitude', 'longitude', 'address', 'status', 
                              'registered_area', 'real_area', 'percent_difference']].dropna()
        
        if not map_df.empty:
            # Color mapping
            color_map = {
                'compliant': '#00CC96',      # Green
                'underdeclared': '#EF553B',  # Red
                'overdeclared': '#FFA15A'    # Orange
            }
            
            map_df['color'] = map_df['status'].map(color_map)
            
            # Size based on difference percentage
            map_df['size'] = map_df['percent_difference'].abs() * 2 + 10
            
            # Create interactive map
            fig_map = go.Figure()
            
            for status in map_df['status'].unique():
                status_data = map_df[map_df['status'] == status]
                
                fig_map.add_trace(go.Scattermapbox(
                    lat=status_data['latitude'],
                    lon=status_data['longitude'],
                    mode='markers',
                    marker=dict(
                        size=status_data['size'],
                        color=status_data['color'],
                        opacity=0.7
                    ),
                    text=status_data['address'],
                    name=status.capitalize(),
                    hovertemplate='<b>%{text}</b><br>' +
                                  'Status: ' + status + '<br>' +
                                  'Registered: %{customdata[0]:.1f} m²<br>' +
                                  'Measured: %{customdata[1]:.1f} m²<br>' +
                                  'Difference: %{customdata[2]:.1f}%' +
                                  '<extra></extra>',
                    customdata=status_data[['registered_area', 'real_area', 'percent_difference']].values
                ))
            
            # Calculate center of map
            center_lat = map_df['latitude'].mean()
            center_lon = map_df['longitude'].mean()
            
            fig_map.update_layout(
                mapbox=dict(
                    style='open-street-map',
                    center=dict(lat=center_lat, lon=center_lon),
                    zoom=11
                ),
                showlegend=True,
                height=600,
                margin={"r":0,"t":0,"l":0,"b":0}
            )
            
            st.plotly_chart(fig_map, use_container_width=True)
            
            # Map legend
            st.markdown("""
            **Map Legend:**
            - 🟢 Green = Compliant (within tolerance)
            - 🔴 Red = Underdeclared (potential tax evasion)
            - 🟠 Orange = Overdeclared (overpaying taxes)
            - Marker size = Magnitude of difference
            """)
        else:
            st.info("No properties with coordinates to display on map")
    
    # Data table
    st.subheader("📋 Detailed Results")
    
    # Color code the status
    def color_status(val):
        if val == 'compliant':
            return 'background-color: #d4edda'
        elif val == 'underdeclared':
            return 'background-color: #f8d7da'
        elif val == 'overdeclared':
            return 'background-color: #fff3cd'
        return ''
    
    display_df = filtered_df[[
        'address', 'registered_area', 'real_area',
        'difference', 'percent_difference', 'status'
    ]].copy()
    
    display_df.columns = ['Address', 'Registered (m²)', 'Measured (m²)',
                          'Difference (m²)', 'Difference (%)', 'Status']
    
    styled_df = display_df.style.applymap(color_status, subset=['Status'])
    st.dataframe(styled_df, use_container_width=True)
    
    # Statistics
    st.subheader("📊 Statistics")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Average Difference", f"{filtered_df['percent_difference'].mean():.2f}%")
    
    with col2:
        st.metric("Median Difference", f"{filtered_df['percent_difference'].median():.2f}%")
    
    with col3:
        st.metric("Max Difference", f"{filtered_df['percent_difference'].max():.2f}%")
    
except Exception as e:
    st.error(f"❌ Error loading data: {e}")
    st.info("Make sure the database exists. Run: `python src/main.py`")
