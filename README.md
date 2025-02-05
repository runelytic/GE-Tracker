# OSRS GE Price Monitor

A Python application that monitors item prices on the Old School RuneScape Grand Exchange using a modern GUI built with CustomTkinter. It fetches real-time price data from the OSRS Prices API and displays item icons from the RuneScape Wiki API. You can search for items, view their current prices, and set up price alerts with desktop notifications.

## Features

- Modern GUI with dark mode (CustomTkinter)
- Real-time price data from the OSRS Prices API
- Item icons fetched via the RuneScape Wiki API
- Searchable item list with dropdown filtering
- Readable price formatting with commas
- Desktop notifications for price alerts

## Installation

1. **Clone or download this repository.**

2. **Install the required dependencies:**

   ```bash
   pip install customtkinter requests pillow plyer


Usage
Run the application:

bash
Copy
python osrs_ge_price_monitor.py
Use the search bar to find an OSRS item.

Click "Get Price" to fetch and display the current low and high prices for the selected item.

Optionally, set low and/or high price alerts and click "Start Monitoring" to continuously check prices and receive desktop notifications when thresholds are met.

Click "Stop Monitoring" to end the monitoring process.
