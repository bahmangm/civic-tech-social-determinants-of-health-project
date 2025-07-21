# Social Determinants of Health (SDoH) Visualizer – RSC11

This Dash application visualizes Social Determinants of Health (SDoH) rankings across different regions in RSC11 using an interactive SVG map. It enables users to explore and compare socioeconomic indicators that influence community health outcomes.

## 🔍 Features

- Interactive SVG map displaying SDoH rankings by region.
- Color-coded visualization (green/red) based on whether a higher value is positive or negative.
- Hover and click on regions to view detailed rank bars and statistical summaries.
- Client-side interactivity using JavaScript via Dash's clientside callback.
- Automatically processes and ranks data from a CSV file and stores results in a JSON format for use in the app.

## 📁 Project Structure

```
├── app.py                 # Main Dash app file
├── assets/
│   ├── image_map_labeled.svg  # Interactive labeled map of regions
│   └── rank_data.json         # Auto-generated rank and stats data
├── data.csv              # Raw input data for SDoH indicators
├── .env                  # (Optional) Environment variable for local/dev mode
```

## 🧠 How It Works

1. **Data Cleaning & Ranking**  
   The app reads `data.csv`, cleans numerical values, and ranks each region for all SDoH fields. Positive/negative impact signs are defined in a dictionary.

2. **Data Storage**  
   Rankings, raw values, and summary stats are stored in a `rank_data.json` file for fast front-end access.

3. **Visualization**  
   - Users select a field from a dropdown.
   - The map updates with rank-based coloring.
   - Clicking on a region displays:
     - A bar-based rank breakdown across all fields.
     - A statistical summary comparing the region to the CRSC average.

4. **Client-side Callback**  
   A clientside JavaScript function powers the SVG interactivity for smooth, instant user experience.

## 🚀 Getting Started

### 1. Install dependencies

```bash
pip install dash pandas python-dotenv
```

### 2. Prepare your environment

Make sure your `.env` file contains:

```bash
ENVIRONMENT=local
```

### 3. Run the app

```bash
python app.py
```

Then open [http://127.0.0.1:8050](http://127.0.0.1:8050) in your browser.


## 📌 Notes

- This app currently assumes a fixed number of 14 regions.
- Colors:  
  - **Green** = More desirable (e.g., higher education, higher income)  
  - **Red** = Less desirable (e.g., higher unemployment, low income)

## 📄 License

This project is open-source and can be freely modified and extended for non-commercial and educational purposes. Attribution is appreciated.

## 👥 Credits

Created by volunteers from **Civic Tech Fredericton** in partnership with **Capital Region Service Commission** (CRSC11), as part of a community-driven initiative to promote data-informed policy and resource allocation.

---
