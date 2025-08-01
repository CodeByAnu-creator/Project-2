import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text # Corrected: Import 'text' from sqlalchemy
import pymysql # Required by SQLAlchemy for MySQL connection, even if not directly used
import plotly.express as px

# --- Database Connection Configuration ---
# The app now securely fetches credentials from Streamlit secrets.
# You must set these up in your Streamlit Community Cloud dashboard or in a
# .streamlit/secrets.toml file if running locally.
# Example secrets.toml:
# [mysql]
# host = "your_mysql_host.com"
# user = "your_mysql_username"
# password = "your_mysql_password"
# database = "ola_rides_db"


# --- Cached Database Engine Creation ---
@st.cache_resource
def get_db_engine():
    """
    Creates and returns a SQLAlchemy engine for connecting to the MySQL database.
    This function now uses Streamlit secrets for credentials.
    """
    db_uri = f"mysql+pymysql://{st.secrets['mysql']['user']}:{st.secrets['mysql']['password']}@{st.secrets['mysql']['host']}/{st.secrets['mysql']['database']}"
    try:
        engine = create_engine(db_uri)
        # Test the connection by executing a simple query
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        st.success("Successfully connected to MySQL database!")
        return engine
    except Exception as e:
        st.error(f"Error connecting to MySQL database. Please check your credentials: {e}")
        st.stop()

# --- Function to Run SQL Queries ---
def run_query(query):
    """
    Executes a given SQL query and returns the result as a pandas DataFrame.
    """
    engine = get_db_engine()
    try:
        df = pd.read_sql(query, engine)
        return df
    except Exception as e:
        st.error(f"Error executing query: {e}")
        return pd.DataFrame()

# --- Function to get unique values for filters ---
@st.cache_data
def get_unique_column_values(column_name, table_name="ola_rides_tbl"):
    """
    Fetches unique values from a specified column in a given table for use in filters.
    """
    query = f"SELECT DISTINCT {column_name} FROM {table_name} ORDER BY {column_name};"
    df = run_query(query)
    return [str(item) for item in df[column_name].dropna().unique()]

# --- Set Streamlit Page Configuration ---
st.set_page_config(
    layout="wide",
    page_title="Ola Ride Insights",
    initial_sidebar_state="expanded"
)

# --- Top-level Horizontal Navigation ---
page = st.radio(
    "Choose a page:",
    ["Home", "Insights"],
    index=0,
    horizontal=True,
    label_visibility="hidden"
)

if page == "Home":
    st.title("🏡 OLA Ride Insights Project Overview")

    st.markdown("""
        This dashboard provides a high-level overview and key insights from a comprehensive analysis of OLA ride-sharing data.
        It serves as a single source of truth for tracking performance, customer behavior, and operational trends.
        Use the 'Insights' tab above for a deeper, section-by-section analysis.
        ---
    """)

    # --- Home Page Key Metrics ---
    st.header("Key Performance Indicators")
    col1, col2, col3 = st.columns(3)

    # Total Rides Metric
    total_rides_query = "SELECT COUNT(*) FROM ola_rides_tbl;"
    total_rides = run_query(total_rides_query).iloc[0, 0]
    col1.metric(label="Total Rides", value=f"{total_rides:,}")

    # Total Successful Rides Metric
    successful_rides_query = "SELECT COUNT(*) FROM ola_rides_tbl WHERE Booking_Status = 'Success';"
    successful_rides = run_query(successful_rides_query).iloc[0, 0]
    col2.metric(label="Successful Rides", value=f"{successful_rides:,}")

    # Total Revenue Metric
    total_revenue_query = "SELECT SUM(Booking_Value) FROM ola_rides_tbl WHERE Booking_Status = 'Success';"
    total_revenue = run_query(total_revenue_query).iloc[0, 0]
    col3.metric(label="Total Revenue", value=f"₹{total_revenue:,.2f}")

    st.markdown("---")

    # --- At-a-Glance Visualizations ---
    st.header("At-a-Glance Insights")

    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Booking Status Distribution")
        booking_status_query = """
        SELECT
            Booking_Status,
            COUNT(Booking_ID) AS Total_Bookings
        FROM
            ola_rides_tbl
        GROUP BY
            Booking_Status;
        """
        booking_status_df = run_query(booking_status_query)
        if not booking_status_df.empty:
            fig = px.pie(
                booking_status_df,
                values='Total_Bookings',
                names='Booking_Status',
                title='Overall Ride Outcome Distribution',
                hole=0.3
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.subheader("Ride Volume Over Time")
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
            ride_volume_df['Ride_Date'] = pd.to_datetime(ride_volume_df['Ride_Date'])
            st.line_chart(ride_volume_df.set_index('Ride_Date'))

elif page == "Insights":
    st.title("📊 Detailed OLA Ride Insights Dashboard")

    # --- Left-side Radio Button Navigation for Insights Page ---
    st.sidebar.title("Insights Navigation")
    insight_selection = st.sidebar.radio("Jump to Section:", [
        "Top Customers by Rides",
        "Top Customers by Revenue",
        "Average Ratings by Vehicle Type",
        "Average Ride Distance by Vehicle Type",
        "Driver Cancellation Reasons",
        "Driver Cancellation Trend",
        "Revenue by Payment Method",
        "Rides Paid via UPI",
        "UPI Usage Trend",
        "Average UPI Booking Value",
        "Prime Sedan Driver Ratings",
        "Incomplete Ride Reasons",
        "Total Cancellations",
        "Successful Bookings"
    ])

    if insight_selection == "Top Customers by Rides":
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
            st.bar_chart(top_customers_df.set_index('Customer_ID'))
        else:
            st.info("No data available for Top 5 Customers.")

    elif insight_selection == "Top Customers by Revenue":
        st.header("👑 Top 5 Customers by Total Booking Value")
        top_customers_by_value_query = """
        SELECT
            Customer_ID,
            SUM(Booking_Value) AS Total_Booking_Value
        FROM
            ola_rides_tbl
        WHERE
            Booking_Status = 'Success'
        GROUP BY
            Customer_ID
        ORDER BY
            Total_Booking_Value DESC
        LIMIT 5;
        """
        top_customers_by_value_df = run_query(top_customers_by_value_query)
        if not top_customers_by_value_df.empty:
            st.dataframe(top_customers_by_value_df, use_container_width=True)
            st.bar_chart(top_customers_by_value_df.set_index('Customer_ID'))
        else:
            st.info("No successful rides found to identify top customers by value.")

    elif insight_selection == "Average Ratings by Vehicle Type":
        st.header("⭐ Average Customer Ratings by Vehicle Type")
        vehicle_types = get_unique_column_values("Vehicle_Type")
        selected_vehicle_type = st.selectbox(
            "Select Vehicle Type for Average Rating:",
            ["All"] + vehicle_types,
            index=0
        )
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
            st.bar_chart(avg_customer_rating_df.set_index('Vehicle_Type'))
        else:
            st.info("No data available for Average Customer Ratings by Vehicle Type with current filters.")

    elif insight_selection == "Average Ride Distance by Vehicle Type":
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

    elif insight_selection == "Driver Cancellation Reasons":
        st.header("🚫 Breakdown of Driver Cancellation Reasons")
        reasons_query = """
        SELECT
            Canceled_Rides_by_Driver,
            COUNT(*) AS Total_Count
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
            Canceled_Rides_by_Driver
        ORDER BY
            Total_Count DESC;
        """
        reasons_df = run_query(reasons_query)
        if not reasons_df.empty:
            st.dataframe(reasons_df, use_container_width=True)
            st.bar_chart(reasons_df.set_index('Canceled_Rides_by_Driver'))
        else:
            st.info("No specific reasons found for these driver cancellations.")

    elif insight_selection == "Driver Cancellation Trend":
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

    elif insight_selection == "Revenue by Payment Method":
        st.header("💰 Revenue by Payment Method")
        revenue_by_method_query = """
        SELECT
            Payment_Method,
            SUM(Booking_Value) AS Total_Revenue
        FROM
            ola_rides_tbl
        WHERE
            Booking_Status = 'Success'
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




    elif insight_selection == "Rides Paid via UPI":
        st.header("📈 Payment done through UPI")
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




    elif insight_selection == "UPI Usage Trend":
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
            upi_trend_df['Ride_Date'] = pd.to_datetime(upi_trend_df['Ride_Date'])
            st.line_chart(upi_trend_df.set_index('Ride_Date'))
        else:
            st.info("No UPI ride data available to show trends.")



    elif insight_selection == "Average UPI Booking Value":
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

    elif insight_selection == "Prime Sedan Driver Ratings":
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
            col1, col2 = st.columns(2)
            with col1:
                st.metric(label="Maximum Driver Rating", value=ratings_df.iloc[0]['Max_Driver_Rating'])
            with col2:
                st.metric(label="Minimum Driver Rating", value=ratings_df.iloc[0]['Min_Driver_Rating'])
            st.markdown("### Comparison of Ratings")
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

    elif insight_selection == "Incomplete Ride Reasons":
        st.header("📊 Distribution of Incomplete Ride Reasons")

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
            fig = px.pie(
                incomplete_reasons_df,
                values='Total_Count',
                names='Incomplete_Rides_Reason',
                title='Distribution of Incomplete Ride Reasons',
                hole=0.3
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No incomplete rides found to generate the pie chart.")

    elif insight_selection == "Total Cancellations":
        st.header("Total Cancellations & Incomplete Rides")
        col1, col2 = st.columns(2)
        with col1:
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
        with col2:
            incomplete_rides_query = """
            SELECT
                COUNT(*) AS Total_Incomplete_Rides
            FROM
                ola_rides_tbl
            WHERE
                Is_Incomplete = TRUE;
            """
            incomplete_rides_df = run_query(incomplete_rides_query)
            if not incomplete_rides_df.empty:
                total_incomplete = incomplete_rides_df.iloc[0, 0]
                st.metric(label="Total Incomplete Rides", value=total_incomplete)
            else:
                st.info("No incomplete rides found.")












    elif insight_selection == "Successful Bookings":
        st.header("All Successful Ola Bookings")
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









