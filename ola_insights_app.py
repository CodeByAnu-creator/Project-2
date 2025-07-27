import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text # Corrected: Import 'text' from sqlalchemy
import pymysql # Required by SQLAlchemy for MySQL connection, even if not directly used

# --- Database Connection Configuration ---
# IMPORTANT: Replace with your actual MySQL credentials
DB_CONFIG = {
    'host': 'localhost',        # Or your MySQL server IP (e.g., '127.0.0.1')
    'user': 'root', # e.g., 'root'
    'password': 'God%40%239999', # e.g., 'password'
    'database': 'ola'  # Your database name
}

# --- Cached Database Engine Creation ---
# @st.cache_resource caches the SQLAlchemy engine, so it's created only once.
@st.cache_resource
def get_db_engine():
    """
    Creates and returns a SQLAlchemy engine for connecting to the MySQL database.
    """
    # Construct the database URI for SQLAlchemy
    # Format: 'mysql+pymysql://user:password@host/database_name'
    db_uri = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}"
    try:
        engine = create_engine(db_uri)
        # Attempt to connect to test the engine
        with engine.connect() as connection:
            # Corrected: Use 'text' imported from sqlalchemy, not 'pd.text'
            connection.execute(text("SELECT 1"))
        st.success("Successfully connected to MySQL database!")
        return engine
    except Exception as e:
        st.error(f"Error connecting to MySQL database: {e}")
        st.stop() # Stop the app if connection fails

# --- Function to Run SQL Queries ---
def run_query(query):
    """
    Executes a given SQL query and returns the result as a pandas DataFrame.
    """
    engine = get_db_engine()
    try:
        # pd.read_sql works seamlessly with a SQLAlchemy engine
        df = pd.read_sql(query, engine)
        return df
    except Exception as e:
        st.error(f"Error executing query: {e}")
        return pd.DataFrame() # Return empty DataFrame on query error

# --- Function to get unique values for filters ---
@st.cache_data # Cache data to avoid re-running query on every interaction
def get_unique_column_values(column_name, table_name="ola_rides_tbl"):
    """
    Fetches unique values from a specified column in a given table for use in filters.
    """
    query = f"SELECT DISTINCT {column_name} FROM {table_name} ORDER BY {column_name};"
    df = run_query(query)
    # Convert to a list, filter out None/NaN if necessary, and ensure correct data type
    return [str(item) for item in df[column_name].dropna().unique()]


# --- Streamlit App Layout ---
st.set_page_config(
    layout="wide",
    page_title="Ola Ride Insights",
    initial_sidebar_state="expanded"
)

# Sidebar for navigation or filters (optional, but good for larger apps)
with st.sidebar:
    st.header("Navigation")
    st.write("Explore different insights:")
    # You can add radio buttons or select boxes here for different sections/pages
    # For now, we'll just have static content

st.title("Ola Ride Insights Dashboard")
st.markdown("A comprehensive analysis of OLA ride-sharing data.")
st.markdown("---")

# --- Section 1: Top 5 Customers by Total Rides Booked ---
st.header("📊 Top 5 Customers by Total Rides Booked")
top_customers_query = """
SELECT
    Customer_ID,
    COUNT(Booking_ID) AS Total_Rides_Booked
FROM
    ola_rides_tbl
GROUP BY
    Customer_ID
ORDER BY
    Total_Rides_Booked DESC
LIMIT 5;
"""
top_customers_df = run_query(top_customers_query)

if not top_customers_df.empty:
    st.dataframe(top_customers_df, use_container_width=True)
else:
    st.info("No data available for Top 5 Customers.")

st.markdown("---")

# --- Section 2: Average Customer Ratings by Vehicle Type (with Filter) ---
st.header("⭐ Average Customer Ratings by Vehicle Type")

# Get unique vehicle types for the filter
vehicle_types = get_unique_column_values("Vehicle_Type")
# Add an "All" option to the filter
selected_vehicle_type = st.selectbox(
    "Select Vehicle Type for Average Rating:",
    ["All"] + vehicle_types,
    index=0 # Default to "All"
)

# Modify the query based on selection
avg_customer_rating_query = f"""
SELECT
    Vehicle_Type,
    AVG(Customer_Rating) AS Average_Customer_Rating
FROM
    ola_rides_tbl
WHERE
    Customer_Rating IS NOT NULL
"""
if selected_vehicle_type != "All":
    # Ensure proper escaping for SQL string literals if Vehicle_Type contains single quotes
    avg_customer_rating_query += f" AND Vehicle_Type = '{selected_vehicle_type.replace("'", "''")}'"

avg_customer_rating_query += """
GROUP BY
    Vehicle_Type
ORDER BY
    Average_Customer_Rating DESC;
"""
avg_customer_rating_df = run_query(avg_customer_rating_query)

if not avg_customer_rating_df.empty:
    st.dataframe(avg_customer_rating_df, use_container_width=True)
    # Optional: Add a bar chart visualization
    st.bar_chart(avg_customer_rating_df.set_index('Vehicle_Type'))
else:
    st.info("No data available for Average Customer Ratings by Vehicle Type with current filters.")

st.markdown("---")

# --- Section 3: Ride Volume Over Time (Example Placeholder for Power BI type visuals) ---
st.header("📈 Ride Volume Over Time")
st.write("This section typically features an interactive chart showing ride trends over time.")

# Example for a simple time-series chart generated directly in Streamlit
ride_volume_query = """
SELECT
    DATE(Timestamp) AS Ride_Date,
    COUNT(Booking_ID) AS Daily_Rides
FROM
    ola_rides_tbl
GROUP BY
    DATE(Timestamp)
ORDER BY
    Ride_Date;
"""
ride_volume_df = run_query(ride_volume_query)

if not ride_volume_df.empty:
    # Ensure 'Ride_Date' is a datetime object for proper plotting if not already
    ride_volume_df['Ride_Date'] = pd.to_datetime(ride_volume_df['Ride_Date'])
    st.line_chart(ride_volume_df.set_index('Ride_Date'))
else:
    st.info("No data available for Ride Volume Over Time.")

st.markdown("---")

# --- Project Information Section ---
st.sidebar.subheader("Project Details")
st.sidebar.info(
    "**Project Title:** Ola Ride Insights\n\n"
    "**Domain:** Ride-Sharing & Mobility Analytics\n\n"
    "This application provides key insights from OLA ride data."
)

st.caption("Developed as part of the Ola Ride Insights Project.")






















