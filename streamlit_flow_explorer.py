# import pandas as pd
# import numpy as np
# import plotly.express as px
# import plotly.graph_objects as go
# import plotly.io as pio
# import streamlit as st
# from datetime import datetime
# import re

# # ------------ Page Config ------------
# st.set_page_config(page_title="WRMM Forecast Explorer", layout="wide")

# # ------------ Header ------------
# st.title("🌊 WRMM Forecast Explorer")

# # ------------ Sidebar: File Upload Section ------------
# st.sidebar.header("📁 Data Upload")

# # Upload QA/QC data
# st.sidebar.subheader("1. QA/QC Data")
# qa_file = st.sidebar.file_uploader(
#     "Upload QA/QC data file",
#     type=["csv", "xlsx", "xls"],
#     help="Upload a CSV or Excel file with columns: Date, River_basin_name, Station_name, Raw_median, Step_2_median, Final_median",
#     key="qa_upload"
# )

# # Upload Forecast data
# st.sidebar.subheader("2. Forecast Data")
# forecast_file = st.sidebar.file_uploader(
#     "Upload forecast data file",
#     type=["csv", "xlsx", "xls"],
#     help="Upload a CSV or Excel file with forecast data (Tmin, Tmax, Precip)",
#     key="forecast_upload"
# )

# # Add option to select sheet name for Excel files
# sheet_name_qa = "Combined"
# sheet_name_forecast = "All_Stations_Enhanced_Format"

# if qa_file and qa_file.name.endswith(('.xlsx', '.xls')):
#     sheet_name_qa = st.sidebar.text_input("QA/QC Sheet name", value="Combined", help="Sheet name for QA/QC data")

# if forecast_file and forecast_file.name.endswith(('.xlsx', '.xls')):
#     sheet_name_forecast = st.sidebar.text_input("Forecast Sheet name", value="All_Stations_Enhanced_Format", help="Sheet name for forecast data")

# # ------------ Helper Functions ------------
# def parse_forecast_dates_from_filename(filename):
#     """Extract forecast start and end dates from filename format: Data_for_Dashboard_YYYYMMDD_YYYYMMDD"""
#     match = re.search(r'(\d{8})_(\d{8})', filename)
#     if match:
#         start_str = match.group(1)
#         end_str = match.group(2)
#         forecast_start = pd.to_datetime(start_str, format='%Y%m%d')
#         forecast_end = pd.to_datetime(end_str, format='%Y%m%d')
#         return forecast_start, forecast_end
#     return None, None

# @st.cache_data
# def load_qa_data(file, sheet=None):
#     """Load QA/QC data from uploaded file"""
#     try:
#         if file.name.endswith('.csv'):
#             df = pd.read_csv(file)
#         elif file.name.endswith(('.xlsx', '.xls')):
#             df = pd.read_excel(file, sheet_name=sheet)
#         else:
#             st.error(f"Unsupported file type: {file.name}")
#             return None, None
        
#         df["Date"] = pd.to_datetime(df["Date"])
        
#         basin_to_stations = (
#             df[["River_basin_name", "Station_name"]]
#             .dropna()
#             .drop_duplicates()
#             .groupby("River_basin_name")["Station_name"]
#             .apply(list)
#             .to_dict()
#         )
        
#         return df, basin_to_stations
#     except Exception as e:
#         st.error(f"Error loading QA/QC file: {str(e)}")
#         return None, None

# @st.cache_data
# def load_forecast_data(file, sheet=None):
#     """Load forecast data from uploaded file"""
#     try:
#         if file.name.endswith('.csv'):
#             df = pd.read_csv(file)
#         elif file.name.endswith(('.xlsx', '.xls')):
#             df = pd.read_excel(file, sheet_name=sheet)
#         else:
#             st.error(f"Unsupported file type: {file.name}")
#             return None, None, None, None
        
#         df["Date"] = pd.to_datetime(df["Date"])
        
#         # Parse forecast dates from filename
#         forecast_start, forecast_end = parse_forecast_dates_from_filename(file.name)
        
#         # Get unique stations - check multiple possible column names
#         station_col = None
#         for col_name in ['Station', 'Stations', 'Station_name', 'station', 'stations']:
#             if col_name in df.columns:
#                 station_col = col_name
#                 break
        
#         if station_col:
#             stations = sorted(df[station_col].unique())
#             # Standardize to 'Station' for consistency
#             if station_col != 'Station':
#                 df = df.rename(columns={station_col: 'Station'})
#         else:
#             stations = []
        
#         return df, forecast_start, forecast_end, stations
#     except Exception as e:
#         st.error(f"Error loading forecast file: {str(e)}")
#         return None, None, None, None

# def detect_metric_columns(df):
#     """Detect available metric columns and their types"""
#     metrics = {}
    
#     # Standard forecast format
#     for base in ['Precip', 'Tmax', 'Tmin']:
#         if f'{base} M' in df.columns:
#             metrics[base] = {
#                 'median': f'{base} M',
#                 'lq': f'{base} LQ' if f'{base} LQ' in df.columns else None,
#                 'uq': f'{base} UQ' if f'{base} UQ' in df.columns else None,
#                 'historical': f'Historical_{base}' if f'Historical_{base}' in df.columns else None,
#                 'name': base
#             }
    
#     # Generic format (Median, UL, LL)
#     if 'Median' in df.columns:
#         metrics['Generic'] = {
#             'median': 'Median',
#             'lq': 'LL' if 'LL' in df.columns else None,
#             'uq': 'UL' if 'UL' in df.columns else None,
#             'historical': None,
#             'name': 'Value'
#         }
    
#     return metrics

# def create_forecast_plot(df, metric_config, metric_name, forecast_start, stations_filter=None, show_confidence=True, show_historical=False):
#     """Create a plotly figure with historical (light) and forecast (bright) data"""
    
#     # If no forecast_start, use the midpoint of the date range
#     if forecast_start is None:
#         date_range = df['Date'].max() - df['Date'].min()
#         forecast_start = df['Date'].min() + date_range / 2
    
#     # Filter by stations if specified
#     if stations_filter:
#         df = df[df['Station'].isin(stations_filter)].copy()
    
#     if df.empty:
#         return None
    
#     metric_col = metric_config['median']
#     lq_col = metric_config['lq']
#     uq_col = metric_config['uq']
#     historical_col = metric_config.get('historical', None)
    
#     # Split into historical and forecast based on date
#     df_historical = df[df['Date'] < forecast_start].copy()
#     df_forecast = df[df['Date'] >= forecast_start].copy()
    
#     fig = go.Figure()
    
#     # Get unique stations
#     stations = df['Station'].unique()
#     colors = px.colors.qualitative.Plotly
    
#     for i, station in enumerate(stations):
#         color = colors[i % len(colors)]
        
#         # Historical data - only plot if show_historical is True
#         if show_historical:
#             if historical_col and historical_col in df.columns:
#                 # Use the dedicated historical column for all dates before forecast start
#                 hist_data = df_historical[df_historical['Station'] == station]
#                 if not hist_data.empty:
#                     fig.add_trace(go.Scatter(
#                         x=hist_data['Date'],
#                         y=hist_data[historical_col],
#                         mode='lines+markers',
#                         name=f'{station} (Historical)',
#                         line=dict(color=color, width=2, dash='dot'),
#                         marker=dict(size=5, opacity=0.6),
#                         opacity=0.6,
#                         legendgroup=station,
#                         showlegend=True
#                     ))
#             else:
#                 # Fallback: use median column for historical period
#                 hist_data = df_historical[df_historical['Station'] == station]
#                 if not hist_data.empty and metric_col in hist_data.columns:
#                     fig.add_trace(go.Scatter(
#                         x=hist_data['Date'],
#                         y=hist_data[metric_col],
#                         mode='lines+markers',
#                         name=f'{station} (Historical)',
#                         line=dict(color=color, width=2, dash='dot'),
#                         marker=dict(size=5, opacity=0.6),
#                         opacity=0.6,
#                         legendgroup=station,
#                         showlegend=True
#                     ))
        
#         # Forecast data (bright color) - always show
#         forecast_data = df_forecast[df_forecast['Station'] == station]
#         if not forecast_data.empty and metric_col in forecast_data.columns:
#             fig.add_trace(go.Scatter(
#                 x=forecast_data['Date'],
#                 y=forecast_data[metric_col],
#                 mode='lines+markers',
#                 name=f'{station} (Forecast)',
#                 line=dict(color=color, width=3),
#                 marker=dict(size=6),
#                 opacity=1.0,
#                 legendgroup=station,
#                 showlegend=True
#             ))
        
#         # Add confidence intervals if requested and available
#         if show_confidence and lq_col and uq_col:
#             forecast_data_conf = df_forecast[df_forecast['Station'] == station]
#             if not forecast_data_conf.empty:
#                 # Upper quartile line
#                 fig.add_trace(go.Scatter(
#                     x=forecast_data_conf['Date'],
#                     y=forecast_data_conf[uq_col],
#                     mode='lines',
#                     name=f'{station} (UQ)',
#                     line=dict(color=color, width=1.5, dash='dash'),
#                     opacity=0.5,
#                     legendgroup=station,
#                     showlegend=False
#                 ))
                
#                 # Lower quartile line
#                 fig.add_trace(go.Scatter(
#                     x=forecast_data_conf['Date'],
#                     y=forecast_data_conf[lq_col],
#                     mode='lines',
#                     name=f'{station} (LQ)',
#                     line=dict(color=color, width=1.5, dash='dash'),
#                     opacity=0.5,
#                     legendgroup=station,
#                     showlegend=False
#                 ))
    
#     # Add vertical line at forecast start (only if showing historical data)
#     if show_historical:
#         fig.add_shape(
#             type="line",
#             x0=forecast_start,
#             x1=forecast_start,
#             y0=0,
#             y1=1,
#             yref="paper",
#             line=dict(color="red", width=2, dash="dash")
#         )
        
#         fig.add_annotation(
#             x=forecast_start,
#             y=1,
#             yref="paper",
#             text="Forecast Start",
#             showarrow=False,
#             yshift=10,
#             font=dict(color="red", size=12)
#         )
    
#     # Set x-axis range based on show_historical toggle
#     if show_historical:
#         # Show full time range (historical + forecast)
#         x_range = None  # Auto range
#     else:
#         # Show only forecast period
#         if not df_forecast.empty:
#             x_range = [df_forecast['Date'].min(), df_forecast['Date'].max()]
#         else:
#             x_range = None
    
#     title_suffix = " - Historical vs Forecast" if show_historical else " - Forecast"
    
#     fig.update_layout(
#         title=f"{metric_name}{title_suffix}",
#         xaxis_title="Date",
#         yaxis_title=metric_name,
#         height=600,
#         hovermode='x unified',
#         legend=dict(
#             yanchor="top",
#             y=0.99,
#             xanchor="left",
#             x=1.01
#         )
#     )
    
#     # Apply x-axis range if specified
#     if x_range:
#         fig.update_xaxes(range=x_range)
    
#     return fig

# # ------------ Main App ------------

# # Show welcome message if no files uploaded
# if forecast_file is None and qa_file is None:
#     st.info("👆 Please upload data files from the sidebar to get started!")
    
#     st.markdown("""
#     ### 📊 Available Dashboards
    
#     #### 1. **Forecast Data Dashboard** (Upload Forecast Data)
#     - The input data file name should be `Data_for_Dashboard_yyyymmdd_yyyymmdd.xlsx`
#     - Visualize precipitation and temperature forecasts
#     - Compare historical vs forecast data
#     - View confidence intervals (LQ, M, UQ)
#     - Multiple stations support
    
#     #### 2. **QA/QC Dashboard** (Upload QA/QC Data)
#     - Input filename should be `RiverBasin_Flows_Combined_yyyymmdd_yyyymmdd.xlsx`
#     - Time-series analysis
#     - Pairwise differences
#     - BC vs Observation analysis
#     - Per-station summaries
#     """)
    
#     st.stop()

# # ------------ FORECAST DATA DASHBOARD ------------
# if forecast_file is not None:
#     st.header("📈 Forecast Data Dashboard")
    
#     # Load forecast data
#     forecast_df, forecast_start, forecast_end, forecast_stations = load_forecast_data(forecast_file, sheet_name_forecast)
    
#     if forecast_df is None:
#         st.error("Failed to load forecast data. Please check your file format.")
#     else:
#         # Detect available metrics
#         available_metrics = detect_metric_columns(forecast_df)
        
#         # Show data info
#         col_info1, col_info2, col_info3, col_info4 = st.columns(4)
#         with col_info1:
#             st.metric("Total Records", f"{len(forecast_df):,}")
#         with col_info2:
#             st.metric("Stations", len(forecast_stations))
#         with col_info3:
#             if forecast_start:
#                 st.metric("Forecast Start", forecast_start.strftime('%Y-%m-%d'))
#             else:
#                 st.warning("⚠️ Dates not detected")
#         with col_info4:
#             st.metric("Date Range", f"{(forecast_df['Date'].max() - forecast_df['Date'].min()).days} days")
        
#         # Check if stations were found
#         if not forecast_stations:
#             st.error("❌ No stations found in the data. Please check that your file has a 'Station', 'Stations', or 'Station_name' column.")
#             st.info("**Available columns:** " + ", ".join(forecast_df.columns.tolist()))
#             st.stop()
        
#         # Check if metrics were found
#         if not available_metrics:
#             st.error("❌ No recognized metric columns found in the data.")
#             st.info("Expected columns like: Precip M, Tmax M, Tmin M OR Median, UL, LL")
#             st.info("**Available columns:** " + ", ".join(forecast_df.columns.tolist()))
#             st.stop()
        
#         # Station filter
#         st.subheader("Station Selection")
#         selected_stations = st.multiselect(
#             "Select stations to display",
#             options=forecast_stations,
#             default=forecast_stations[:5] if len(forecast_stations) > 5 else forecast_stations,
#             help="Select one or more stations to display in the charts"
#         )
        
#         # Validate station selection
#         if not selected_stations:
#             st.warning("⚠️ Please select at least one station to display the charts.")
#             st.stop()
        
#         # Display options
#         col_opt1, col_opt2 = st.columns(2)
#         with col_opt1:
#             show_historical = st.checkbox("Show historical data", value=False, help="Toggle to show historical data along with forecast")
#         with col_opt2:
#             show_confidence = st.checkbox("Show confidence intervals (LQ/UQ or LL/UL)", value=True)
        
#         # Create tabs based on available metrics
#         if 'Precip' in available_metrics and 'Tmax' in available_metrics and 'Tmin' in available_metrics:
#             # Standard format with Precip, Tmax, Tmin
#             tab_precip, tab_tmax, tab_tmin, tab_data = st.tabs([
#                 "🌧️ Precipitation",
#                 "🌡️ Temperature Max",
#                 "❄️ Temperature Min",
#                 "📋 Data Table"
#             ])
            
#             with tab_precip:
#                 fig = create_forecast_plot(
#                     forecast_df,
#                     available_metrics['Precip'],
#                     'Precipitation (mm)',
#                     forecast_start if forecast_start else forecast_df['Date'].min(),
#                     selected_stations,
#                     show_confidence,
#                     show_historical
#                 )
#                 if fig:
#                     st.plotly_chart(fig, use_container_width=True)
                    
#                     st.subheader("Summary Statistics")
#                     filtered_df = forecast_df[forecast_df['Station'].isin(selected_stations)]
#                     if forecast_start:
#                         forecast_data = filtered_df[filtered_df['Date'] >= forecast_start]
#                     else:
#                         forecast_data = filtered_df
                    
#                     if not forecast_data.empty:
#                         metric_col = available_metrics['Precip']['median']
#                         col1, col2, col3 = st.columns(3)
#                         with col1:
#                             st.metric("Average", f"{forecast_data[metric_col].mean():.2f} mm")
#                         with col2:
#                             st.metric("Max", f"{forecast_data[metric_col].max():.2f} mm")
#                         with col3:
#                             st.metric("Total", f"{forecast_data[metric_col].sum():.2f} mm")
            
#             with tab_tmax:
#                 fig = create_forecast_plot(
#                     forecast_df,
#                     available_metrics['Tmax'],
#                     'Temperature Max (°C)',
#                     forecast_start if forecast_start else forecast_df['Date'].min(),
#                     selected_stations,
#                     show_confidence,
#                     show_historical
#                 )
#                 if fig:
#                     st.plotly_chart(fig, use_container_width=True)
                    
#                     st.subheader("Summary Statistics")
#                     filtered_df = forecast_df[forecast_df['Station'].isin(selected_stations)]
#                     if forecast_start:
#                         forecast_data = filtered_df[filtered_df['Date'] >= forecast_start]
#                     else:
#                         forecast_data = filtered_df
                    
#                     if not forecast_data.empty:
#                         metric_col = available_metrics['Tmax']['median']
#                         col1, col2, col3 = st.columns(3)
#                         with col1:
#                             st.metric("Average", f"{forecast_data[metric_col].mean():.2f} °C")
#                         with col2:
#                             st.metric("Max", f"{forecast_data[metric_col].max():.2f} °C")
#                         with col3:
#                             st.metric("Min", f"{forecast_data[metric_col].min():.2f} °C")
            
#             with tab_tmin:
#                 fig = create_forecast_plot(
#                     forecast_df,
#                     available_metrics['Tmin'],
#                     'Temperature Min (°C)',
#                     forecast_start if forecast_start else forecast_df['Date'].min(),
#                     selected_stations,
#                     show_confidence,
#                     show_historical
#                 )
#                 if fig:
#                     st.plotly_chart(fig, use_container_width=True)
                    
#                     st.subheader("Summary Statistics")
#                     filtered_df = forecast_df[forecast_df['Station'].isin(selected_stations)]
#                     if forecast_start:
#                         forecast_data = filtered_df[filtered_df['Date'] >= forecast_start]
#                     else:
#                         forecast_data = filtered_df
                    
#                     if not forecast_data.empty:
#                         metric_col = available_metrics['Tmin']['median']
#                         col1, col2, col3 = st.columns(3)
#                         with col1:
#                             st.metric("Average", f"{forecast_data[metric_col].mean():.2f} °C")
#                         with col2:
#                             st.metric("Max", f"{forecast_data[metric_col].max():.2f} °C")
#                         with col3:
#                             st.metric("Min", f"{forecast_data[metric_col].min():.2f} °C")
            
#             with tab_data:
#                 st.subheader("Raw Data Preview")
#                 display_df = forecast_df[forecast_df['Station'].isin(selected_stations)].copy()
#                 st.dataframe(display_df, height=400, use_container_width=True)
                
#                 csv = display_df.to_csv(index=False)
#                 st.download_button(
#                     label="📥 Download Filtered Data as CSV",
#                     data=csv,
#                     file_name="forecast_data_filtered.csv",
#                     mime="text/csv"
#                 )
        
#         elif 'Generic' in available_metrics:
#             # Generic format with Median, UL, LL
#             tab_plot, tab_data = st.tabs(["📈 Forecast Plot", "📋 Data Table"])
            
#             with tab_plot:
#                 fig = create_forecast_plot(
#                     forecast_df,
#                     available_metrics['Generic'],
#                     'Forecast Value',
#                     forecast_start if forecast_start else forecast_df['Date'].min(),
#                     selected_stations,
#                     show_confidence,
#                     show_historical
#                 )
#                 if fig:
#                     st.plotly_chart(fig, use_container_width=True)
                    
#                     st.subheader("Summary Statistics")
#                     filtered_df = forecast_df[forecast_df['Station'].isin(selected_stations)]
#                     if forecast_start:
#                         forecast_data = filtered_df[filtered_df['Date'] >= forecast_start]
#                     else:
#                         forecast_data = filtered_df
                    
#                     if not forecast_data.empty:
#                         metric_col = available_metrics['Generic']['median']
#                         col1, col2, col3 = st.columns(3)
#                         with col1:
#                             st.metric("Average", f"{forecast_data[metric_col].mean():.2f}")
#                         with col2:
#                             st.metric("Max", f"{forecast_data[metric_col].max():.2f}")
#                         with col3:
#                             st.metric("Min", f"{forecast_data[metric_col].min():.2f}")
#                 else:
#                     st.warning("No data to display for selected stations.")
            
#             with tab_data:
#                 st.subheader("Raw Data Preview")
#                 display_df = forecast_df[forecast_df['Station'].isin(selected_stations)].copy()
#                 st.dataframe(display_df, height=400, use_container_width=True)
                
#                 csv = display_df.to_csv(index=False)
#                 st.download_button(
#                     label="📥 Download Filtered Data as CSV",
#                     data=csv,
#                     file_name="forecast_data_filtered.csv",
#                     mime="text/csv"
#                 )

# # ------------ QA/QC DATA DASHBOARD ------------
# if qa_file is not None:
#     st.header("🔍 QA/QC Data Dashboard")
    
#     qa_df, basin_to_stations = load_qa_data(qa_file, sheet_name_qa)
    
#     if qa_df is None:
#         st.error("Failed to load QA/QC data. Please check your file format.")
#     else:
#         st.sidebar.success(f"✅ Loaded {len(qa_df):,} rows")
#         st.sidebar.info(f"📊 {len(basin_to_stations)} basins found")
#         st.sidebar.info(f"📍 {qa_df['Station_name'].nunique()} unique stations")
        
#         all_basins = sorted(basin_to_stations.keys())
#         metric_options = ["Raw_median", "Step_2_median", "Final_median"]
#         available_metrics = [m for m in metric_options if m in qa_df.columns]
        
#         if not available_metrics:
#             st.error("No valid metric columns found in the data.")
#         else:
#             col1, col2, col3 = st.columns([1, 1.5, 1])
            
#             with col1:
#                 selected_basin = st.selectbox("Basin", options=all_basins, index=0 if all_basins else None)
            
#             with col2:
#                 available_stations = sorted(basin_to_stations.get(selected_basin, []))
#                 selected_qa_stations = st.multiselect("Stations", options=available_stations, default=available_stations)
            
#             with col3:
#                 selected_metrics = st.multiselect("Metric(s)", options=available_metrics, default=[available_metrics[0]] if available_metrics else [])
            
#             if selected_basin and selected_qa_stations:
#                 sub = qa_df[(qa_df["River_basin_name"] == selected_basin) & (qa_df["Station_name"].isin(selected_qa_stations))].copy()
#             else:
#                 sub = pd.DataFrame()
            
#             tab1, tab2, tab3, tab4 = st.tabs(["📈 Time-series", "📊 Pairwise Differences", "🔄 BC vs Observation", "📋 Per-Station Summary"])
            
#             with tab1:
#                 if sub.empty:
#                     st.warning("Select at least one station to view data.")
#                 elif not selected_metrics:
#                     st.warning("Select at least one metric.")
#                 else:
#                     ycols = [c for c in selected_metrics if c in sub.columns]
#                     if ycols:
#                         plot_df = sub.melt(id_vars=["Date", "Station_name"], value_vars=ycols, var_name="Metric", value_name="Flow")
#                         fig = px.line(plot_df, x="Date", y="Flow", color="Station_name", line_dash="Metric", markers=True, title=f"{selected_basin} – Time Series")
#                         fig.update_layout(legend_title_text="Station • Metric", yaxis_title="Flow (CMS)", height=600)
#                         st.plotly_chart(fig, use_container_width=True)
            
#             with tab2:
#                 if not sub.empty:
#                     col_a, col_b, col_c = st.columns(3)
#                     with col_a:
#                         diff_metric = st.selectbox("Difference metric", options=available_metrics, index=0)
#                     with col_b:
#                         up_station = st.selectbox("Upstream station", options=[None] + available_stations, format_func=lambda x: "(Optional)" if x is None else x)
#                     with col_c:
#                         down_station = st.selectbox("Downstream station", options=[None] + available_stations, format_func=lambda x: "(Optional)" if x is None else x)
                    
#                     st.markdown("---")
                    
#                     if up_station and down_station and up_station != down_station:
#                         up = qa_df[(qa_df["River_basin_name"] == selected_basin) & (qa_df["Station_name"] == up_station)][["Date", diff_metric]]
#                         down = qa_df[(qa_df["River_basin_name"] == selected_basin) & (qa_df["Station_name"] == down_station)][["Date", diff_metric]]
#                         m = pd.merge(up, down, on="Date", suffixes=("_up", "_down"))
#                         m["Diff"] = m[f"{diff_metric}_up"] - m[f"{diff_metric}_down"]
#                         fig = px.line(m, x="Date", y="Diff", title=f"{selected_basin} – Difference ({diff_metric}): {up_station} - {down_station}", markers=True)
#                         fig.update_layout(yaxis_title="Difference (CMS)", height=600)
#                         st.plotly_chart(fig, use_container_width=True)
#                     elif len(selected_qa_stations) >= 2:
#                         stations_in_basin = basin_to_stations.get(selected_basin, [])
#                         order = [s for s in stations_in_basin if s in selected_qa_stations]
#                         wide = qa_df[(qa_df["River_basin_name"] == selected_basin) & (qa_df["Station_name"].isin(order))].pivot_table(index="Date", columns="Station_name", values=diff_metric, aggfunc="first").reindex(columns=order).sort_index()
#                         rows = []
#                         for i in range(len(order) - 1):
#                             a, b = order[i], order[i + 1]
#                             dname = f"D{i+1}: {a} - {b}"
#                             series = wide[a] - wide[b]
#                             rows.append(series.rename(dname))
#                         if rows:
#                             diff_df = pd.concat(rows, axis=1).reset_index()
#                             long_df = diff_df.melt("Date", var_name="Pair", value_name="Diff")
#                             fig = px.line(long_df, x="Date", y="Diff", color="Pair", title=f"{selected_basin} – Consecutive Pairwise Differences ({diff_metric})", markers=True)
#                             fig.update_layout(yaxis_title="Difference (CMS)", height=600)
#                             st.plotly_chart(fig, use_container_width=True)
#                     else:
#                         st.warning("Select at least two stations.")
#                 else:
#                     st.warning("Select at least one station to view differences.")
            
#             with tab3:
#                 if sub.empty:
#                     st.warning("Select at least one station to view data.")
#                 elif "OBS" not in sub.columns or "BC_Factor" not in sub.columns:
#                     st.warning("OBS / BC_Factor columns not found in the data.")
#                 else:
#                     fig = px.scatter(sub, x="OBS", y="BC_Factor", color="Station_name", trendline="ols", trendline_scope="overall", title=f"{selected_basin} – BC Factor vs OBS")
#                     fig.update_layout(xaxis_title="OBS", yaxis_title="BC_Factor", height=600)
#                     st.plotly_chart(fig, use_container_width=True)
            
#             with tab4:
#                 if sub.empty:
#                     st.warning("Select at least one station to view summary.")
#                 else:
#                     summary_metrics = [m for m in ["Raw_median", "Step_2_median", "Final_median"] if m in sub.columns]
#                     if summary_metrics:
#                         sums = sub.groupby("Station_name")[summary_metrics].sum(min_count=1).reset_index()
#                         avgs = sub.groupby("Station_name")[summary_metrics].mean().reset_index()
#                         sums["Type"] = "Sum"
#                         avgs["Type"] = "Average"
#                         summary = pd.concat([sums, avgs], ignore_index=True)
#                         summary = summary.melt(id_vars=["Station_name", "Type"], value_vars=summary_metrics, var_name="Metric", value_name="Value")
#                         fig = px.bar(summary, x="Station_name", y="Value", color="Metric", facet_col="Type", barmode="group", title=f"{selected_basin} – Per-Station Sums & Averages")
#                         fig.update_layout(yaxis_title="Flow (CMS)", height=600)
#                         st.plotly_chart(fig, use_container_width=True)

# st.markdown("---")
# st.caption("WRMM Forecast Explorer | Built with Streamlit | 🌊 Upload your data to get started")

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st
from datetime import datetime
import re
from typing import Dict, List


# ------------ Page Config ------------
st.set_page_config(page_title="WRMM Forecast Explorer", layout="wide")

# ------------ Header ------------
st.title("🌊 WRMM Forecast Explorer")

# ------------ Sidebar: File Upload Section ------------
st.sidebar.header("📁 Data Upload")

# Upload QA/QC data
st.sidebar.subheader("1. QA/QC Data")
qa_file = st.sidebar.file_uploader(
    "Upload QA/QC data file",
    type=["csv", "xlsx", "xls"],
    help="Upload a CSV or Excel file with columns: Date, River_basin_name, Station_name, Raw_median, Step_2_median, Final_median",
    key="qa_upload"
)

# Upload Forecast data
st.sidebar.subheader("2. Forecast Data")
forecast_file = st.sidebar.file_uploader(
    "Upload forecast data file",
    type=["csv", "xlsx", "xls"],
    help="Upload a CSV or Excel file with forecast data (Tmin, Tmax, Precip)",
    key="forecast_upload"
)

# Add option to select sheet name for Excel files
sheet_name_qa = "Combined"
sheet_name_forecast = "All_Stations_Enhanced_Format"

if qa_file and qa_file.name.endswith(('.xlsx', '.xls')):
    sheet_name_qa = st.sidebar.text_input("QA/QC Sheet name", value="Combined", help="Sheet name for QA/QC data")

if forecast_file and forecast_file.name.endswith(('.xlsx', '.xls')):
    sheet_name_forecast = st.sidebar.text_input("Forecast Sheet name", value="All_Stations_Enhanced_Format", help="Sheet name for forecast data")

new_river_basins: Dict[str, List[str]] = {
    "Waterton River": ['G5AD260','05AD008','05ADU01'],
    "Belly River": ['05AD032', '05AD005', '05AD041','05AD002','GBWCON','GBEMOU'],
    "St. Mary River": ['05AE027', 'GSTDAM','05AE006'],
    "Castle River": ['05AA022'],
    "Crowsnest River": ['05AA002'],
    "Pincher Creek": ['05AA004'],
    "Willow Creek": ['05AB028', '05AB021', '05AB002'],
    "Mosquito Creek": ['GMOSWC', 'GMOSNT', 'GMOSMO'],
    "Frank Lake": ['GLBFK1', 'GLBFK2', 'GLBFK3'],
    "Little Bow River": ['GLBFLK', 'GLB5330','05AC930','05AC003'],
    "Oldman River": ['05AA023','05AA024','05AAU01','05AB918','05AB007','05AAU02', '05AD019', '05ADU03', '05AD007','05AG006'],
    "Elbow River": ['05BJ004', '05BJ001'],
    "Sheep River": ['GSHMOU'],
    "Highwood River": ['05BL019', 'GHISQA','05BL004', '05BL009', '05BL024'],
    "Spray River": ['05BC006'],
    "Ghost River": ['05BG002'],
    "Cascade River": ['05BD002'],
    "Kananaskis River": ['05BF003','05BF001'],
    "Bow River": ['05BB001', '05BE008', '05BE004', '05BE006', '05BH008', '05BH004','05BHU01','05BMU01','05BM002','05BM004','05BN012'],
    "Red Deer River": ['05CB007', '05CC002', '05CD004', 'GRDBIG', '05CE001', 'GRDJEN', '05CK004'],
    "SSask River": ['05AJU01','05AJ001','05HBU01']
}

# -------------------- Station aliasing utilities --------------------
def station_aliases(canonical: str) -> List[str]:
    """
    Return a list of plausible aliases for a canonical station id as they may
    appear in your CSV/XLSX (e.g., padded with trailing zero to 7 chars).
    Examples:
      GBWCON   -> ['GBWCON', 'GBWCON0']
      GLBFK1   -> ['GLBFK1', 'GLBFK10']
      GLBFK2   -> ['GLBFK2', 'GLBFK20']
      GLBFK3   -> ['GLBFK3', 'GLBFK30']
      05AD005  -> ['05AD005']  (no change)
    """
    c = canonical.strip().upper()

    # Plain 05xxxx style: return as-is
    if re.fullmatch(r"\d{2}[A-Z]{2}\d{3}|05[A-Z0-9]{4,}", c) or c.startswith("05"):
        return [c]

    # GLBFK1/2/3 pattern: add pad-0 version used in some files (GLBFK10/20/30)
    m = re.fullmatch(r"(GLB[A-Z]{2,})(\d)$", c)
    if m:
        base, num = m.group(1), m.group(2)
        return [c, f"{base}{num}0"]

    # Pure G-code with letters only (e.g., GBWCON, GBEMOU, GSHMOU, GSTDAM, GHISQA)
    if re.fullmatch(r"G[A-Z]{5,6}", c):
        return [c, c + "0"]

    # Fallback: return itself
    return [c]

def build_alias_to_canonical_map() -> Dict[str, str]:
    """Create a lookup dict: alias -> canonical, across all basins."""
    alias_map = {}
    for basin, stations in new_river_basins.items():
        for s in stations:
            for a in station_aliases(s):
                alias_map[a] = s
    return alias_map

ALIAS_TO_CANON = build_alias_to_canonical_map()

def map_to_canonical(s: str) -> str:
    """Map a station id from the file to its canonical id (if known)."""
    if not isinstance(s, str):
        return s
    key = s.strip().upper()
    return ALIAS_TO_CANON.get(key, key)  # keep original if unknown

def canonical_stations_present(df: pd.DataFrame, basin: str) -> List[str]:
    """
    For a given basin, return the canonical stations that actually have data
    in df['Station_name'] (after alias mapping).
    """
    if "Station_name" not in df.columns:
        return []
    # Convert to canonical
    canon_series = df["Station_name"].astype(str).map(map_to_canonical)
    present = set(canon_series.unique())
    desired = new_river_basins.get(basin, [])
    return [s for s in desired if s in present]

def rekey_to_canonical(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return a copy of df where Station_name is canonical (using the alias map).
    """
    out = df.copy()
    out["Station_name"] = out["Station_name"].astype(str).map(map_to_canonical)
    return out


# ------------ Helper Functions ------------
def parse_forecast_dates_from_filename(filename):
    """Extract forecast start and end dates from filename format: Data_for_Dashboard_YYYYMMDD_YYYYMMDD"""
    match = re.search(r'(\d{8})_(\d{8})', filename)
    if match:
        start_str = match.group(1)
        end_str = match.group(2)
        forecast_start = pd.to_datetime(start_str, format='%Y%m%d')
        forecast_end = pd.to_datetime(end_str, format='%Y%m%d')
        return forecast_start, forecast_end
    return None, None

@st.cache_data
def load_qa_data(file, sheet=None):
    """Load QA/QC data from uploaded file"""
    try:
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file, sheet_name=sheet)
        else:
            st.error(f"Unsupported file type: {file.name}")
            return None, None
        
        df["Date"] = pd.to_datetime(df["Date"])
        
        basin_to_stations = (
            df[["River_basin_name", "Station_name"]]
            .dropna()
            .drop_duplicates()
            .groupby("River_basin_name")["Station_name"]
            .apply(list)
            .to_dict()
        )
        
        return df, basin_to_stations
    except Exception as e:
        st.error(f"Error loading QA/QC file: {str(e)}")
        return None, None

@st.cache_data
def load_forecast_data(file, sheet=None):
    """Load forecast data from uploaded file"""
    try:
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file, sheet_name=sheet)
        else:
            st.error(f"Unsupported file type: {file.name}")
            return None, None, None, None
        
        df["Date"] = pd.to_datetime(df["Date"])
        
        # Parse forecast dates from filename
        forecast_start, forecast_end = parse_forecast_dates_from_filename(file.name)
        
        # Get unique stations - check multiple possible column names
        station_col = None
        for col_name in ['Station', 'Stations', 'Station_name', 'station', 'stations']:
            if col_name in df.columns:
                station_col = col_name
                break
        
        if station_col:
            stations = sorted(df[station_col].unique())
            # Standardize to 'Station' for consistency
            if station_col != 'Station':
                df = df.rename(columns={station_col: 'Station'})
        else:
            stations = []
        
        return df, forecast_start, forecast_end, stations
    except Exception as e:
        st.error(f"Error loading forecast file: {str(e)}")
        return None, None, None, None

def detect_metric_columns(df):
    """Detect available metric columns and their types"""
    metrics = {}
    
    # Standard forecast format
    for base in ['Precip', 'Tmax', 'Tmin']:
        if f'{base} M' in df.columns:
            metrics[base] = {
                'median': f'{base} M',
                'lq': f'{base} LQ' if f'{base} LQ' in df.columns else None,
                'uq': f'{base} UQ' if f'{base} UQ' in df.columns else None,
                'historical': f'Historical_{base}' if f'Historical_{base}' in df.columns else None,
                'name': base
            }
    
    # Generic format (Median, UL, LL)
    if 'Median' in df.columns:
        metrics['Generic'] = {
            'median': 'Median',
            'lq': 'LL' if 'LL' in df.columns else None,
            'uq': 'UL' if 'UL' in df.columns else None,
            'historical': None,
            'name': 'Value'
        }
    
    return metrics

def create_forecast_plot(df, metric_config, metric_name, forecast_start, stations_filter=None, show_confidence=True, show_historical=False):
    """Create a plotly figure with historical (light) and forecast (bright) data"""
    
    # If no forecast_start, use the midpoint of the date range
    if forecast_start is None:
        date_range = df['Date'].max() - df['Date'].min()
        forecast_start = df['Date'].min() + date_range / 2
    
    # Filter by stations if specified
    if stations_filter:
        df = df[df['Station'].isin(stations_filter)].copy()
    
    if df.empty:
        return None
    
    metric_col = metric_config['median']
    lq_col = metric_config['lq']
    uq_col = metric_config['uq']
    historical_col = metric_config.get('historical', None)
    
    # Split into historical and forecast based on date
    df_historical = df[df['Date'] < forecast_start].copy()
    df_forecast = df[df['Date'] >= forecast_start].copy()
    
    fig = go.Figure()
    
    # Get unique stations
    stations = df['Station'].unique()
    colors = px.colors.qualitative.Plotly
    
    for i, station in enumerate(stations):
        color = colors[i % len(colors)]
        
        # Historical data - only plot if show_historical is True
        if show_historical:
            if historical_col and historical_col in df.columns:
                # Use the dedicated historical column for all dates before forecast start
                hist_data = df_historical[df_historical['Station'] == station]
                if not hist_data.empty:
                    fig.add_trace(go.Scatter(
                        x=hist_data['Date'],
                        y=hist_data[historical_col],
                        mode='lines+markers',
                        name=f'{station} (Historical)',
                        line=dict(color=color, width=2, dash='dot'),
                        marker=dict(size=5, opacity=0.6),
                        opacity=0.6,
                        legendgroup=station,
                        showlegend=True
                    ))
            else:
                # Fallback: use median column for historical period
                hist_data = df_historical[df_historical['Station'] == station]
                if not hist_data.empty and metric_col in hist_data.columns:
                    fig.add_trace(go.Scatter(
                        x=hist_data['Date'],
                        y=hist_data[metric_col],
                        mode='lines+markers',
                        name=f'{station} (Historical)',
                        line=dict(color=color, width=2, dash='dot'),
                        marker=dict(size=5, opacity=0.6),
                        opacity=0.6,
                        legendgroup=station,
                        showlegend=True
                    ))
        
        # Forecast data (bright color) - always show
        forecast_data = df_forecast[df_forecast['Station'] == station]
        if not forecast_data.empty and metric_col in forecast_data.columns:
            fig.add_trace(go.Scatter(
                x=forecast_data['Date'],
                y=forecast_data[metric_col],
                mode='lines+markers',
                name=f'{station} (Forecast)',
                line=dict(color=color, width=3),
                marker=dict(size=6),
                opacity=1.0,
                legendgroup=station,
                showlegend=True
            ))
        
        # Add confidence intervals if requested and available
        if show_confidence and lq_col and uq_col:
            forecast_data_conf = df_forecast[df_forecast['Station'] == station]
            if not forecast_data_conf.empty:
                # Upper quartile line
                fig.add_trace(go.Scatter(
                    x=forecast_data_conf['Date'],
                    y=forecast_data_conf[uq_col],
                    mode='lines',
                    name=f'{station} (UQ)',
                    line=dict(color=color, width=1.5, dash='dash'),
                    opacity=0.5,
                    legendgroup=station,
                    showlegend=False
                ))
                
                # Lower quartile line
                fig.add_trace(go.Scatter(
                    x=forecast_data_conf['Date'],
                    y=forecast_data_conf[lq_col],
                    mode='lines',
                    name=f'{station} (LQ)',
                    line=dict(color=color, width=1.5, dash='dash'),
                    opacity=0.5,
                    legendgroup=station,
                    showlegend=False
                ))
    
    # Add vertical line at forecast start (only if showing historical data)
    if show_historical:
        fig.add_shape(
            type="line",
            x0=forecast_start,
            x1=forecast_start,
            y0=0,
            y1=1,
            yref="paper",
            line=dict(color="red", width=2, dash="dash")
        )
        
        fig.add_annotation(
            x=forecast_start,
            y=1,
            yref="paper",
            text="Forecast Start",
            showarrow=False,
            yshift=10,
            font=dict(color="red", size=12)
        )
    
    # Set x-axis range based on show_historical toggle
    if show_historical:
        # Show full time range (historical + forecast)
        x_range = None  # Auto range
    else:
        # Show only forecast period
        if not df_forecast.empty:
            x_range = [df_forecast['Date'].min(), df_forecast['Date'].max()]
        else:
            x_range = None
    
    title_suffix = " - Historical vs Forecast" if show_historical else " - Forecast"
    
    fig.update_layout(
        title=f"{metric_name}{title_suffix}",
        xaxis_title="Date",
        yaxis_title=metric_name,
        height=600,
        hovermode='x unified',
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=1.01
        )
    )
    
    # Apply x-axis range if specified
    if x_range:
        fig.update_xaxes(range=x_range)
    
    return fig

# ------------ Main App ------------

# Show welcome message if no files uploaded
if forecast_file is None and qa_file is None:
    st.info("👆 Please upload data files from the sidebar to get started!")
    
    st.markdown("""
    ### 📊 Available Dashboards
    
    #### 1. **Forecast Data Dashboard** (Upload Forecast Data)
    - The input data file name should be `Data_for_Dashboard_yyyymmdd_yyyymmdd.xlsx`
    - Visualize precipitation and temperature forecasts
    - Compare historical vs forecast data
    - View confidence intervals (LQ, M, UQ)
    - Multiple stations support
    
    #### 2. **QA/QC Dashboard** (Upload QA/QC Data)
    - Input filename should be `RiverBasin_Flows_Combined_yyyymmdd_yyyymmdd.xlsx`
    - Time-series analysis
    - Pairwise differences
    - BC vs Observation analysis
    - Per-station summaries
    """)
    
    st.stop()

# ------------ FORECAST DATA DASHBOARD ------------
if forecast_file is not None:
    st.header("📈 Forecast Data Dashboard")
    
    # Load forecast data
    forecast_df, forecast_start, forecast_end, forecast_stations = load_forecast_data(forecast_file, sheet_name_forecast)
    
    if forecast_df is None:
        st.error("Failed to load forecast data. Please check your file format.")
    else:
        # Detect available metrics
        available_metrics = detect_metric_columns(forecast_df)
        
        # Show data info
        col_info1, col_info2, col_info3, col_info4 = st.columns(4)
        with col_info1:
            st.metric("Total Records", f"{len(forecast_df):,}")
        with col_info2:
            st.metric("Stations", len(forecast_stations))
        with col_info3:
            if forecast_start:
                st.metric("Forecast Start", forecast_start.strftime('%Y-%m-%d'))
            else:
                st.warning("⚠️ Dates not detected")
        with col_info4:
            st.metric("Date Range", f"{(forecast_df['Date'].max() - forecast_df['Date'].min()).days} days")
        
        # Check if stations were found
        if not forecast_stations:
            st.error("❌ No stations found in the data. Please check that your file has a 'Station', 'Stations', or 'Station_name' column.")
            st.info("**Available columns:** " + ", ".join(forecast_df.columns.tolist()))
            st.stop()
        
        # Check if metrics were found
        if not available_metrics:
            st.error("❌ No recognized metric columns found in the data.")
            st.info("Expected columns like: Precip M, Tmax M, Tmin M OR Median, UL, LL")
            st.info("**Available columns:** " + ", ".join(forecast_df.columns.tolist()))
            st.stop()
        
        # Station filter
        st.subheader("Station Selection")
        selected_stations = st.multiselect(
            "Select stations to display",
            options=forecast_stations,
            default=forecast_stations[:5] if len(forecast_stations) > 5 else forecast_stations,
            help="Select one or more stations to display in the charts"
        )
        
        # Validate station selection
        if not selected_stations:
            st.warning("⚠️ Please select at least one station to display the charts.")
            st.stop()
        
        # Display options
        col_opt1, col_opt2 = st.columns(2)
        with col_opt1:
            show_historical = st.checkbox("Show historical data", value=False, help="Toggle to show historical data along with forecast")
        with col_opt2:
            show_confidence = st.checkbox("Show confidence intervals (LQ/UQ or LL/UL)", value=True)
        
        # Create tabs based on available metrics
        if 'Precip' in available_metrics and 'Tmax' in available_metrics and 'Tmin' in available_metrics:
            # Standard format with Precip, Tmax, Tmin
            tab_precip, tab_tmax, tab_tmin, tab_data = st.tabs([
                "🌧️ Precipitation",
                "🌡️ Temperature Max",
                "❄️ Temperature Min",
                "📋 Data Table"
            ])
            
            with tab_precip:
                fig = create_forecast_plot(
                    forecast_df,
                    available_metrics['Precip'],
                    'Precipitation (mm)',
                    forecast_start if forecast_start else forecast_df['Date'].min(),
                    selected_stations,
                    show_confidence,
                    show_historical
                )
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.subheader("Summary Statistics")
                    filtered_df = forecast_df[forecast_df['Station'].isin(selected_stations)]
                    if forecast_start:
                        forecast_data = filtered_df[filtered_df['Date'] >= forecast_start]
                    else:
                        forecast_data = filtered_df
                    
                    if not forecast_data.empty:
                        metric_col = available_metrics['Precip']['median']
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Average", f"{forecast_data[metric_col].mean():.2f} mm")
                        with col2:
                            st.metric("Max", f"{forecast_data[metric_col].max():.2f} mm")
                        with col3:
                            st.metric("Total", f"{forecast_data[metric_col].sum():.2f} mm")
            
            with tab_tmax:
                fig = create_forecast_plot(
                    forecast_df,
                    available_metrics['Tmax'],
                    'Temperature Max (°C)',
                    forecast_start if forecast_start else forecast_df['Date'].min(),
                    selected_stations,
                    show_confidence,
                    show_historical
                )
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.subheader("Summary Statistics")
                    filtered_df = forecast_df[forecast_df['Station'].isin(selected_stations)]
                    if forecast_start:
                        forecast_data = filtered_df[filtered_df['Date'] >= forecast_start]
                    else:
                        forecast_data = filtered_df
                    
                    if not forecast_data.empty:
                        metric_col = available_metrics['Tmax']['median']
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Average", f"{forecast_data[metric_col].mean():.2f} °C")
                        with col2:
                            st.metric("Max", f"{forecast_data[metric_col].max():.2f} °C")
                        with col3:
                            st.metric("Min", f"{forecast_data[metric_col].min():.2f} °C")
            
            with tab_tmin:
                fig = create_forecast_plot(
                    forecast_df,
                    available_metrics['Tmin'],
                    'Temperature Min (°C)',
                    forecast_start if forecast_start else forecast_df['Date'].min(),
                    selected_stations,
                    show_confidence,
                    show_historical
                )
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.subheader("Summary Statistics")
                    filtered_df = forecast_df[forecast_df['Station'].isin(selected_stations)]
                    if forecast_start:
                        forecast_data = filtered_df[filtered_df['Date'] >= forecast_start]
                    else:
                        forecast_data = filtered_df
                    
                    if not forecast_data.empty:
                        metric_col = available_metrics['Tmin']['median']
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Average", f"{forecast_data[metric_col].mean():.2f} °C")
                        with col2:
                            st.metric("Max", f"{forecast_data[metric_col].max():.2f} °C")
                        with col3:
                            st.metric("Min", f"{forecast_data[metric_col].min():.2f} °C")
            
            with tab_data:
                st.subheader("Raw Data Preview")
                display_df = forecast_df[forecast_df['Station'].isin(selected_stations)].copy()
                st.dataframe(display_df, height=400, use_container_width=True)
                
                csv = display_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Filtered Data as CSV",
                    data=csv,
                    file_name="forecast_data_filtered.csv",
                    mime="text/csv"
                )
        
        elif 'Generic' in available_metrics:
            # Generic format with Median, UL, LL
            tab_plot, tab_data = st.tabs(["📈 Forecast Plot", "📋 Data Table"])
            
            with tab_plot:
                fig = create_forecast_plot(
                    forecast_df,
                    available_metrics['Generic'],
                    'Forecast Value',
                    forecast_start if forecast_start else forecast_df['Date'].min(),
                    selected_stations,
                    show_confidence,
                    show_historical
                )
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.subheader("Summary Statistics")
                    filtered_df = forecast_df[forecast_df['Station'].isin(selected_stations)]
                    if forecast_start:
                        forecast_data = filtered_df[filtered_df['Date'] >= forecast_start]
                    else:
                        forecast_data = filtered_df
                    
                    if not forecast_data.empty:
                        metric_col = available_metrics['Generic']['median']
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Average", f"{forecast_data[metric_col].mean():.2f}")
                        with col2:
                            st.metric("Max", f"{forecast_data[metric_col].max():.2f}")
                        with col3:
                            st.metric("Min", f"{forecast_data[metric_col].min():.2f}")
                else:
                    st.warning("No data to display for selected stations.")
            
            with tab_data:
                st.subheader("Raw Data Preview")
                display_df = forecast_df[forecast_df['Station'].isin(selected_stations)].copy()
                st.dataframe(display_df, height=400, use_container_width=True)
                
                csv = display_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Filtered Data as CSV",
                    data=csv,
                    file_name="forecast_data_filtered.csv",
                    mime="text/csv"
                )

# ------------ QA/QC DATA DASHBOARD ------------
if qa_file is not None:
    st.header("🔍 QA/QC Data Dashboard")

    qa_df, _auto_basin_to_stations = load_qa_data(qa_file, sheet_name_qa)
    if qa_df is None:
        st.error("Failed to load QA/QC data. Please check your file format.")
    else:
        # Force canonical station ids for all subsequent logic
        qa_df = rekey_to_canonical(qa_df)

        st.sidebar.success(f"✅ Loaded {len(qa_df):,} rows")
        st.sidebar.info(f"📊 {len(new_river_basins)} basins (from dictionary)")
        st.sidebar.info(f"📍 {qa_df['Station_name'].nunique()} unique stations (canonical)")

        all_basins = sorted(new_river_basins.keys())
        metric_options = ["Raw_median", "Step_2_median", "Final_median"]
        available_metrics = [m for m in metric_options if m in qa_df.columns]

        if not available_metrics:
            st.error("No valid metric columns found in the QA/QC data.")
        else:
            col1, col2, col3 = st.columns([1.2, 1.6, 1.1])

            with col1:
                selected_basin = st.selectbox("Basin", options=all_basins, index=0 if all_basins else None)

            # Work out which canonical stations of this basin are present in the data
            basin_stations_all = new_river_basins.get(selected_basin, [])
            basin_stations_present = canonical_stations_present(qa_df, selected_basin)

            with col2:
                if basin_stations_present:
                    default_sel = basin_stations_present  # show all with data by default
                else:
                    default_sel = []
                selected_qa_stations = st.multiselect(
                    "Stations",
                    options=basin_stations_all,    # show dictionary order
                    default=default_sel,
                    help="Only stations with data will plot"
                )

            with col3:
                selected_metrics = st.multiselect(
                    "Metric(s)",
                    options=available_metrics,
                    default=[available_metrics[0]] if available_metrics else []
                )

            # Subset for basin + selected stations (canonical)
            if selected_basin and selected_qa_stations:
                sub = qa_df[
                    (qa_df["River_basin_name"] == selected_basin) &
                    (qa_df["Station_name"].isin(selected_qa_stations))
                ].copy()
            else:
                sub = pd.DataFrame()

            tab1, tab2, tab3, tab4 = st.tabs([
                "📈 Time-series",
                "📊 Pairwise Differences",
                "🔄 BC vs Observation",
                "📋 Per-Station Summary"
            ])

            # ------------- Time-series -------------
# ------------- Time-series -------------
with tab1:
    if sub.empty:
        st.warning("Select at least one station to view data.")
    elif not selected_metrics:
        st.warning("Select at least one metric.")
    else:
        # 1) Build frames (one per metric)
        frames = []
        for m in selected_metrics:
            if m in sub.columns:
                frames.append(
                    sub[["Date", "Station_name", m]]
                    .rename(columns={m: "Flow"})
                    .assign(Metric=m)
                )

        if not frames:
            st.warning("No matching metric columns found for plotting.")
        else:
            plot_df = pd.concat(frames, ignore_index=True)

            # 2) Enforce legend order = dictionary order (for the selected basin)
            dict_order = new_river_basins.get(selected_basin, [])
            # keep only stations actually selected
            legend_order = [s for s in dict_order if s in selected_qa_stations]

            # Make Station_name and Metric categorical with desired order
            plot_df["Station_name"] = pd.Categorical(
                plot_df["Station_name"], categories=legend_order, ordered=True
            )
            plot_df["Metric"] = pd.Categorical(
                plot_df["Metric"], categories=selected_metrics, ordered=True
            )

            # Sort rows so traces are created in the desired order
            plot_df = plot_df.sort_values(["Station_name", "Metric", "Date"])

            # 3) Plot with explicit category_orders so Plotly keeps that order in the legend
            fig = px.line(
                plot_df,
                x="Date",
                y="Flow",
                color="Station_name",
                line_dash="Metric",
                markers=True,
                title=f"{selected_basin} – Time Series",
                category_orders={
                    "Station_name": legend_order,
                    "Metric": list(selected_metrics)
                },
            )

            # Group traces by station and keep the creation order → legend follows dict order
            fig.update_layout(
                legend_title_text="Station • Metric",
                legend_traceorder="grouped",  # group by Station_name in the legend
                yaxis_title="Flow (CMS)",
                height=600,
            )

            st.plotly_chart(fig, use_container_width=True)

            # ------------- Pairwise Differences -------------
            with tab2:
                if sub.empty:
                    st.warning("Select at least one station to view differences.")
                else:
                    # Use dictionary order for this basin
                    dict_order = [s for s in new_river_basins.get(selected_basin, []) if s in sub["Station_name"].unique()]
                    if len(dict_order) < 2:
                        st.info("Need at least two stations (with data) in this basin to compute pairwise differences.")
                    else:
                        cA, cB, cM = st.columns(3)
                        with cM:
                            diff_metric = st.selectbox("Difference metric", options=available_metrics, index=0)
                        with cA:
                            up_station = st.selectbox(
                                "Upstream (optional)",
                                options=[None] + dict_order,
                                format_func=lambda x: "(Auto: consecutive pairs)" if x is None else x
                            )
                        with cB:
                            down_station = st.selectbox(
                                "Downstream (optional)",
                                options=[None] + dict_order,
                                format_func=lambda x: "(Auto)" if x is None else x
                            )

                        st.markdown("---")

                        # Helper: wide frame with columns in dictionary order
                        wide = (
                            qa_df[
                                (qa_df["River_basin_name"] == selected_basin) &
                                (qa_df["Station_name"].isin(dict_order))
                            ]
                            .pivot_table(index="Date", columns="Station_name", values=diff_metric, aggfunc="first")
                            .reindex(columns=dict_order)
                            .sort_index()
                        )

                        if up_station and down_station and up_station != down_station:
                            if up_station not in wide.columns or down_station not in wide.columns:
                                st.warning("Selected pair has no overlapping data.")
                            else:
                                m = pd.DataFrame({
                                    "Date": wide.index,
                                    "Diff": wide[up_station] - wide[down_station]
                                })
                                fig = px.line(
                                    m, x="Date", y="Diff",
                                    title=f"{selected_basin} – Difference ({diff_metric}): {up_station} - {down_station}",
                                    markers=True
                                )
                                fig.update_layout(yaxis_title="Difference (CMS)", height=600)
                                st.plotly_chart(fig, use_container_width=True)
                        else:
                            # Auto: D1=A-B, D2=B-C, ... in dict order
                            rows = []
                            for i in range(len(dict_order) - 1):
                                a, b = dict_order[i], dict_order[i + 1]
                                if a in wide.columns and b in wide.columns:
                                    series = (wide[a] - wide[b]).rename(f"D{i+1}: {a} - {b}")
                                    rows.append(series)
                            if rows:
                                diff_df = pd.concat(rows, axis=1).reset_index()
                                long_df = diff_df.melt("Date", var_name="Pair", value_name="Diff")
                                fig = px.line(
                                    long_df, x="Date", y="Diff", color="Pair",
                                    title=f"{selected_basin} – Consecutive Pairwise Differences ({diff_metric})",
                                    markers=True
                                )
                                fig.update_layout(yaxis_title="Difference (CMS)", height=600)
                                st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.info("No overlapping data between consecutive stations for the chosen metric.")

            # ------------- BC vs Observation -------------
            with tab3:
                if sub.empty:
                    st.warning("Select at least one station to view data.")
                elif "OBS" not in sub.columns or "BC_Factor" not in sub.columns:
                    st.warning("OBS / BC_Factor columns not found in the data.")
                else:
                    fig = px.scatter(
                        sub, x="OBS", y="BC_Factor",
                        color="Station_name",
                        trendline="ols", trendline_scope="overall",
                        title=f"{selected_basin} – BC Factor vs OBS"
                    )
                    fig.update_layout(xaxis_title="OBS", yaxis_title="BC_Factor", height=600)
                    st.plotly_chart(fig, use_container_width=True)

            # ------------- Per-Station Summary -------------
            with tab4:
                if sub.empty:
                    st.warning("Select at least one station to view summary.")
                else:
                    summary_metrics = [m for m in ["Raw_median", "Step_2_median", "Final_median"] if m in sub.columns]
                    if summary_metrics:
                        sums = sub.groupby("Station_name")[summary_metrics].sum(min_count=1).reset_index()
                        avgs = sub.groupby("Station_name")[summary_metrics].mean().reset_index()
                        sums["Type"] = "Sum"
                        avgs["Type"] = "Average"
                        summary = pd.concat([sums, avgs], ignore_index=True)
                        summary = summary.melt(id_vars=["Station_name", "Type"], value_vars=summary_metrics,
                                              var_name="Metric", value_name="Value")
                        fig = px.bar(
                            summary, x="Station_name", y="Value", color="Metric",
                            facet_col="Type", barmode="group",
                            title=f"{selected_basin} – Per-Station Sums & Averages"
                        )
                        fig.update_layout(yaxis_title="Flow (CMS)", height=600)
                        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.caption("WRMM Forecast Explorer | Built with Streamlit | 🌊 Upload your data to get started")