import streamlit as st
import requests

# Flask API URL
FLASK_API_URL = "http://localhost:5000"

def fetch_regions():
    response = requests.get(f"{FLASK_API_URL}/regions")
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Failed to fetch regions")
        return []

def fetch_cities(region):
    response = requests.get(f"{FLASK_API_URL}/cities", params={"region": region})
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Failed to fetch cities for region {region}")
        return []

def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Login/Signup", "Add Place", "Check Temperature"])

    if page == "Login/Signup":
        login_signup()
    elif page == "Add Place":
        add_place()
    elif page == "Check Temperature":
        check_temperature()

def login_signup():
    st.title("Login/Signup")

    action = st.selectbox("Select Action", ["Login", "Signup"])

    if action == "Login":
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            st.success("Login successful!")
    elif action == "Signup":
        username = st.text_input("New Username")
        password = st.text_input("New Password", type="password")
        if st.button("Signup"):
            st.success("Signup successful!")

def add_place():
    st.title("Add Place")

    regions = fetch_regions()
    if not regions:
        return

    selected_region = st.selectbox("Select Region", regions)
    city_name = st.text_input("City Name")

    if st.button("Add Place"):
        data = {"region": selected_region, "city": city_name}
        response = requests.post(f"{FLASK_API_URL}/add_place", json=data)
        if response.status_code == 201:
            st.success(f"Added {city_name} in {selected_region}")
        else:
            st.error("Failed to add place")

def check_temperature():
    st.title("Check Temperature")

    regions = fetch_regions()
    if not regions:
        return

    selected_region = st.selectbox("Select Region", regions)
    if selected_region:
        cities = fetch_cities(selected_region)
        if cities:
            selected_city = st.selectbox("Select City", [city for city in cities])

            if st.button("Check Temperature"):
                response = requests.get(f"{FLASK_API_URL}/temperature", params={"city": selected_city})
                if response.status_code == 200:
                    data = response.json()
                    st.success(f"The temperature in {selected_city} is {data['temperature']:.2f}°C")
                else:
                    st.error("Failed to fetch temperature data")

if __name__ == "__main__":
    main()
