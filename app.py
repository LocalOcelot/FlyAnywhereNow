import streamlit as st
from flight_search import FlightSearch
import data_utilities

# Initialize your core services
fs = FlightSearch()

def refresh_on_sort(flights, sort_by):
    if sort_by == "Price":
        return fs.sort_by_price(flights)
    return sorted(flights, key=lambda f: f.outbound_duration)

def render_ui():
    st.set_page_config(page_title="FlyAnywhereNow", layout="wide")

    st.markdown("<h1 style='text-align: center;'>✈️ FlyAnywhereNow</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>No plan. No destination. Just go.</p>", unsafe_allow_html=True)

    st.divider()

    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)

    with col1:
        df = data_utilities.load_all_airports()
        countries = ["Choose a country..."] + sorted(df["country_name"].unique().tolist())
        selected_country = st.selectbox("Country", countries)

    with col2:
        if selected_country == "Choose a country...":
            airport = None
            st.selectbox("Airport", ["Select country first..."], disabled=True)
        else:
            airport_options = data_utilities.get_airport_options_by_country(df, selected_country)
            selected = st.selectbox("Airport", ["Choose an airport..."] + list(airport_options.keys()))
            
            if selected == "Choose an airport...":
                airport = None
            else:
                airport = airport_options[selected]

    # Resolve currency metrics first to customize slider label interfaces dynamically
    if selected_country and selected_country != "Choose a country...":
        currency_code, currency_symbol, exchange_rate = data_utilities.get_currency_details(selected_country)
    else:
        currency_symbol = "£"
        exchange_rate = 1.0

    with col3:
        max_price = st.slider(f"Max Price ({currency_symbol})", 0, 1000, 500)
    with col4:
        max_duration = st.slider("Max Duration (hrs)", 1, 48, 24)
    with col5:
        international_only = st.toggle("International Only")
    with col6:
        direct_only = st.toggle("Direct Only")
    with col7:
        sort_by = st.radio("Sort by", ["Price", "Duration"])

    st.divider()

    _, centre, _ = st.columns([2, 1, 2])
    with centre:
        search = st.button("🔍 Search Flights", use_container_width=True)

    st.divider()

    if search:
        if not airport:
            st.warning("Please select a valid airport before searching.")
            return

        # 1. Let your database manager handle checking staleness and running the scraper
        with st.spinner(f"Checking data for {airport}... Please wait if scraper launches."):
            flights = fs.get_flights(airport)

        # 2. Filter flights using the converted local currency to match slider values correctly
        if direct_only:
            flights = fs.filter_direct(flights)

        flights = [f for f in flights if (f.price * exchange_rate) <= max_price]
        flights = [f for f in flights if f.outbound_duration <= max_duration * 60]

        # 3. Sorting Processing
        flights = refresh_on_sort(flights, sort_by)

        # 4. Header Title Calculations
        city_name = data_utilities.get_city_from_iata(airport)
        display_location = city_name if city_name else airport.upper()
        st.subheader(f"{len(flights)} flights found from {display_location}")

        # 5. Grid Layout Cards Presentation
        if not flights:
            st.warning("No flights match your filters. Try raising your maximum budget or duration limit!")
        else:
            for i in range(0, len(flights), 3):
                cols = st.columns(3)
                for j, col in enumerate(cols):
                    if i + j < len(flights):
                        f = flights[i + j]
                        converted_price = f.price * exchange_rate
                        
                        with col:
                            with st.container(border=True):
                                st.subheader(f"✈️ {f.destination_full}")
                                st.metric("Price", f"{currency_symbol}{converted_price:.2f}")
                                
                                st.write(f"🛫 **{f.outbound_date}** at {f.outbound_dep} → {f.outbound_arr}")
                                st.write(f"🛬 **Return:** {f.return_date} at {f.return_dep} → {f.return_arr}")
                                st.write(f"⏱ Duration: {f.outbound_duration // 60}h {f.outbound_duration % 60}m")
                                st.write(f"🏢 {f.airline}")
                                stops = "Direct" if f.outbound_stops == 0 else f"{f.outbound_stops} stop(s)"
                                st.write(f"🔀 {stops}")


if __name__ == "__main__":
    render_ui()