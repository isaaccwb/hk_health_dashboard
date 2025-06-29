# Hong Kong Government Hospital Emergency Wait Times Dashboard

## Quick Start

Follow these steps to set up and run the dashboard after receiving the zip file:

### 1. Unzip the Application
- **Windows:**
  1. Right-click the zip file and select "Extract All..."
  2. Choose a folder and click "Extract"
- **Mac:**
  1. Double-click the zip file. A folder will appear in the same location.

### 2. Install Python (if not already installed)
- Download and install Python 3.8 or newer from [python.org/downloads](https://www.python.org/downloads/)
- During installation, check the box that says **"Add Python to PATH"** (Windows only)

### 3. Open a Terminal or Command Prompt
- **Windows:** Press `Win + R`, type `cmd`, and press Enter
- **Mac:** Open `Terminal` from Applications > Utilities

### 4. Navigate to the Unzipped Folder
- Type `cd ` (with a space), then drag the unzipped folder into the terminal window and press Enter.
  - Example (Windows): `cd C:\Users\YourName\Downloads\hk_health_dashboard`
  - Example (Mac): `cd /Users/yourname/Downloads/hk_health_dashboard`

### 5. Create and Activate a Virtual Environment
- **Windows:**
  ```cmd
  python -m venv venv
  venv\Scripts\activate
  ```
- **Mac:**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### 6. Install Required Libraries
- **Windows:**
  ```cmd
  pip install -r requirements.txt
  ```
- **Mac:**
  ```bash
  pip3 install -r requirements.txt
  ```

### 7. Run the Application
- **Attention:** Make sure you see `(venv)` in your terminal prompt before running the commands below. This means your virtual environment is activated and the correct Python and packages will be used.
- **Windows:**
  ```cmd
  streamlit run main.py
  ```
- **Mac:**
  ```bash
  python3 -m streamlit run main.py
  ```
- Your browser should open automatically. If not, go to [http://localhost:8501]
** First time loading the dashboard maybe taking up to 2-4 minutes as the application will be fetching the real time data

### 8. Using the Dashboard
- Use the sidebar for navigation and instructions.
- Explore hospital wait times, maps, and route planning features.

### 9. Stopping the App
- Go back to the terminal window and press `Ctrl + C` to stop.

---

If you have any issues, see the Troubleshooting section below or contact the project author.

---

## Main Features

- Real-time A&E wait times for all Hong Kong public hospitals
- Interactive map with hospital locations and color-coded wait times
- Route planning from your location to any hospital
- Search and view hospital details (address, telephone)
- Sidebar navigation with instructions and About Me section
- General disclaimer at the bottom of the dashboard

## How to Use

### Sidebar Navigation
- **How to Use**: Sidebar expander with instructions for dashboard features
- **Hospital Information**: Sidebar expander with search bar and full hospital info
- **About Me**: Sidebar expander with student name, ID, and assignment info

### Hospital Information
1. Use the search bar to find hospitals by name, address, or location (e.g., 'chai wan', 'queen mary', 'pok fu lam').
2. View full hospital details including address and telephone number.
3. When you select a hospital from the map or chart, its details are highlighted and shown at the top of this section.
4. Browse all hospitals in the expandable list below the search bar.

### Hospital Rankings
1. View the horizontal bar chart showing all hospitals
2. Use filters to sort by wait time or region
3. Click on any hospital bar to select it

### Interactive Map
1. The map shows all hospitals with color-coded wait times
2. Selected hospitals are highlighted with a purple border
3. Choose from multiple map styles for better visualization

### Route Planning
1. Select a hospital by clicking its bar
2. Enter your current location in the route input field
3. View route details including duration, distance, and traffic
4. Explore alternative routes and transport options
5. Traffic legend appears to the right of the map

### Disclaimer
- A general disclaimer with student name and assignment info is shown at the bottom of the dashboard

## Data Sources

- **A&E Wait Times**: Hong Kong Hospital Authority Open Data API
- **Traffic Data**: Mapbox Directions API (real-time)
- **Maps**: Mapbox 
- **Static Hospital Info**: https://www.ha.org.hk/visitor/ha_visitor_index.asp?Content_ID=200246&lang=ENG

## Configuration


## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure virtual environment is activated
   - Run `pip install -r requirements.txt`

2. **Mapbox Token Issues**
   - The token is already included in the zip file. If you see a token error, contact the project author.

3. **API Connection Issues**
   - App includes fallback data if HK Hospital Authority API is unavailable
   - Check internet connection

4. **Port Already in Use**
   - Change port: `streamlit run main.py --server.port 8502`
