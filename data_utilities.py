import pandas as pd
import requests
import streamlit as st
import pycountry



COMMON_SYMBOLS = {
    "GBP": "£", "USD": "$", "EUR": "€", 
    "JPY": "¥", "AUD": "A$", "CAD": "C$", 
    "INR": "₹", "CNY": "¥", "NZD": "NZ$"
}

COUNTRY_CURRENCIES = {
    "Afghanistan": "AFN", "Albania": "ALL", "Algeria": "DZD", "Andorra": "EUR", "Angola": "AOA",
    "Antigua and Barbuda": "XCD", "Argentina": "ARS", "Armenia": "AMD", "Australia": "AUD", "Austria": "EUR",
    "Azerbaijan": "AZN", "Bahamas": "BSD", "Bahrain": "BHD", "Bangladesh": "BDT", "Barbados": "BBD",
    "Belarus": "BYN", "Belgium": "EUR", "Belize": "BZD", "Benin": "XOF", "Bhutan": "BTN",
    "Bolivia": "BOB", "Bosnia and Herzegovina": "BAM", "Botswana": "BWP", "Brazil": "BRL", "Brunei": "BND",
    "Bulgaria": "BGN", "Burkina Faso": "XOF", "Burundi": "BIF", "Cabo Verde": "CVE", "Cambodia": "KHR",
    "Cameroon": "XAF", "Canada": "CAD", "Central African Republic": "XAF", "Chad": "XAF", "Chile": "CLP",
    "China": "CNY", "Colombia": "COP", "Comoros": "KMF", "Congo (Congo-Brazzaville)": "XAF", "Congo (Democratic Republic)": "CDF",
    "Costa Rica": "CRC", "Croatia": "EUR", "Cuba": "CUP", "Cyprus": "EUR", "Czechia": "CZK",
    "Denmark": "DKK", "Djibouti": "DJF", "Dominica": "XCD", "Dominican Republic": "DOP", "Ecuador": "USD",
    "Egypt": "EGP", "El Salvador": "USD", "Equatorial Guinea": "XAF", "Eritrea": "ERN", "Estonia": "EUR",
    "Eswatini": "SZL", "Ethiopia": "ETB", "Fiji": "FJD", "Finland": "EUR", "France": "EUR",
    "Gabon": "XAF", "Gambia": "GMD", "Georgia": "GEL", "Germany": "EUR", "Ghana": "GHS",
    "Greece": "EUR", "Grenada": "XCD", "Guatemala": "GTQ", "Guinea": "GNF", "Guinea-Bissau": "XOF",
    "Guyana": "GYD", "Haiti": "HTG", "Honduras": "HNL", "Hungary": "HUF", "Iceland": "ISK",
    "India": "INR", "Indonesia": "IDR", "Iran": "IRR", "Iraq": "IQD", "Ireland": "EUR",
    "Israel": "ILS", "Italy": "EUR", "Jamaica": "JMD", "Japan": "JPY", "Jordan": "JOD",
    "Kazakhstan": "KZT", "Kenya": "KES", "Kiribati": "AUD", "Kuwait": "KWD", "Kyrgyzstan": "KGS",
    "Laos": "LAK", "Latvia": "EUR", "Lebanon": "LBP", "Lesotho": "LSL", "Liberia": "LRD",
    "Libya": "LYD", "Liechtenstein": "CHF", "Lithuania": "EUR", "Luxembourg": "EUR", "Madagascar": "MGA",
    "Malawi": "MWK", "Malaysia": "MYR", "Maldives": "MVR", "Mali": "XOF", "Malta": "EUR",
    "Marshall Islands": "USD", "Mauritania": "MRU", "Mauritius": "MUR", "Mexico": "MXN", "Micronesia": "USD",
    "Moldova": "MDL", "Monaco": "EUR", "Mongolia": "MNT", "Montenegro": "EUR", "Morocco": "MAD",
    "Mozambique": "MZN", "Myanmar": "MMK", "Namibia": "NAD", "Nauru": "AUD", "Nepal": "NPR",
    "Netherlands": "EUR", "New Zealand": "NZD", "Nicaragua": "NIO", "Niger": "XOF", "Nigeria": "NGN",
    "North Korea": "KPW", "North Macedonia": "MKD", "Norway": "NOK", "Oman": "OMR", "Pakistan": "PKR",
    "Palau": "USD", "Palestine": "ILS", "Panama": "PAB", "Papua New Guinea": "PGK", "Paraguay": "PYG",
    "Peru": "PEN", "Philippines": "PHP", "Poland": "PLN", "Portugal": "EUR", "Qatar": "QAR",
    "Romania": "RON", "Russia": "RUB", "Rwanda": "RWF", "Saint Kitts and Nevis": "XCD", "Saint Lucia": "XCD",
    "Saint Vincent and the Grenadines": "XCD", "Samoa": "WST", "San Marino": "EUR", "Sao Tome and Principe": "STN", "Saudi Arabia": "SAR",
    "Senegal": "XOF", "Serbia": "RSD", "Seychelles": "SCR", "Sierra Leone": "SLE", "Singapore": "SGD",
    "Slovakia": "EUR", "Slovenia": "EUR", "Solomon Islands": "SBD", "Somalia": "SOS", "South Africa": "ZAR",
    "South Korea": "KRW", "South Sudan": "SSP", "Spain": "EUR", "Sri Lanka": "LKR", "Sudan": "SDG",
    "Suriname": "SRD", "Sweden": "SEK", "Switzerland": "CHF", "Syria": "SYP", "Taiwan": "TWD",
    "Tajikistan": "TJS", "Tanzania": "TZS", "Thailand": "THB", "Timor-Leste": "USD", "Togo": "XOF",
    "Tonga": "TOP", "Trinidad and Tobago": "TTD", "Tunisia": "TND", "Turkey": "TRY", "Turkmenistan": "TMT",
    "Tuvalu": "AUD", "Uganda": "UGX", "Ukraine": "UAH", "United Arab Emirates": "AED", "United Kingdom": "GBP",
    "United States": "USD", "Uruguay": "UYU", "Uzbekistan": "UZS", "Vanuatu": "VUV", "Vatican City": "EUR",
    "Venezuela": "VES", "Vietnam": "VND", "Yemen": "YER", "Zambia": "ZMW", "Zimbabwe": "ZWG"
}


@st.cache_data(ttl=3600)  # Caches data for 1 hour 
def get_exchange_rate(target_currency: str, base_currency: str = "GBP") -> float:
    """
    Fetches the live exchange conversion multiplier from base_currency to target_currency.
    Falls back gracefully to 1.0 if the API limit or a network timeout happens.
    """
    if target_currency == base_currency:
        return 1.0
        
    try:
        # Utilizing the open access endpoint structure of ExchangeRate-API
        url = f"https://open.er-api.com/v6/latest/{base_currency}"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            rates = data.get("rates", {})
            return rates.get(target_currency, 1.0)
    except Exception:
        pass
        
    return 1.0

def get_currency_details(country_name: str):
    """
    Resolves the currency code, clean UI glyph, and live exchange rate multiplier
    based on the selected country name.
    """
    currency_code = COUNTRY_CURRENCIES.get(country_name, "GBP")
    symbol = COMMON_SYMBOLS.get(currency_code, f"{currency_code} ")
    rate = get_exchange_rate(currency_code)
    
    return currency_code, symbol, rate

@st.cache_data
def load_all_airports():
    df = pd.read_csv("airports.csv")
    df = df[df["iata_code"].notna()]
    df = df[df["iata_code"] != ""]
    df = df[df["type"].isin(["medium_airport", "large_airport"])]
    df = df[df["iso_country"].notna()]
    

    def get_country_name(code):
        try:
            return pycountry.countries.get(alpha_2=code).name
        except AttributeError:
            return None 
            
    df["country_name"] = df["iso_country"].apply(get_country_name)
    #drop any rows where the country name cant be found
    df = df[df["country_name"].notna()]
    df = df.sort_values("municipality")
    return df

def get_airport_options_by_country(df, country_name):

    filtered_df = df[df["country_name"] == country_name]
        
    return {
        f"{row['iata_code']} — {row['municipality']}": row['iata_code']
        for _, row in filtered_df.iterrows()
    }

def get_city_from_iata(iata):
    df = load_all_airports()
    match = df[df["iata_code"] == iata.upper()]
    if not match.empty:
        row = match.iloc[0]
        city = str(row["municipality"]).lower().strip()
        country = str(row["country_name"]).lower().strip()
        
        # Clean up characters
        for char in [" ", ",", "/", "."]:
            city = city.replace(char, "-")
            country = country.replace(char, "-")
            
        # Prevent double hyphens 
        while "--" in city: city = city.replace("--", "-")
        while "--" in country: country = country.replace("--", "-")

        return f"{city}-{country}"
    return None