import dash
from dash import html, dcc, Input, Output, State
import pandas as pd
import os
import json

# Load and rank data
df = pd.read_csv("data.csv")
fields = df.columns[1:]
ranks_df = df.copy()

# Calculate ranks (higher is better)
for col in fields:
    ranks_df[col] = df[col].rank(ascending=False, method='min')

# Save rank data as JSON for frontend use (only once)
if not os.path.exists('assets/rank_data.json'):
    all_field_ranks = {}
    for field in fields:
        all_field_ranks[field] = dict(zip(df["Area"], ranks_df[field].astype(int)))

    all_ranks_by_area = {}
    for area in df["Area"]:
        area_ranks = {field: int(ranks_df.loc[df["Area"] == area, field].values[0]) for field in fields}
        all_ranks_by_area[area] = area_ranks

    with open('assets/rank_data.json', 'w') as f:
        json.dump({
            'all_fields': all_ranks_by_area,
            **all_field_ranks
        }, f)

    print("✅ rank_data.json created.")

# Create Dash app
app = dash.Dash(__name__)
app.title = "Interactive Area Report"

# Layout
app.layout = html.Div([
    html.Div([
        html.H2("Interactive Area Visualization"),

        dcc.Dropdown(
            id='field-dropdown',
            options=[{'label': f, 'value': f} for f in fields],
            placeholder='Select a field',
            style={'width': '100%', 'marginBottom': '20px'}
        ),

        html.Div(id='area-details')
    ], style={'width': '30%', 'padding': '20px', 'boxSizing': 'border-box'}),

    html.Div([
        html.ObjectEl(
            id='svg-container',
            data='/assets/image_map.svg',
            type='image/svg+xml',
            style={'width': '100%', 'height': 'auto'}
        ),

        dcc.Interval(
            id='svg-loader',
            interval=500,
            n_intervals=0,
            max_intervals=10  # Stop after 10 tries
        ),
    ], style={'width': '70%', 'padding': '20px', 'boxSizing': 'border-box'})

], style={'display': 'flex', 'flexDirection': 'row'})


# JavaScript-based color and click handler
app.clientside_callback(
    """
    function(field, n_intervals) {
        const obj = document.querySelector('#svg-container');
        const svgDoc = obj?.contentDocument;
        if (!svgDoc || !svgDoc.getElementById) return "";

        const areas = [
            "Harvey",
            "Arcadia",
            "Fredericton_Junction",
            "Tracy",
            "Sunburty-York_South",
            "Hanwell",
            "Oromocto",
            "Fredericton",
            "New_Maryland",
            "Nackawick-Millville",
            "Central_York",
            "Grand_Lake",
            "Hashwaak"
        ];

        const rankDataRaw = localStorage.getItem('rank_data');
        if (!rankDataRaw) return "";

        const rankData = JSON.parse(rankDataRaw);
        const fieldRanks = field ? (rankData?.[field] || {}) : {};
        const allFieldsRanks = rankData?.['all_fields'] || {};

        for (const area of areas) {
            const group = svgDoc.getElementById(area);
            if (!group ) continue;

            group.style.cursor = 'pointer';

            if (fieldRanks[area]) {
                const rank = fieldRanks[area];
                const maxRank = 13;
                const minGreen = 50;
                const maxGreen = 255;
                const green = minGreen + Math.floor((maxGreen - minGreen) * (maxRank - rank) / (maxRank - 1));
                group.style.fill = `rgb(0,${green},0)`;
            } else {
                group.style.fill = '';
            }

            group.onclick = () => {
                const allRanks = allFieldsRanks?.[area];
                if (!allRanks || typeof allRanks !== 'object') return;

                let html = `<h4>Rank Details for ${area}</h4><table><thead><tr><th>Field</th><th>Rank</th></tr></thead><tbody>`;
                for (const fieldName in allRanks) {
                    const rank = allRanks[fieldName];
                    const totalUnits = 13;
                    let bar = '<div style="display: flex; gap: 2px;">';
                    for (let i = 0; i < totalUnits; i++) {
                        if (i < totalUnits - rank) {
                            bar += '<span style="width: 10px; height: 12px; background-color: green; display: inline-block;"></span>';
                        } else {
                            bar += '<span style="width: 10px; height: 12px; background-color: #eee; display: inline-block;"></span>';
                        }
                    }
                    bar += '</div>';
                    html += `<tr><td>${fieldName}</td><td>${bar}</td></tr>`;

                }
                html += "</tbody></table>";

                const target = document.getElementById('area-details');
                target.innerHTML = html;
            };
        }

        return "";
    }
    """,
    Output('area-details', 'children'),
    Input('field-dropdown', 'value'),
    Input('svg-loader', 'n_intervals')
)

# Inject rank_data into localStorage on app start
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Interactive Area Report</title>
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

if __name__ == '__main__':
    app.run(debug=True)
