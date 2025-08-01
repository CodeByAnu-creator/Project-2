import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text # Corrected: Import 'text' from sqlalchemy
import pymysql # Required by SQLAlchemy for MySQL connection, even if not directly used
import plotly.express as px
import plotly.express as px

# --- Database Connection Configuration ---
DB_CONFIG = {
    'host': 'localhost',        
    'user': 'root', 
    'password': 'God%40%239999', 
    'database': 'ola'  }

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
    round(AVG(Customer_Rating),2) AS Average_Customer_Rating
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








# --- Section: All Successful Bookings ---
st.header("✅ All Successful Bookings")
st.markdown("Displays a table of all rides with 'Success' status.")

successful_bookings_query = """
SELECT
    Booking_ID,
    Customer_ID,
    Vehicle_Type,
    Pickup_Location,
    Drop_Location,
    Booking_Value,
    Payment_Method,
    Ride_Distance,
    Timestamp
FROM
    ola_rides_tbl
WHERE
    Booking_Status = 'Success'
LIMIT 100; -- Limiting to 100 rows for display efficiency in Streamlit
"""
successful_bookings_df = run_query(successful_bookings_query)

if not successful_bookings_df.empty:
    st.dataframe(successful_bookings_df, use_container_width=True)
    st.info("Displayed the first 100 successful bookings for performance.")
else:
    st.info("No successful bookings found.")

st.markdown("---")







# --- Section: Average Ride Distance by Vehicle Type ---
st.header("📏 Average Ride Distance by Vehicle Type")
avg_ride_distance_query = """
SELECT
    Vehicle_Type,
    AVG(Ride_Distance) AS Average_Ride_Distance
FROM
    ola_rides_tbl
GROUP BY
    Vehicle_Type
ORDER BY
    Average_Ride_Distance DESC;
"""
avg_ride_distance_df = run_query(avg_ride_distance_query)


'''
if not avg_ride_distance_df.empty:
    st.dataframe(avg_ride_distance_df, use_container_width=True)
    st.bar_chart(avg_ride_distance_df.set_index('Vehicle_Type'))
else:
    st.info("No data available for Average Ride Distance by Vehicle Type.")

st.markdown("---")
'''
if not avg_ride_distance_df.empty:
    st.dataframe(avg_ride_distance_df, use_container_width=True)

    st.subheader("Average Ride Distance by Vehicle Type (Horizontal Bar Chart)")
    fig_horizontal_bar = px.bar(
        avg_ride_distance_df,
        x='Average_Ride_Distance',
        y='Vehicle_Type',
        orientation='h', # This makes it horizontal
        title='Average Ride Distance by Vehicle Type',
        labels={'Average_Ride_Distance': 'Average Distance (km)', 'Vehicle_Type': 'Vehicle Type'},
        color='Average_Ride_Distance', # Color bars by distance for emphasis
        color_continuous_scale=px.colors.sequential.Plasma # Or another color scale
    )
    fig_horizontal_bar.update_layout(showlegend=False) # Hide color bar legend if not necessary
    st.plotly_chart(fig_horizontal_bar, use_container_width=True)
else:
    st.info("No data available for Average Ride Distance by Vehicle Type.")







# --- Section: Total Customer Cancelled Rides ---
st.header("❌ Total Customer Cancelled Rides")
customer_cancelled_rides_query = """
SELECT COUNT(*) AS Total_Customer_Cancelled_Rides
FROM ola_rides_tbl
WHERE booking_status = 'Canceled by Customer';
    
"""
customer_cancelled_rides_df = run_query(customer_cancelled_rides_query)

if not customer_cancelled_rides_df.empty:
    total_cancelled = customer_cancelled_rides_df.iloc[0, 0]
    st.metric(label="Total Rides Cancelled by Customers", value=total_cancelled)
else:
    st.info("No data available for customer cancelled rides.")

st.markdown("---")








# --- Section: Total Driver Cancellations for Specific Reasons ---
st.header("🚫 Total Driver Cancellations (Personal/Car Issues)")
driver_cancelled_query = """
SELECT
    COUNT(*) AS Total_Rides_Cancelled
FROM
    ola_rides_tbl
where booking_status = 'Canceled by Driver' and Canceled_Rides_by_Driver = 'Personal & Car related issue';
"""
driver_cancelled_df = run_query(driver_cancelled_query)

if not driver_cancelled_df.empty:
    total_cancelled = driver_cancelled_df.iloc[0, 0]
    st.metric(label="Total Driver Cancellations (Personal/Car Issues)", value=total_cancelled)
else:
    st.info("No driver cancelled rides found for personal or car-related issues.")

st.markdown("---")









# --- Section: Driver Cancellations Trend ---
st.header("📈 Driver Cancellation Trend (Personal/Car Issues)")
trend_query = """
SELECT
    DATE(Timestamp) AS Cancellation_Date,
    COUNT(*) AS Total_Cancellations
FROM
    ola_rides_tbl
WHERE
    Is_Driver_Canceled = TRUE
    AND (
        Canceled_Rides_by_Driver LIKE '%%personal%%'
        OR Canceled_Rides_by_Driver LIKE '%%car%%'
        OR Canceled_Rides_by_Driver LIKE '%%vehicle%%'
        OR Canceled_Rides_by_Driver LIKE '%%breakdown%%'
        OR Canceled_Rides_by_Driver LIKE '%%maintenance%%'
    )
GROUP BY
    Cancellation_Date
ORDER BY
    Cancellation_Date;
"""
trend_df = run_query(trend_query)

if not trend_df.empty:
    trend_df['Cancellation_Date'] = pd.to_datetime(trend_df['Cancellation_Date'])
    st.line_chart(trend_df.set_index('Cancellation_Date'))
else:
    st.info("No data available to show driver cancellation trends.")
st.markdown("---")


# --- Section: Driver Ratings for Prime Sedan Bookings ---
st.header("⭐ Driver Ratings for Prime Sedan Bookings")

ratings_query = """
SELECT
    MAX(Driver_Ratings) AS Max_Driver_Rating,
    MIN(Driver_Ratings) AS Min_Driver_Rating
FROM
    ola_rides_tbl
WHERE
    Vehicle_Type = 'Prime Sedan';
"""

ratings_df = run_query(ratings_query)

if not ratings_df.empty and ratings_df.iloc[0]['Max_Driver_Rating'] is not None:
    # Use st.columns to display metrics and the chart
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Maximum Driver Rating", value=ratings_df.iloc[0]['Max_Driver_Rating'])
    with col2:
        st.metric(label="Minimum Driver Rating", value=ratings_df.iloc[0]['Min_Driver_Rating'])

    st.markdown("### Comparison of Ratings")
    # Reshape the DataFrame for plotting
    plot_df = ratings_df.T.reset_index()
    plot_df.columns = ['Rating_Type', 'Rating_Value']

    fig = px.bar(
        plot_df,
        x='Rating_Type',
        y='Rating_Value',
        color='Rating_Type',
        title='Max vs. Min Driver Ratings for Prime Sedan',
        labels={'Rating_Value': 'Rating', 'Rating_Type': ''}
    )
    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("No Prime Sedan booking data available to calculate ratings.")

st.markdown("---")





# --- Section: Rides Paid via UPI ---
st.header("💳 Rides Paid via UPI")
st.markdown("Displays all rides where the payment method was 'UPI'.")

upi_rides_query = """
SELECT
    Booking_ID,
    Customer_ID,
    Vehicle_Type,
    Pickup_Location,
    Drop_Location,
    Booking_Value,
    Ride_Distance,
    Timestamp
FROM
    ola_rides_tbl
WHERE
    Payment_Method = 'UPI'
LIMIT 100; -- Limiting to 100 rows for display efficiency in Streamlit
"""
upi_rides_df = run_query(upi_rides_query)

if not upi_rides_df.empty:
    st.dataframe(upi_rides_df, use_container_width=True)
    st.info("Displayed the first 100 UPI-paid rides for performance.")
else:
    st.info("No rides found with UPI as the payment method.")

st.markdown("---")





# --- Section: UPI Usage Trend Over Time ---
st.header("📈 UPI Usage Trend Over Time")
upi_trend_query = """
SELECT
    DATE(Timestamp) AS Ride_Date,
    COUNT(*) AS Total_UPI_Rides
FROM
    ola_rides_tbl
WHERE
    Payment_Method = 'UPI'
GROUP BY
    Ride_Date
ORDER BY
    Ride_Date;
"""
upi_trend_df = run_query(upi_trend_query)

if not upi_trend_df.empty:
    # Ensure 'Ride_Date' is a datetime object for proper plotting
    upi_trend_df['Ride_Date'] = pd.to_datetime(upi_trend_df['Ride_Date'])
    st.line_chart(upi_trend_df.set_index('Ride_Date'))
else:
    st.info("No UPI ride data available to show trends.")

st.markdown("---")








# --- Section: Average Booking Value (UPI) ---
st.header("💰 Average Booking Value for UPI Rides")
upi_value_query = """
SELECT
    AVG(Booking_Value) AS Average_UPI_Booking_Value
FROM
    ola_rides_tbl
WHERE
    Payment_Method = 'UPI'
    AND Booking_Status = 'Success';
"""
upi_value_df = run_query(upi_value_query)

if not upi_value_df.empty and upi_value_df.iloc[0, 0] is not None:
    avg_value = upi_value_df.iloc[0, 0]
    st.metric(label="Average Booking Value for UPI", value=f"₹{avg_value:,.2f}")
else:
    st.info("No successful UPI rides found to calculate average booking value.")

st.markdown("---")









# --- Section: Total Booking Value of Successful Rides ---
st.header("💰 Total Booking Value (Successful Rides)")
total_booking_value_query = """
SELECT
    SUM(Booking_Value) AS Total_Successful_Booking_Value
FROM
    ola_rides_tbl
WHERE
    Booking_Status = 'Success';
"""
total_booking_value_df = run_query(total_booking_value_query)

if not total_booking_value_df.empty and total_booking_value_df.iloc[0, 0] is not None:
    total_value = total_booking_value_df.iloc[0, 0]
    st.metric(label="Total Booking Value", value=f"₹{total_value:,.2f}")
else:
    st.info("No successful rides found to calculate total booking value.")

st.markdown("---")





# --- Section: Incomplete Rides and Reasons ---
st.header("⚠️ Incomplete Rides")
st.markdown("Details of rides that were not completed, along with the reason.")

incomplete_rides_query = """
SELECT
    Booking_ID,
    Incomplete_Rides_Reason
FROM
    ola_rides_tbl
WHERE
    Is_Incomplete = TRUE
LIMIT 100; -- Limiting to 100 rows for display efficiency in Streamlit
"""
incomplete_rides_df = run_query(incomplete_rides_query)

if not incomplete_rides_df.empty:
    st.dataframe(incomplete_rides_df, use_container_width=True)
    st.info("Displayed the first 100 incomplete rides for performance.")
else:
    st.info("No incomplete rides found.")

st.markdown("---")

import plotly.express as px # Make sure you have this import at the top of your file






# --- Section: Incomplete Ride Reasons Pie Chart ---
st.header("📊 Distribution of Incomplete Ride Reasons")
st.markdown("Shows the proportion of each reason for incomplete rides.")

incomplete_reasons_query = """
SELECT
    Incomplete_Rides_Reason,
    COUNT(*) AS Total_Count
FROM
    ola_rides_tbl
WHERE
    Is_Incomplete = TRUE
GROUP BY
    Incomplete_Rides_Reason
ORDER BY
    Total_Count DESC;
"""
incomplete_reasons_df = run_query(incomplete_reasons_query)

if not incomplete_reasons_df.empty:
    # Use Plotly Express to create a pie chart
    fig = px.pie(
        incomplete_reasons_df,
        values='Total_Count',
        names='Incomplete_Rides_Reason',
        title='Distribution of Incomplete Ride Reasons',
        hole=0.3 # Creates a donut chart style
    )
    fig.update_traces(textposition='inside', textinfo='percent+label') # Display percentage and label inside slices
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No incomplete rides found to generate the pie chart.")

st.markdown("---")









# --- Section: Revenue by Payment Method ---
st.header("💰 Revenue by Payment Method")
st.markdown("Shows the total booking value generated by each payment method.")

revenue_by_method_query = """
SELECT
    Payment_Method,
    SUM(Booking_Value) AS Total_Revenue
FROM
    ola_rides_tbl
WHERE
    Booking_Status = 'Success' -- Only count revenue from successful rides
GROUP BY
    Payment_Method
ORDER BY
    Total_Revenue DESC;
"""
revenue_by_method_df = run_query(revenue_by_method_query)

if not revenue_by_method_df.empty:
    st.dataframe(revenue_by_method_df, use_container_width=True)
    st.bar_chart(revenue_by_method_df.set_index('Payment_Method'))
else:
    st.info("No successful ride data available to calculate revenue.")

st.markdown("---")





# --- Project Information Section ---
st.sidebar.subheader("Project Details")
st.sidebar.info(
    "**Project Title:** Ola Ride Insights\n\n"
    "**Domain:** Ride-Sharing & Mobility Analytics\n\n"
    "This application provides key insights from OLA ride data."
)

