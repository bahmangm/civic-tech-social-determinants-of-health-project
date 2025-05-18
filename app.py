import dash
from dash import html, dcc, Input, Output, State
import pandas as pd
import os
import json

# Load and clean data
df = pd.read_csv("data.csv")
fields = df.columns[1:]

# Remove %, $ and commas → convert to numeric
for col in fields:
    df[col] = df[col].replace('[\$,%,]', '', regex=True).replace('', '0').astype(float)

# Rank data (higher values = better)
ranks_df = df.copy()
for col in fields:
    ranks_df[col] = df[col].rank(ascending=False, method='min')

# Save JSON once
if not os.path.exists('assets/rank_data.json'):
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

    # Convert to list to ensure JSON serializability
    areas = df["Area"].dropna().unique().tolist()

    with open('assets/rank_data.json', 'w') as f:
        json.dump({
            'areas': areas,
            'all_fields': all_ranks_by_area,
            **all_field_ranks
        }, f)

    print("rank_data.json created.")


# Create Dash app
app = dash.Dash(__name__)

# Layout
app.layout = html.Div([
    html.Div([
        html.H2("Social Determinants of Health in RSC11"),

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

        const target = document.getElementById('area-details');
        target.innerHTML = "";  // Clear the table when dropdown value changes

        const rankDataRaw = localStorage.getItem('rank_data');
        if (!rankDataRaw) return "";

        const rankData = JSON.parse(rankDataRaw);
        const areas = rankData?.['areas'] || [];
        const fieldRanks = field ? (rankData?.[field] || {}) : {};
        const allFieldsRanks = rankData?.['all_fields'] || {};

        for (const area of areas) {
            const group = svgDoc.getElementById(area);
            if (!group) continue;

            group.style.cursor = 'pointer';

            // Add tooltip (title tag) for hover
            let existingTitle = group.querySelector('title');
            if (!existingTitle) {
                const titleEl = document.createElementNS("http://www.w3.org/2000/svg", "title");
                titleEl.textContent = area.replace(/_/g, ' ');
                group.appendChild(titleEl);
            } else {
                existingTitle.textContent = area.replace(/_/g, ' ');
            }


            // Color by selected field
            if (fieldRanks[area]) {
                const rank = fieldRanks[area];
                const maxRank = 13;
                const minGreen = 50;
                const maxGreen = 255;
                const green = minGreen + Math.floor((maxGreen - minGreen) * (1- (maxRank - rank) / (maxRank - 1) ));
                group.style.fill = `rgb(0,${green},0)`;
            } else {
                group.style.fill = '';
            }

            // Handle area click
            group.onclick = (event) => {
                event.stopPropagation();
                const allRanks = allFieldsRanks?.[area];
                if (!allRanks) return;

                let html = `<h4>Rank Details for ${area.replace(/_/g, ' ')}</h4><table><thead><tr><th>SDoH</th><th>Rank</th></tr></thead><tbody>`;
                for (const fieldName in allRanks) {
                    const rank = allRanks[fieldName];
                    const totalUnits = 13;
                    let bar = '<div style="display: flex; gap: 2px;">';
                    for (let i = 0; i < totalUnits; i++) {
                        if (i <= totalUnits - rank) {
                            bar += '<span style="width: 10px; height: 12px; background-color: green; display: inline-block;"></span>';
                        } else {
                            bar += '<span style="width: 10px; height: 12px; background-color: #eee; display: inline-block;"></span>';
                        }
                    }
                    bar += '</div>';
                    html += `<tr><td>${fieldName}</td><td>${bar}</td></tr>`;
                }
                html += "</tbody></table>";
                target.innerHTML = html;
            };
        }

        // Remove old event listener first, then add new one
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


# Inject rank_data into localStorage on app start
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

if __name__ == '__main__':
    app.run(debug=True)
