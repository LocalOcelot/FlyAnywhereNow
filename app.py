import streamlit as st
from flight_search import FlightSearch
from scraper import AIRPORT_LOCATIONS

fs = FlightSearch()

#Es to run it: streamlit run app.py

def refresh_on_sort(flights, sort_by):
    if sort_by == "Price":
        return fs.sort_by_price(flights)
    return sorted(flights, key=lambda f: f.outbound_duration)

def render_ui():
    st.set_page_config(page_title="FlyAnywhereNow", layout="wide")


    st.markdown("<h1 style='text-align: center;'>✈️ FlyAnywhereNow</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>No plan. No destination. Just go.</p>", unsafe_allow_html=True)

    st.divider()

    # controls bar
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        airport = st.selectbox("Departure Airport", list(AIRPORT_LOCATIONS.keys()))
    with col2:
        max_price = st.slider("Max Price £", 0, 1000, 500)
    with col3:
        direct_only = st.toggle("Direct Only")
    with col4:
        max_duration = st.slider("Max Duration (hrs)", 1, 24, 12)
    with col5:
        sort_by = st.radio("Sort by", ["Price", "Duration"])

    st.divider()

    _, centre, _ = st.columns([2, 1, 2])
    with centre:
        search = st.button("🔍 Search Flights", use_container_width=True)

    st.divider()

    if search:
        flights = fs.get_flights(airport)

        # filters 
        if direct_only:
            flights = fs.filter_direct(flights)

        flights = [f for f in flights if f.price <= max_price]
        flights = [f for f in flights if f.outbound_duration <= max_duration * 60]

        # sorting
        flights = refresh_on_sort(flights, sort_by)

        st.subheader(f"{len(flights)} flights found from {airport}")

        if not flights:
            st.warning("No flights match your filters. Try adjusting them.")
        else:
            for i in range(0, len(flights), 3):
                cols = st.columns(3)
                for j, col in enumerate(cols):
                    if i + j < len(flights):
                        f = flights[i + j]
                        with col:
                            with st.container(border=True):
                                st.subheader(f"✈️ {f.destination_full}")
                                st.metric("Price", f"£{f.price:.2f}")
                                st.write(f"🛫 **{f.outbound_date}** at {f.outbound_dep} → {f.outbound_arr}")
                                st.write(f"🛬 **Return:** {f.return_date} at {f.return_dep} → {f.return_arr}")
                                st.write(f"⏱ Duration: {f.outbound_duration // 60}h {f.outbound_duration % 60}m")
                                st.write(f"🏢 {f.airline}")
                                stops = "Direct" if f.outbound_stops == 0 else f"{f.outbound_stops} stop(s)"
                                st.write(f"🔀 {stops}")


if __name__ == "__main__":
    render_ui()