"""
Dash app for visualizing Social Determinants of Health (SDoH) ranks across regions in RSC11.
Loads data, processes rankings, and renders an interactive SVG map with interactivity.
"""

import dash
from dash import html, dcc, Input, Output
import pandas as pd
import os
import json

# ------------------------
# Constants
# ------------------------

DATA_PATH = "data.csv"
JSON_PATH = "assets/rank_data.json"
SVG_PATH = "assets/image_map_labeled.svg"

# Indicate which SDoHs are positive and which are negative
SDoH_SIGNS = {
    "% No Highschool diploma": "Negative",
    "% Highschool": "Negative",
    "% Postsecondary": "Positive",
    "% of Children in 1-Parent families": "Negative",
    # "% Living with other relatives": "Positive",
    # "% Living with non-relatives only": "Negative",
    "Median after tax income (in 2020)": "Positive",
    "% Received COVID-19 benefits": "Negative",
    "% Low-income (after taxes)": "Negative",
    "% Spending >30% income on housing": "Negative",
    "Unemployment Rate": "Negative"
}

# ------------------------
# Data Processing Functions
# ------------------------

def clean_and_rank_data(filepath):
    """Load CSV, clean numeric fields, and compute ranks (higher = better)."""
    df = pd.read_csv(filepath)
    fields = df.columns[1:]

    for col in fields:
        df[col] = df[col].replace(r'[\$,%,]', '', regex=True).replace('', '0').astype(float)

    ranks_df = df.copy()
    for col in fields:
        ranks_df[col] = df[col].rank(ascending=False, method='min')

    return df, ranks_df, fields


def generate_rank_json(df, ranks_df, fields, output_path=JSON_PATH):
    """Generate and save rank data to a JSON file for clientside use."""
    all_field_ranks = {
        field: dict(zip(df["Area"], ranks_df[field].astype(int)))
        for field in fields
    }

    all_ranks_by_area = {
        area: {
            field: int(ranks_df.loc[df["Area"] == area, field].values[0])
            for field in fields
        }
        for area in df["Area"]
    }

    # Add stats and raw_values for statistical summary table
    stats = {
        field: {
            # "min": float(df[field].min()),
            "avg": float(df[field].mean()),
            # "max": float(df[field].max())
        } for field in fields
    }
    raw_values = {
        area: {
            field: float(df.loc[df["Area"] == area, field].values[0])
            for field in fields
        }
        for area in df["Area"]
    }
    

    areas = df["Area"].dropna().unique().tolist()

    with open(output_path, 'w') as f:
        json.dump({
            'areas': areas,
            'all_fields': all_ranks_by_area,
            'raw_values': raw_values,
            'stats': stats,
            'field_signs': SDoH_SIGNS,
            **all_field_ranks
        }, f)

    print(f"{output_path} created.")


# ------------------------
# Load & Prepare Data
# ------------------------

df, ranks_df, fields = clean_and_rank_data(DATA_PATH)

if not os.path.exists(JSON_PATH):
    generate_rank_json(df, ranks_df, fields)


# ------------------------
# App Layout
# ------------------------

# Create Dash app
app = dash.Dash(__name__)

app.layout = html.Div([
        html.Div([
            html.H2("Social Determinants of Health in RSC11"),

            dcc.Dropdown(
                id='field-dropdown',
                options=[{'label': f, 'value': f} for f in fields],
                placeholder='Select a SDoH',
                style={'width': '100%', 'marginBottom': '20px'}
            ),

            html.Div(id='area-details', 
                     style={'marginTop': '60px'})
        ], style={'width': '32%', 'padding': '0px', 'boxSizing': 'border-box'}),

        html.Div([
            html.ObjectEl(
                id='svg-container',
                data=SVG_PATH,
                type='image/svg+xml',
                style={'width': '100%', 'height': 'auto'}
            ),

            dcc.Interval(
                id='svg-loader',
                interval=500,
                n_intervals=0,
                max_intervals=10  # Stop after 10 tries
            ),
        ], style={'width': '68%', 'padding': '20px', 'boxSizing': 'border-box'})

    ], style={'display': 'flex', 'flexDirection': 'row',
              'fontFamily': 'Verdana, Arial, Helvetica, sans-serif'})


# ------------------------
# Client-Side Callback
# ------------------------

app.clientside_callback(
    """
    function(field, n_intervals) {
        const obj = document.querySelector('#svg-container');
        const svgDoc = obj?.contentDocument;
        if (!svgDoc || !svgDoc.getElementById) return "";

        const target = document.getElementById('area-details');
        target.innerHTML = "";  // Clear previous selection

        const rankDataRaw = localStorage.getItem('rank_data');
        if (!rankDataRaw) return "";

        const rankData = JSON.parse(rankDataRaw);
        const areas = rankData?.['areas'] || [];
        const fieldRanks = field ? (rankData?.[field] || {}) : {};
        const allFieldsRanks = rankData?.['all_fields'] || {};
        const fieldSigns = rankData?.['field_signs'] || {};
        const rawValues = rankData?.['raw_values'] || {};
        const sign = fieldSigns?.[field] || "Positive";


        for (const area of areas) {
            const group = svgDoc.getElementById(area);
            if (!group) continue;

            group.style.cursor = 'pointer';

            // Add or update tooltip
            // let existingTitle = group.querySelector('title');
            // if (!existingTitle) {
            //     const titleEl = document.createElementNS("http://www.w3.org/2000/svg", "title");
            //     titleEl.textContent = area.replace(/_/g, ' ');
            //     group.appendChild(titleEl);
            // } else {
            //     existingTitle.textContent = area.replace(/_/g, ' ');
            // }

            // Fill color based on rank
            if (fieldRanks[area]) {
                const rank = fieldRanks[area];
                const maxRank = 14;
                // 255 is max shade of green (or red) and 50 is min shade
                const intensity = 50 + Math.floor((255 - 50) * (1 - (maxRank - rank) / (maxRank - 1)));
                
                if (sign === "Positive") {
                    group.style.fill = `rgb(0,${intensity},0)`;  // green
                } else {
                    group.style.fill = `rgb(${intensity},0,0)`;  // red
                }

            } else {
                group.style.fill = '';
            }

            // Click handler
            group.onclick = (event) => {
                event.stopPropagation();
                const allRanks = allFieldsRanks?.[area];
                if (!allRanks) return;

                let html = `<h4 style="margin-bottom: 0px;">Rank Details for ${area.replace(/_/g, ' ')}</h4><table><thead><tr><th>SDoH</th><th>Rank</th></tr></thead><tbody>`;
                for (const fieldName in allRanks) {
                    const rank = allRanks[fieldName];
                    const totalUnits = 14;
                    const fieldSign = fieldSigns?.[fieldName] || "Positive";  // Use sign for current field

                    // Get raw numeric value
                    const rawValue = rawValues?.[area]?.[fieldName];
                    const formattedValue = rawValue !== undefined ? rawValue.toFixed(2) : "N/A";

                    // Build bar
                    let bar = '<div style="display: flex; gap: 2px;">';
                    for (let i = 0; i < totalUnits; i++) {
                        if (i <= totalUnits - rank) {
                            const color = fieldSign === "Positive" ? "green" : "red";  // ✅ Individual color
                            bar += `<span style="width: 10px; height: 12px; background-color: ${color}; display: inline-block;"></span>`;
                        } else {
                            bar += '<span style="width: 10px; height: 12px; background-color: #eee; display: inline-block;"></span>';
                        }
                    }
                    bar += '</div>';
                    html += `<tr><td>${fieldName} (${formattedValue})</td><td>${bar}</td></tr>`;
                }
                html += "</tbody></table>";

                /*
                // Add statistical summary table to html
                const stats = rankData?.['stats'] || {};
                const selectedRaw = rawValues?.[area];

                html += `<br><h4 style="margin-bottom: 0px;">Statistical Summary for ${area.replace(/_/g, ' ')}</h4><table>
                <thead><tr><th>Social Determinant</th><th>Value</th><th>CRSC Average</th></tr></thead><tbody>`;

                for (const fieldName in stats) {
                    const stat = stats[fieldName];
                    const raw = selectedRaw?.[fieldName];
                    html += `<tr>
                        <td>${fieldName}</td>
                        <td>${raw !== undefined ? raw.toFixed(2) : 'N/A'}</td>
                        <td>${stat.avg.toFixed(2)}</td>
                        
                        
                    </tr>`;
                }
                html += "</tbody></table>";
                */


                target.innerHTML = html;
            };
        }

        // Clear on outside click
        svgDoc.removeEventListener('click', window._outsideClickHandler);
        window._outsideClickHandler = function(e) {
            if (!areas.includes(e.target?.id)) {
                const target = document.getElementById('area-details');
                if (target) target.innerHTML = "";
            }
        };
        svgDoc.addEventListener('click', window._outsideClickHandler);

        return "";
    }
    """,
    Output('area-details', 'children'),
    Input('field-dropdown', 'value'),
    Input('svg-loader', 'n_intervals')
)


# ------------------------
# HTML Index String
# ------------------------

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>SDoH in RSC11</title>
        {%favicon%}
        {%css%}
        <script>
        fetch('/assets/rank_data.json')
          .then(resp => resp.json())
          .then(data => {
              localStorage.setItem('rank_data', JSON.stringify(data));
          });
        </script>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''


# ------------------------
# Run Server
# ------------------------
import dotenv
dotenv.load_dotenv()

if os.environ.get('ENVIRONMENT') == 'local':
    if __name__ == '__main__':
        app.run(debug=True)
