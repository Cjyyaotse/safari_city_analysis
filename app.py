import pandas as pd
from dash import Dash, html, dcc, callback, Input, Output
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# =======================
# 1. LOAD DATA
# =======================
engagement = pd.read_csv("datasets/processed/engagement_time.csv")
devices = pd.read_csv("datasets/processed/device_distribution.csv")
events = pd.read_csv("datasets/processed/events.csv")
countries = pd.read_csv("datasets/processed/country_distribution.csv")
consistency = pd.read_csv("datasets/processed/consistency.csv")

# Clean up events
events = events.dropna(subset=["Key events"])

# Map countries to full names and continents
country_map = {
    "KE": ("Kenya", "Africa"),
    "NG": ("Nigeria", "Africa"),
    "GH": ("Ghana", "Africa"),
    "ZA": ("South Africa", "Africa"),
    "ZW": ("Zimbabwe", "Africa"),
    "SN": ("Senegal", "Africa"),
    "UG": ("Uganda", "Africa")
}
countries["Country Name"] = countries["Country"].map(lambda x: country_map.get(x, (x, "Unknown"))[0])
countries["Continent"] = countries["Country"].map(lambda x: country_map.get(x, (x, "Unknown"))[1])

# =======================
# 2. ENHANCED VISUALIZATIONS
# =======================

def create_funnel_chart():
    """Early player journey funnel with conversion rates"""
    funnel_stages = ["first_open", "session_start"]
    funnel_df = engagement[engagement["Event name"].isin(funnel_stages)]
    funnel_df = pd.concat([
        events.rename(columns={"Event name": "Event name", "Key events": "Event count"})[["Event name", "Event count"]],
        funnel_df
    ])

    funnel_df = funnel_df.groupby("Event name", as_index=False)["Event count"].sum()
    funnel_df = funnel_df.sort_values(by="Event count", ascending=False)

    fig = go.Figure(go.Funnel(
        y=funnel_df["Event name"],
        x=funnel_df["Event count"],
        textinfo="value+percent initial+percent previous",
        marker=dict(color=["#FF6B6B", "#4ECDC4", "#45B7D1"])
    ))
    fig.update_layout(
        title="🎯 Player Acquisition Funnel",
        height=400,
        template="plotly_white"
    )
    return fig

def create_engagement_heatmap():
    """Heatmap of event engagement patterns"""
    top_events = engagement.nlargest(15, "Event count")

    fig = px.bar(
        top_events,
        x="Event count",
        y="Event name",
        orientation="h",
        title="🔥 Top 15 Engagement Events",
        color="Event count",
        color_continuous_scale="Viridis",
        text="Event count"
    )
    fig.update_traces(texttemplate='%{text:.2s}', textposition='outside')
    fig.update_layout(height=500, showlegend=False, template="plotly_white")
    return fig

def create_device_analysis():
    """Enhanced device distribution with market share"""
    top_devices = devices.nlargest(15, "Active users")

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Device Distribution", "Market Share"),
        specs=[[{"type": "bar"}, {"type": "pie"}]]
    )

    # Bar chart
    fig.add_trace(
        go.Bar(
            x=top_devices["Active users"],
            y=top_devices["Device model"],
            orientation='h',
            marker_color='lightseagreen',
            text=top_devices["Active users"],
            textposition='outside'
        ),
        row=1, col=1
    )

    # Pie chart
    fig.add_trace(
        go.Pie(
            labels=top_devices["Device model"],
            values=top_devices["Active users"],
            hole=0.4
        ),
        row=1, col=2
    )

    fig.update_layout(
        title_text="📱 Device Analytics Overview",
        height=500,
        showlegend=False,
        template="plotly_white"
    )
    return fig

def create_geographic_analysis():
    """Enhanced country distribution with multiple views"""
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "Active Users by Country",
            "Top 5 Countries",
            "Continent Distribution",
            "User Concentration %"
        ),
        specs=[
            [{"type": "bar", "colspan": 2}, None],
            [{"type": "pie"}, {"type": "bar"}]
        ],
        row_heights=[0.5, 0.5]
    )

    # Full country bar
    sorted_countries = countries.sort_values("Active users", ascending=False)
    fig.add_trace(
        go.Bar(
            x=sorted_countries["Country Name"],
            y=sorted_countries["Active users"],
            marker_color=px.colors.qualitative.Set3[:len(sorted_countries)],
            text=sorted_countries["Active users"],
            textposition='outside'
        ),
        row=1, col=1
    )

    # Top 5 pie
    top5 = sorted_countries.head(5)
    fig.add_trace(
        go.Pie(
            labels=top5["Country Name"],
            values=top5["Active users"],
            hole=0.3
        ),
        row=2, col=1
    )

    # Map countries to African regions
    region_map = {
        "KE": "East Africa",       # Kenya
        "UG": "East Africa",       # Uganda
        "TZ": "East Africa",       # Tanzania (if exists)
        "NG": "West Africa",       # Nigeria
        "GH": "West Africa",       # Ghana
        "SN": "West Africa",       # Senegal
        "CI": "West Africa",       # Côte d’Ivoire (if exists)
        "ZA": "Southern Africa",   # South Africa
        "ZW": "Southern Africa",   # Zimbabwe
        "ZM": "Southern Africa",   # Zambia (if exists)
        "DZ": "North Africa",      # Algeria
        "EG": "North Africa",      # Egypt
        "MA": "North Africa",      # Morocco
        "TN": "North Africa",      # Tunisia
        "NE": "West Africa",       # Niger
        "ML": "West Africa"        # Mali
    }

    # Add region column to DataFrame
    sorted_countries["Region"] = sorted_countries["Country"].map(region_map)

    # Group by region
    region_summary = (
        sorted_countries.groupby("Region", as_index=False)["Active users"]
        .sum()
        .sort_values(by="Active users", ascending=False)
    )

    # Calculate percentage share
    region_summary["Percentage"] = (region_summary["Active users"] / region_summary["Active users"].sum()) * 100

    # --- Plotly Bar Chart ---
    fig.add_trace(
        go.Bar(
            x=region_summary["Region"],
            y=region_summary["Percentage"],
            marker_color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'],  # different colors for regions
            text=region_summary["Percentage"].round(1).astype(str) + '%',
            textposition='outside'
        ),
        row=2, col=2
    )


    fig.update_layout(
        title_text="🌍 Geographic Distribution Analysis",
        height=800,
        showlegend=False,
        template="plotly_white"
    )
    return fig

def create_retention_metrics():
    """Retention and conversion metrics"""
    # Calculate key metrics
    total_installs = engagement[engagement["Event name"] == "first_open"]["Event count"].sum()
    session_starts = engagement[engagement["Event name"] == "session_start"]["Event count"].sum()
    progress_events = engagement[engagement["Event name"] == "progress"]["Event count"].sum()

    retention_rate = (session_starts / total_installs * 100) if total_installs > 0 else 0
    engagement_rate = (progress_events / session_starts * 100) if session_starts > 0 else 0

    fig = go.Figure()

    # Gauge charts for key metrics
    fig.add_trace(go.Indicator(
        mode="gauge+number+delta",
        value=retention_rate,
        title={'text': "Day 1 Retention Rate (%)"},
        delta={'reference': 30, 'increasing': {'color': "green"}},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 25], 'color': "lightgray"},
                {'range': [25, 50], 'color': "gray"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 50
            }
        },
        domain={'x': [0, 0.48], 'y': [0.5, 1]}
    ))

    fig.add_trace(go.Indicator(
        mode="gauge+number+delta",
        value=engagement_rate,
        title={'text': "Engagement Rate (%)"},
        delta={'reference': 60, 'increasing': {'color': "green"}},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkgreen"},
            'steps': [
                {'range': [0, 40], 'color': "lightgray"},
                {'range': [40, 70], 'color': "gray"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 70
            }
        },
        domain={'x': [0.52, 1], 'y': [0.5, 1]}
    ))

    # Add KPI cards
    fig.add_trace(go.Indicator(
        mode="number",
        value=total_installs,
        title={'text': "Total Installs"},
        domain={'x': [0, 0.33], 'y': [0, 0.4]}
    ))

    fig.add_trace(go.Indicator(
        mode="number",
        value=session_starts,
        title={'text': "Session Starts"},
        domain={'x': [0.34, 0.66], 'y': [0, 0.4]}
    ))

    fig.add_trace(go.Indicator(
        mode="number",
        value=progress_events,
        title={'text': "Progress Events"},
        domain={'x': [0.67, 1], 'y': [0, 0.4]}
    ))

    fig.update_layout(
        title_text="📊 Key Performance Indicators",
        height=600,
        template="plotly_white"
    )
    return fig

def create_consistency_chart():
    # --- Compute retention % ---
    df_consistency = globals()['consistency'].set_index("Date").apply(lambda x: (x / x["Week 0"]) * 100, axis=1)
    df_consistency = df_consistency.drop(columns=["Week 0"])
    df_consistency = df_consistency.reset_index()

    # --- Melt for plotting ---
    consistency_melted = df_consistency.melt(id_vars="Date", var_name="Week", value_name="Retention (%)")

    # --- Interactive Plotly line plot ---
    fig = px.line(
        consistency_melted,
        x="Week",
        y="Retention (%)",
        color="Date",
        markers=True,
        title="📉 Safari City Retention Cohorts by Week",
        template="plotly_white",
    )

    # --- Style adjustments ---
    fig.update_traces(line=dict(width=3))
    fig.update_layout(
        height=600,
        yaxis_title="Retention (% of Week 0 Users)",
        xaxis_title="Week Since Acquisition",
        legend_title="Cohort Start Date",
        font=dict(size=13),
        hovermode="x unified"
    )

    return fig


def create_event_comparison():
    """Compare different event categories"""
    # Categorize events
    categories = {
        'Core': ['first_open', 'session_start', 'user_engagement'],
        'Progression': ['progress', 'level_up', 'tutorial_complete']
    }

    category_data = []
    for cat, event_list in categories.items():
        count = engagement[engagement["Event name"].isin(event_list)]["Event count"].sum()
        category_data.append({'Category': cat, 'Count': count})

    cat_df = pd.DataFrame(category_data)

    fig = px.pie(
        cat_df,
        names='Category',
        values='Count',
        title='📊 Event Categories Comparison',
        color='Category',
        color_discrete_sequence=px.colors.qualitative.Bold,
        hole=0.4  # creates the doughnut effect
    )

    fig.update_traces(
        textinfo='percent+label',
        textposition='inside',
        pull=[0.05]*len(cat_df)  # slightly pull slices for separation
    )

    fig.update_layout(
        height=400,
        showlegend=True,
        template="plotly_white",
        title_font=dict(size=20, family="Arial Black"),
        legend_title_text='Event Category',
        annotations=[dict(
            text='Events',
            x=0.5, y=0.5,
            font_size=14,
            showarrow=False
        )]
    )

    return fig


def create_device_performance_scatter():
    """Device performance analysis"""
    # Assuming we can derive some metrics
    top_devices = devices.nlargest(20, "Active users").copy()

    fig = px.scatter(
        top_devices,
        x="Device model",
        y="Active users",
        size="Active users",
        color="Active users",
        title="📱 Device Performance Distribution",
        color_continuous_scale="Turbo",
        size_max=50
    )
    fig.update_layout(
        height=500,
        template="plotly_white",
        xaxis_tickangle=-45
    )
    return fig

# =======================
# 3. MULTI-PAGE DASH APP
# =======================
app = Dash(__name__, suppress_callback_exceptions=True)
server = app.server
# Sidebar styling
SIDEBAR_STYLE = {
    'position': 'fixed',
    'top': 0,
    'left': 0,
    'bottom': 0,
    'width': '16rem',
    'padding': '2rem 1rem',
    'background-color': '#2C3E50',
    'color': 'white'
}

CONTENT_STYLE = {
    'margin-left': '18rem',
    'margin-right': '2rem',
    'padding': '2rem 1rem',
}

sidebar = html.Div(
    [
        html.H2("Safari City", className="display-6", style={'color': '#ECF0F1'}),
        html.Hr(style={'border-color': '#ECF0F1'}),
        html.P("Analytics Dashboard", className="lead", style={'color': '#BDC3C7'}),
        html.Hr(style={'border-color': '#ECF0F1'}),
        dcc.Link('🏠 Overview', href='/', style={'color': 'white', 'display': 'block', 'padding': '10px'}),
        dcc.Link('👥 Player Funnel', href='/funnel', style={'color': 'white', 'display': 'block', 'padding': '10px'}),
        dcc.Link('🎮 Engagement', href='/engagement', style={'color': 'white', 'display': 'block', 'padding': '10px'}),
        dcc.Link('📱 Devices', href='/devices', style={'color': 'white', 'display': 'block', 'padding': '10px'}),
        dcc.Link('🌍 Geography', href='/geography', style={'color': 'white', 'display': 'block', 'padding': '10px'}),
        dcc.Link('💡 Insights', href='/insights', style={'color': 'white', 'display': 'block', 'padding': '10px'}),
    ],
    style=SIDEBAR_STYLE,
)

content = html.Div(id="page-content", style=CONTENT_STYLE)

app.layout = html.Div([dcc.Location(id="url"), sidebar, content])

# =======================
# 4. PAGE CALLBACKS
# =======================

@callback(Output("page-content", "children"), Input("url", "pathname"))
def render_page_content(pathname):
    if pathname == "/":
        return html.Div([
            html.H1("📊 Safari City Analytics Overview", style={'textAlign': 'center', 'color': '#2C3E50'}),
            html.Hr(),
            dcc.Graph(figure=create_retention_metrics()),
            html.Div([
                dcc.Graph(figure=create_event_comparison(), style={'width': '50%'}),
                dcc.Graph(figure=create_funnel_chart(), style={'width': '50%'}),
            ], style={'display': 'flex', 'flexDirection': 'row'}),
        ])

    elif pathname == "/funnel":
        return html.Div([
            html.H1("👥 Player Funnel Analysis", style={'textAlign': 'center', 'color': '#2C3E50'}),
            html.Hr(),
            dcc.Graph(figure=create_funnel_chart()),
            dcc.Graph(figure=create_retention_metrics()),
            html.Div([
                html.H3("Funnel Insights", style={'color': '#34495E'}),
                html.Ul([
                    html.Li("Track player drop-off at each stage of the journey"),
                    html.Li("Identify critical retention bottlenecks"),
                    html.Li("Optimize onboarding experience based on conversion rates"),
                    html.Li("Monitor day-1 retention trends")
                ])
            ], style={'padding': '20px', 'backgroundColor': '#ECF0F1', 'borderRadius': '10px', 'margin': '20px'})
        ])

    elif pathname == "/engagement":
        return html.Div([
            html.H1("🎮 Player Engagement Metrics", style={'textAlign': 'center', 'color': '#2C3E50'}),
            html.Hr(),
            dcc.Graph(figure=create_engagement_heatmap()),
            dcc.Graph(figure=create_event_comparison()),
            dcc.Graph(figure=create_consistency_chart()),
            html.Div([
                html.H3("Engagement Insights", style={'color': '#34495E'}),
                html.Ul([
                    html.Li("Top events indicate strong mid-game engagement loops"),
                    html.Li("Session_start and user_engagement show healthy player activity"),
                    html.Li("Progress events suggest good game flow and difficulty balance"),
                    html.Li("Late-game events (like SafariRace_Complete) need attention"),
                    html.Li("There is a drastic decline in engagement from week 1 to week 2 and by week 4 almost 90% of players stop playing")
                ])
            ], style={'padding': '20px', 'backgroundColor': '#ECF0F1', 'borderRadius': '10px', 'margin': '20px'})
        ])

    elif pathname == "/devices":
        return html.Div([
            html.H1("📱 Device Analytics", style={'textAlign': 'center', 'color': '#2C3E50'}),
            html.Hr(),
            dcc.Graph(figure=create_device_analysis()),
            dcc.Graph(figure=create_device_performance_scatter()),
            html.Div([
                html.H3("Device Insights", style={'color': '#34495E'}),
                html.Ul([
                    html.Li("Dominated by mid-range Android devices (Samsung A-series)"),
                    html.Li("Optimize performance for top 10 device models (70%+ of user base)"),
                    html.Li("Consider device-specific testing for Samsung SM-A055F and similar models"),
                    html.Li("Low-end device optimization critical for market penetration")
                ])
            ], style={'padding': '20px', 'backgroundColor': '#ECF0F1', 'borderRadius': '10px', 'margin': '20px'})
        ])

    elif pathname == "/geography":
        return html.Div([
            html.H1("🌍 Geographic Distribution", style={'textAlign': 'center', 'color': '#2C3E50'}),
            html.Hr(),
            dcc.Graph(figure=create_geographic_analysis()),
            html.Div([
                html.H3("Geographic Insights", style={'color': '#34495E'}),
                html.Ul([
                    html.Li("100% of player base from Africa - strong regional focus"),
                    html.Li("Kenya and Nigeria account for 50%+ of users"),
                    html.Li("Even though Kenya makes majority users as a country, west africa has the most numbers as a sub continent"),
                    html.Li("Opportunity for localization (language, currency, payment methods)"),
                    html.Li("Target marketing campaigns for East and West African markets"),
                    html.Li("Consider regional partnerships and local payment gateways")
                ])
            ], style={'padding': '20px', 'backgroundColor': '#ECF0F1', 'borderRadius': '10px', 'margin': '20px'})
        ])

    elif pathname == "/insights":
        return html.Div([
            html.H1("💡 Strategic Insights & Recommendations", style={'textAlign': 'center', 'color': '#2C3E50'}),
            html.Hr(),
            html.Div([
                dcc.Markdown("""
                ### 🎯 Critical Findings

                #### 1. Retention Challenge
                - **Only ~26% Day-1 Retention** (first_open → session_start)
                - Industry benchmark: 35-40% for mobile games
                - **Action Required**: Immediate onboarding optimization

                #### 2. Engagement Strengths
                - Strong mid-game engagement (progress, user_engagement)
                - Players who pass onboarding show good session depth
                - Core gameplay loop is working well

                #### 3. Technical Optimization
                - 70%+ users on mid-range Android devices
                - Performance optimization critical for market success
                - Focus on Samsung A-series compatibility

                #### 4. Regional Focus
                - 100% African user base (Kenya, Nigeria dominant)
                - Massive opportunity for regional expansion
                - Localization could unlock 2-3x growth

                ---

                ### 🚀 Priority Recommendations

                #### Immediate Actions (0-30 days)
                1. **Improve Onboarding**
                   - Add tutorial skip option for returning users
                   - Implement reward for completing first session
                   - Reduce friction in initial gameplay
                   - A/B test different onboarding flows

                2. **Performance Optimization**
                   - Profile performance on top 10 devices
                   - Optimize asset loading for mid-range devices
                   - Reduce memory footprint
                   - Implement adaptive quality settings

                3. **Retention Mechanics**
                   - Daily login rewards
                   - Push notification strategy
                   - Time-gated content to encourage return
                   - Social features (leaderboards, friend invites)

                #### Short-term (1-3 months)
                1. **Regional Localization**
                   - Support for local payment methods (M-Pesa, Flutterwave)
                   - Consider Swahili/local language support
                   - Partner with regional carriers for billing
                   - Regional pricing strategy

                2. **Monetization Enhancement**
                   - Add rewarded video ads at natural break points
                   - Implement soft currency economy
                   - Test in-app purchase bundles
                   - Create limited-time offers

                3. **Late-game Content**
                   - Expand content beyond mid-game
                   - Add prestige/progression systems
                   - Create end-game challenges
                   - Implement seasonal events

                #### Long-term (3-6 months)
                1. **Market Expansion**
                   - Test in additional African markets
                   - Develop regional marketing partnerships
                   - Create localized content/themes
                   - Build community features

                2. **Live Operations**
                   - Weekly events and challenges
                   - Battle pass / season pass system
                   - Regular content updates
                   - Community engagement programs

                ---

                ### 📈 Expected Impact

                | Initiative | Expected Impact | Timeline |
                |------------|----------------|----------|
                | Onboarding Optimization | +10-15% Day-1 Retention | 1 month |
                | Performance Fixes | +5% Retention | 1 month |
                | Payment Localization | +50-100% Revenue | 2 months |
                | Late-game Content | +20% Long-term Retention | 3 months |
                | Live Operations | +30% DAU | 4 months |

                ---

                ### 🎮 Competitive Positioning

                **Strengths:**
                - Strong African market presence
                - Good mid-game engagement
                - Clear player base identity

                **Opportunities:**
                - First-mover advantage in regional market
                - Untapped localization potential
                - Device optimization as differentiator

                **Threats:**
                - High initial drop-off rate
                - Limited late-game content
                - Competition from global titles

                **Weaknesses:**
                - Retention below industry standard
                - Single-region dependency
                - Technical performance concerns
                """)
            ], style={'padding': '20px', 'backgroundColor': '#FFFFFF', 'borderRadius': '10px', 'margin': '20px'})
        ])

    # If the user tries to reach a different page, return a 404 message
    return html.Div([
        html.H1("404: Not found", className="text-danger"),
        html.Hr(),
        html.P(f"The pathname {pathname} was not recognised..."),
    ])

# Run the app locally on a specific port (e.g., 8051)
if __name__ == '__main__':
    app.run(debug=True, port=8051)
