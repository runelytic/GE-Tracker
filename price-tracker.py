# Import the requests library to make HTTP requests
import requests
# Import customtkinter as ctk for creating a modern, custom GUI
import customtkinter as ctk
# Import the Image class from Pillow (PIL) for image manipulation
from PIL import Image
# Import BytesIO to handle byte data (for image streams)
from io import BytesIO
# Import the notification module from plyer to show desktop notifications
from plyer import notification
# Import threading to run processes concurrently (e.g. monitoring)
import threading
# Import time to add delays (e.g. sleep between checks)
import time

# Define the API URL for fetching item mappings (item names to IDs)
MAPPING_URL = "https://prices.runescape.wiki/api/v1/osrs/mapping"
# Define the API URL for fetching the latest price data of items
PRICES_URL = "https://prices.runescape.wiki/api/v1/osrs/latest"
# Define the API URL for fetching item icons using the OSRS Wiki API.
# {0} is a placeholder for the item name (formatted to match the API requirements).
ICON_URL_API = "https://oldschool.runescape.wiki/api.php?action=query&format=json&titles={0}&prop=pageimages&pithumbsize=100"

# Configure customtkinter to use a dark appearance mode
ctk.set_appearance_mode("dark")
# Set the default colour theme for the GUI to blue
ctk.set_default_color_theme("blue")

def fetch_item_data():
    """
    Fetch item mappings from the OSRS Prices API and return a dictionary that maps
    item names to their corresponding IDs.
    """
    response = requests.get(MAPPING_URL)  # Send an HTTP GET request to the mapping API
    if response.status_code == 200:  # Check if the request was successful
        items = response.json()  # Parse the JSON response to get a list of items
        # Create and return a dictionary: key = item name, value = item ID
        return {item["name"]: item["id"] for item in items}
    return {}  # If the request failed, return an empty dictionary

# Load the item data into a global dictionary that can be used throughout the program
item_dict = fetch_item_data()

def search_items():
    """
    Filter and update the dropdown list based on the text the user enters.
    This function gets triggered whenever the user types in the search entry.
    """
    query = search_var.get().lower()  # Get the current search string and convert to lowercase
    # Create a list of items that contain the search query, sorting them alphabetically
    filtered_items = [item for item in sorted(item_dict.keys()) if query in item.lower()]
    # Update the dropdown's values to the filtered list
    dropdown.configure(values=filtered_items)

def fetch_prices():
    """
    Fetch the latest price data from the OSRS Prices API.
    Returns the 'data' field from the JSON response, which contains the price information.
    """
    response = requests.get(PRICES_URL)  # Send an HTTP GET request to the prices API
    if response.status_code == 200:  # Check if the request was successful
        return response.json()["data"]  # Return the price data (dictionary)
    return {}  # Return an empty dictionary if the request fails

def update_item_icon():
    """
    Fetch and display the item icon from the OSRS Wiki API when an item is selected.
    This function converts the item name into a suitable format for the API, fetches the JSON data,
    extracts the image URL, downloads the image, and displays it on the GUI.
    """
    item_name = search_var.get()  # Retrieve the current item name from the search input

    if not item_name:  # If no item name is provided, clear the icon display
        icon_label.configure(image=None, text="No Icon", compound="top")
        return  # Exit the function

    # Format the item name to match the Wiki API requirements by replacing spaces with underscores
    formatted_name = item_name.replace(" ", "_")
    # Construct the full URL for the API request by inserting the formatted item name
    icon_url = ICON_URL_API.format(formatted_name)

    # Define custom headers to mimic a browser (some APIs require a proper User-Agent)
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        # Send an HTTP GET request to the Wiki API for the item icon
        response = requests.get(icon_url, headers=headers)
        if response.status_code == 200:  # Check if the API call was successful
            data = response.json()  # Parse the JSON response
            # Debug print to help inspect the API response (can be removed later)
            print("Wiki API response:", data)
            # Extract the 'pages' information from the JSON response
            pages = data.get("query", {}).get("pages", {})
            if not pages:  # If no page data is returned, display 'No Icon'
                icon_label.configure(image=None, text="No Icon", compound="top")
                return

            # Get the first page ID from the returned pages
            page_id = list(pages.keys())[0]
            page_data = pages[page_id]  # Retrieve the data for that page
            # Attempt to get the thumbnail information from the page data
            thumbnail = page_data.get("thumbnail")
            if thumbnail and "source" in thumbnail:  # If thumbnail exists and has a 'source' URL
                image_url = thumbnail["source"]  # Extract the URL for the image
            else:
                image_url = None  # Otherwise, set image_url to None

            if image_url:  # If an image URL was found
                # Request the image using the image URL; stream=True allows us to handle the image bytes
                img_response = requests.get(image_url, headers=headers, stream=True)
                if img_response.status_code == 200:  # Check if the image was successfully fetched
                    img_data = BytesIO(img_response.content)  # Convert the byte content to a BytesIO object
                    img = Image.open(img_data)  # Open the image using Pillow
                    # Resize the image to 64x64 pixels with high-quality resampling (LANCZOS)
                    img_resized = img.resize((64, 64), Image.LANCZOS)
                    # Convert the PIL image to a CTkImage for compatibility with customtkinter (for both light and dark modes)
                    ctk_img = ctk.CTkImage(light_image=img_resized, dark_image=img_resized, size=(64, 64))
                    # Update the icon label to display the new image and clear any text
                    icon_label.configure(image=ctk_img, text="", compound="top")
                    # Keep a reference to the image to prevent it from being garbage-collected
                    icon_label.image = ctk_img
                else:
                    # If the image request fails, display 'No Icon'
                    icon_label.configure(image=None, text="No Icon", compound="top")
            else:
                # If no image URL was found, display 'No Icon'
                icon_label.configure(image=None, text="No Icon", compound="top")
        else:
            # If the Wiki API request fails, show an error message on the icon label
            icon_label.configure(image=None, text="Error fetching icon", compound="top")
    except Exception as e:
        # Print the exception error to the console for debugging
        print(f"Error loading icon: {e}")
        # Display an error message on the icon label
        icon_label.configure(image=None, text="Error loading icon", compound="top")

def get_price():
    """
    Fetch and display the current price information (low and high prices) for the selected item.
    This function retrieves the item ID, fetches the latest price data,
    and then updates the result label with the formatted prices.
    """
    item_name = search_var.get()  # Get the selected item name from the search input
    item_id = item_dict.get(item_name)  # Look up the item ID from the dictionary of items
    if not item_id:  # If the item ID is not found, notify the user via the status label
        status_label.configure(text="Item not found! Select a valid item.", text_color="red")
        return

    price_data = fetch_prices()  # Fetch the latest price data from the Prices API
    if not price_data or str(item_id) not in price_data:  # If price data is unavailable for the item
        status_label.configure(text="Price data unavailable.", text_color="red")
        return

    # Extract the low and high price values from the price data
    low_price = price_data[str(item_id)]["low"]
    high_price = price_data[str(item_id)]["high"]

    # Update the result label with the item name and prices,
    # formatting the prices with commas as thousand separators
    result_label.configure(text=f"{item_name}\nLow: {low_price:,} coins\nHigh: {high_price:,} coins")

def monitor_price():
    """
    Continuously monitor the price of the selected item.
    This function checks the price data at regular intervals (every 60 seconds)
    and updates the result label. It also sends desktop notifications if the price
    falls below the low alert or rises above the high alert thresholds.
    """
    global monitoring  # Declare 'monitoring' as a global variable to control the monitoring loop
    item_name = search_var.get()  # Get the selected item name from the search input
    item_id = item_dict.get(item_name)  # Retrieve the corresponding item ID
    if not item_id:  # If the item ID is not found, update the status label with an error message
        status_label.configure(text="Item not found! Select a valid item.", text_color="red")
        return

    # Retrieve the alert values entered by the user for low and high price alerts
    low_price_alert = low_price_var.get()
    high_price_alert = high_price_var.get()
    if not low_price_alert and not high_price_alert:  # Ensure at least one alert value is provided
        status_label.configure(text="Enter at least a Low or High price.", text_color="red")
        return

    try:
        # Convert the alert values to integers if they have been provided
        low_price_alert = int(low_price_alert) if low_price_alert else None
        high_price_alert = int(high_price_alert) if high_price_alert else None
    except ValueError:
        # If conversion fails, notify the user of invalid input
        status_label.configure(text="Invalid price values!", text_color="red")
        return

    monitoring = True  # Set the monitoring flag to True so that the loop runs
    start_button.configure(state="disabled")  # Disable the 'Start Monitoring' button
    stop_button.configure(state="normal")  # Enable the 'Stop Monitoring' button
    status_label.configure(text="Monitoring started...", text_color="green")  # Update the status label

    # Start an infinite loop that will continuously fetch and check the price data
    while monitoring:
        price_data = fetch_prices()  # Fetch the latest price data
        if not price_data or str(item_id) not in price_data:  # Check if price data is available for the item
            status_label.configure(text="Price data unavailable.", text_color="red")
            break  # Exit the loop if no data is found

        # Extract the low and high prices from the price data
        low_price = price_data[str(item_id)]["low"]
        high_price = price_data[str(item_id)]["high"]

        # Update the result label with the latest prices (formatted with commas)
        result_label.configure(text=f"{item_name}\nLow: {low_price:,} coins\nHigh: {high_price:,} coins")

        # If a low price alert is set and the current low price is at or below the alert value, send a notification
        if low_price_alert is not None and low_price <= low_price_alert:
            notification.notify(title=f"{item_name} Price Alert",
                                message=f"Low Price Alert: {low_price:,} coins",
                                timeout=5)  # Notification will disappear after 5 seconds
        # If a high price alert is set and the current high price is at or above the alert value, send a notification
        if high_price_alert is not None and high_price >= high_price_alert:
            notification.notify(title=f"{item_name} Price Alert",
                                message=f"High Price Alert: {high_price:,} coins",
                                timeout=5)

        time.sleep(60)  # Wait for 60 seconds before checking the price data again

def start_monitoring():
    """
    Start the monitor_price function in a separate thread.
    This allows the GUI to remain responsive while monitoring runs in the background.
    """
    thread = threading.Thread(target=monitor_price, daemon=True)  # Create a new daemon thread for monitoring
    thread.start()  # Start the monitoring thread

def stop_monitoring():
    """
    Stop the price monitoring process by setting the monitoring flag to False.
    This will cause the monitoring loop to exit.
    """
    global monitoring  # Declare the global monitoring variable so it can be modified
    monitoring = False  # Set the monitoring flag to False to stop the loop
    start_button.configure(state="normal")  # Re-enable the 'Start Monitoring' button
    stop_button.configure(state="disabled")  # Disable the 'Stop Monitoring' button
    status_label.configure(text="Monitoring stopped.", text_color="orange")  # Update the status label

# -------------------------------
# GUI SETUP USING CUSTOMTKINTER
# -------------------------------

# Create the main application window
root = ctk.CTk()
# Set the title of the window
root.title("OSRS GE Price Monitor")
# Define the geometry (size) of the window (width x height)
root.geometry("400x600")

# Create a StringVar to hold the search input text
search_var = ctk.StringVar()
# Create an entry widget for the user to type the item name
search_entry = ctk.CTkEntry(root, textvariable=search_var, width=300, placeholder_text="Search item...")
search_entry.pack(pady=10)  # Place the search entry in the window with 10 pixels of vertical padding
# Bind the key release event so that the dropdown updates as the user types
search_entry.bind("<KeyRelease>", lambda event: search_items())

# Create a dropdown (combobox) to display matching item names
dropdown = ctk.CTkComboBox(root, variable=search_var, values=sorted(item_dict.keys()), width=300,
                           command=lambda event: update_item_icon())
dropdown.pack(pady=5)  # Place the dropdown in the window with 5 pixels of vertical padding

# Create a label to display the item icon
icon_label = ctk.CTkLabel(root, text="Item Icon", width=64, height=64)
icon_label.pack(pady=10)  # Place the icon label in the window with 10 pixels of vertical padding

# Create a button to fetch and display the current price data without starting monitoring
get_price_button = ctk.CTkButton(root, text="Get Price", command=get_price)
get_price_button.pack(pady=5)  # Place the 'Get Price' button with 5 pixels of vertical padding

# Create a label to explain the low price alert input
ctk.CTkLabel(root, text="Low Price Alert (coins) - Optional:").pack()
# Create a StringVar to hold the low price alert value
low_price_var = ctk.StringVar()
# Create an entry widget for the low price alert value
low_price_entry = ctk.CTkEntry(root, textvariable=low_price_var, width=150, placeholder_text="e.g. 1000")
low_price_entry.pack(pady=5)  # Place the entry in the window with 5 pixels of vertical padding

# Create a label to explain the high price alert input
ctk.CTkLabel(root, text="High Price Alert (coins) - Optional:").pack()
# Create a StringVar to hold the high price alert value
high_price_var = ctk.StringVar()
# Create an entry widget for the high price alert value
high_price_entry = ctk.CTkEntry(root, textvariable=high_price_var, width=150, placeholder_text="e.g. 5000")
high_price_entry.pack(pady=5)  # Place the entry in the window with 5 pixels of vertical padding

# Create a button to start the price monitoring process
start_button = ctk.CTkButton(root, text="Start Monitoring", command=start_monitoring)
start_button.pack(pady=5)  # Place the 'Start Monitoring' button with 5 pixels of vertical padding

# Create a button to stop the price monitoring process; initially disabled until monitoring starts
stop_button = ctk.CTkButton(root, text="Stop Monitoring", command=stop_monitoring, state="disabled")
stop_button.pack(pady=5)  # Place the 'Stop Monitoring' button with 5 pixels of vertical padding

# Create a label to display status messages (errors, notifications, monitoring status)
status_label = ctk.CTkLabel(root, text="", font=("Arial", 12))
status_label.pack(pady=10)  # Place the status label with 10 pixels of vertical padding

# Create a label to display the current price information (result)
result_label = ctk.CTkLabel(root, text="", font=("Arial", 14, "bold"))
result_label.pack(pady=10)  # Place the result label with 10 pixels of vertical padding

# Initially populate the dropdown with all available item names
search_items()

# Start the main event loop to run the GUI continuously
root.mainloop()
