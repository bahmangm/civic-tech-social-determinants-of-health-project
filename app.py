import dash
from dash import html, dcc, Input, Output
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

# Layout
app.layout = html.Div([
    html.H2("Interactive Area Visualization"),

    # Dropdown to choose field
    html.Div([
        # html.Label("Select a Field:"),
        dcc.Dropdown(
            id='field-dropdown',
            options=[{'label': f, 'value': f} for f in fields],
            # value=fields[0]
            placeholder='Select a field'
        )
    ], style={'width': '300px', 'marginBottom': '20px'}),

    # SVG map container
    html.Div([
        html.ObjectEl(
            id='svg-container',
            data='/assets/image_map.svg',
            type='image/svg+xml',
            style={'width': '100%', 'height': 'auto'}
        )
    ]),

    # Tooltip placeholder
    html.Div(id='tooltip-container', style={'marginTop': '20px'})
])

# JavaScript-based color and tooltip handler
app.clientside_callback(
    """
    function(field) {
        const obj = document.querySelector('#svg-container');
        const svgDoc = obj?.contentDocument;
        console.log("SVG Document:", svgDoc);
        if (!field || !svgDoc) return "";

        const tooltipDiv = document.getElementById('tooltip-container');
        tooltipDiv.innerHTML = '';

        const areas = ['A', 'B', 'C', 'D', 'E', 'F'];
        const rankDataRaw = localStorage.getItem('rank_data');
        if (!rankDataRaw) return "";

        const rankData = JSON.parse(rankDataRaw);
        const fieldRanks = rankData?.[field] || {};
        const allFieldsRanks = rankData?.['all_fields'] || {};

        for (const area of areas) {
            const group = svgDoc.getElementById(area);
            const rect = group?.querySelector('rect');
            if (group && rect && fieldRanks[area]) {
                const rank = fieldRanks[area];
                const green = 100 + Math.floor(155 * (6 - rank) / 5);
                rect.style.fill = `rgb(0,${green},0)`;
                group.style.cursor = 'pointer';

                group.onclick = () => {
                    const allRanks = allFieldsRanks?.[area];
                    if (!allRanks || typeof allRanks !== 'object') return;
                    let html = `<h4>Rank Details for Area ${area}</h4><table><thead><tr><th>Field</th><th>Rank</th></tr></thead><tbody>`;
                    for (const fieldName in allRanks) {
                        html += `<tr><td>${fieldName}</td><td>${allRanks[fieldName]}</td></tr>`;
                    }
                    html += "</tbody></table>";
                    tooltipDiv.innerHTML = html;
                };
            }
        }

        return "";
    }
    """,
    Output('tooltip-container', 'children'),
    Input('field-dropdown', 'value')
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
