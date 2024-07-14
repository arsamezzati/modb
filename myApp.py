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

def signup(username, password, user_type=1):
    response = requests.post(f"{FLASK_API_URL}/signup", json={"username": username, "password": password, "type": user_type})
    return response

def login(username, password):
    response = requests.post(f"{FLASK_API_URL}/login", json={"username": username, "password": password})
    return response

def logout():
    st.session_state.logged_in = False
    st.session_state.username = None
    st.sidebar.success("Logged out successfully")

def fetch_history(username):
    response = requests.get(f"{FLASK_API_URL}/history", params={"username": username})
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Failed to fetch history")
        return []

def fetch_favorites(username):
    response = requests.get(f"{FLASK_API_URL}/favorites", params={"username": username})
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Failed to fetch favorites")
        return []

def add_favorite(username, item):
    response = requests.post(f"{FLASK_API_URL}/favorites/add", json={"username": username, "item": item})
    return response

def remove_favorite(username, item):
    response = requests.post(f"{FLASK_API_URL}/favorites/remove", json={"username": username, "item": item})
    return response

def main():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = None

    if st.session_state.logged_in:
        st.sidebar.write(f"Logged in as {st.session_state.username}")
        if st.sidebar.button("Logout"):
            logout()
            st.experimental_rerun()

        st.sidebar.title("Navigation")
        page = st.sidebar.radio("Go to", ["Add Place", "Check Temperature", "History", "Favorites :heartbeat:"])

        if page == "Add Place":
            add_place()
        elif page == "Check Temperature":
            check_temperature()
        elif page == "History":
            view_history()
        elif page == "Favorites :heartbeat:":
            view_favorites()
    else:
        login_signup()

def login_signup():
    st.sidebar.title("Login/Signup")
    action = st.sidebar.radio("Select Action", ["Login", "Signup"])

    if action == "Login":
        st.title("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            response = login(username, password)
            if response.status_code == 200:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success("Login successful!")
                st.experimental_rerun()
            else:
                st.error("Login failed. Please check your username and password.")
                st.write(response.json())
    elif action == "Signup":
        st.title("Signup")
        username = st.text_input("New Username")
        password = st.text_input("New Password", type="password")
        user_type = st.selectbox("User Type", [0, 1])  # Assuming 0 for admin and 1 for regular user
        if st.button("Signup"):
            response = signup(username, password, user_type)
            if response.status_code == 201:
                st.success("Signup successful!")
            else:
                st.error("Signup failed. Please try again.")
                st.write(response.json())

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
                response = requests.get(f"{FLASK_API_URL}/temperature", params={"city": selected_city, "username": st.session_state.username})
                if response.status_code == 200:
                    data = response.json()
                    st.success(f"The temperature in {selected_city} is {data['temperature']:.2f}°C")
                    st.info(f"Humidity: {data['humidity']}%")
                    st.info(f"Pressure: {data['pressure']} hPa")
                    st.info(f"Wind Speed: {data['wind_speed']} m/s")
                    st.info(f"Visibility: {data['visibility']} km")

                    favorites = fetch_favorites(st.session_state.username)
                    item_id = data["id"]
                    if item_id in favorites:
                        st.button("Unlike", on_click=remove_favorite, args=(st.session_state.username, item_id))
                    else:
                        st.button("Like", on_click=add_favorite, args=(st.session_state.username, item_id))
                else:
                    st.error("Failed to fetch temperature data")

def view_history():
    st.title("Weather History")
    history_data = fetch_history(st.session_state.username)

    if history_data:
        for entry in history_data:
            st.write(f"Date: {entry['date']}")
            st.write(f"City: {entry['location']['name']}")
            st.write(f"Temperature: {entry['data']['values']['temperature']}°C")
            st.write(f"Humidity: {entry['data']['values']['humidity']}%")
            st.write(f"Pressure: {entry['data']['values']['pressureSurfaceLevel']} hPa")
            st.write(f"Wind Speed: {entry['data']['values']['windSpeed']} m/s")
            st.write(f"Visibility: {entry['data']['values']['visibility']} km")
            st.write("---")

def view_favorites():
    st.title("Favorites :heartbeat:")
    favorites = fetch_favorites(st.session_state.username)

    if favorites:
        for favorite in favorites:
            st.write(f"Date: {favorite['date']}")
            st.write(f"City: {favorite['location']['name']}")
            st.write(f"Temperature: {favorite['data']['values']['temperature']}°C")
            st.write(f"Humidity: {favorite['data']['values']['humidity']}%")
            st.write(f"Pressure: {favorite['data']['values']['pressureSurfaceLevel']} hPa")
            st.write(f"Wind Speed: {favorite['data']['values']['windSpeed']} m/s")
            st.write(f"Visibility: {favorite['data']['values']['visibility']} km")
            if st.button("Unlike", key=favorite['_id'], on_click=remove_favorite, args=(st.session_state.username, favorite['_id'])):
                st.experimental_rerun()

if __name__ == "__main__":
    main()
