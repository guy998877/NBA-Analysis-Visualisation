import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
import warnings
import numpy as np


# Initial setup
warnings.filterwarnings('ignore')
st.set_page_config(page_title="NBA Shot Analysis!!!", page_icon=":bar_chart:", layout="wide")
st.title(" :bar_chart: NBA Shot Analysis Dashboard :basketball: ")

# Sidebar for page selection
page = st.sidebar.selectbox("Choose a page", ["Page 1 - Shot Clock & Catch and Shoot", "Page 2 - Players Comparison", "Page 3 - Teams Comparison"])

# Load the data
shot_data = pd.read_csv("shot_logs.csv", encoding="ISO-8859-1")
shot_data['TIME_LEFT'] = shot_data['SHOT_CLOCK']

player_df = pd.read_csv('players_teams.csv')
shot_data = shot_data.merge(player_df, how='left', left_on='player_name', right_on='Player')
shot_data = shot_data.drop(columns=['Player'])

before_filter = shot_data

# Function to calculate shooting percentage
def calculate_shooting_percentage(data):
    if len(data) == 0:  # Handle empty data to avoid division by zero
        return 0
    return (data['FGM'].sum() / len(data)) * 100

# Function to count shots
def count_shots(data):
    return len(data)

# Common filters for all pages
game_location = st.sidebar.selectbox(
    "Select Game Location",
    options=["All", "Home", "Away"],
    index=0
)

game_quarter = st.sidebar.selectbox(
    "Select Game Quarter",
    options=["All", "1", "2", "3", "4"],
    index=0
)

shoot_type = st.sidebar.selectbox(
    "Select Shoot Type",
    options=["All", "2 Points", "3 Points"],
    index=0
)

game_close = st.sidebar.selectbox(
    "Select final Game Margin",
    options=["All", "Below 5 points", "More than 5 points"],
    index=0
)

# Filter data based on common selections
if game_location == "Home":
    game_location = "H"
elif game_location == "Away":
    game_location = "A"
else:
    game_location = "All"

if game_location != "All":
    filtered_data = shot_data[shot_data['LOCATION'] == game_location]
else:
    filtered_data = shot_data

if game_quarter != "All":
    filtered_data = filtered_data[filtered_data['PERIOD'] == int(game_quarter)]

if game_close == "Below 5 points":
    filtered_data = filtered_data[abs(filtered_data['FINAL_MARGIN']) <= 5]
elif game_close == "More than 5 points":
    filtered_data = filtered_data[abs(filtered_data['FINAL_MARGIN']) > 5]

if shoot_type == "2 Points":
    filtered_data = filtered_data[filtered_data['PTS_TYPE'] == 2]
elif shoot_type == "3 Points":
    filtered_data = filtered_data[filtered_data['PTS_TYPE'] == 3]

# Page 1 - Shot Clock & Catch and Shoot (common filters only)
if page == "Page 1 - Shot Clock & Catch and Shoot":
    st.header("Comparisons of Different Game Parameters")

    shot_data = filtered_data

    # Visualization 1: Shots Taken and Shooting Percentage by Time Left on Shot Clock
    shot_data['SHOT_CLOCK_CATEGORY'] = pd.cut(shot_data['SHOT_CLOCK'], bins=[0, 3, 6, 9, 12, 15, 18, 21, 24], labels=['0-3', '3-6', '6-9', '9-12', '12-15', '15-18', '18-21', '21-24'])
    shot_clock_summary = shot_data.groupby('SHOT_CLOCK_CATEGORY').agg({
        'SHOT_CLOCK': 'count',
        'FGM': 'sum'
    }).rename(columns={'SHOT_CLOCK': 'Shots'}).reset_index()
    shot_clock_summary['Shooting_Percentage'] = (shot_clock_summary['FGM'] / shot_clock_summary['Shots']) * 100

    fig_dual = go.Figure()
    fig_dual.add_trace(go.Bar(
        x=shot_clock_summary['SHOT_CLOCK_CATEGORY'],
        y=shot_clock_summary['Shots'],
        name='Shots Taken',
        marker=dict(color='lightblue'),
        yaxis='y'
    ))

    fig_dual.add_trace(go.Scatter(
        x=shot_clock_summary['SHOT_CLOCK_CATEGORY'],
        y=shot_clock_summary['Shooting_Percentage'],
        mode='lines+markers',
        name='Shooting Percentage',
        line=dict(color='darkgreen', width=4, dash='dash'),
        yaxis='y2'
    ))

    fig_dual.update_layout(
        title='Shots Taken and Shooting Percentage by Time Left on Shot Clock',
        xaxis_title='Time Left on Shot Clock (seconds)',
        yaxis=dict(
            title='Shots Taken',
            side='left'
        ),
        yaxis2=dict(
            title='Shooting Percentage (%)',
            overlaying='y',
            side='right'
        ),
        showlegend=True,
        width=600, height=500
    )

    st.plotly_chart(fig_dual, use_container_width=True)

    # Visualization 3: Catch and Shoot vs After Dribble Shot
    filtered_data['SHOT_DIST'] = np.ceil(filtered_data['SHOT_DIST'])
    filtered_data['TIME_LEFT'] = np.ceil(filtered_data['TIME_LEFT'])
    filtered_data['CLOSE_DEF_DIST'] = np.ceil(filtered_data['CLOSE_DEF_DIST'])
    filtered_data['Catch and Shoot'] = filtered_data['DRIBBLES'] < 1.0

    filtered_data['Distance'] = pd.cut(filtered_data['SHOT_DIST'],
                                        bins=[0, 14, filtered_data['SHOT_DIST'].max()],
                                        labels=['Short Distance (0-14 feet)',
                                                f'Long Distance (14+ feet)'], right=False)

    filtered_data['Time Left'] = pd.cut(filtered_data['TIME_LEFT'],
                                        bins=[0, 12, 24],
                                        labels=['Low Time Left (0-12 seconds)',
                                                'High Time Left (12-24 seconds)'], right=False)

    filtered_data['Defender Distance'] = pd.cut(filtered_data['CLOSE_DEF_DIST'],
                                                bins=[0, 3.8, filtered_data['CLOSE_DEF_DIST'].max()],
                                                labels=['Tight Defense (0-3.8 feet)',
                                                        f'Loose Defense (3.8+ feet)'], right=False)

    summary_table = pd.DataFrame(columns=['Category', 'Type', 'Shooting Percentage'])

    for category in ['Distance', 'Time Left', 'Defender Distance']:
        for level in filtered_data[category].cat.categories:
            catch_and_shoot = calculate_shooting_percentage(filtered_data[(filtered_data['Catch and Shoot']) & (filtered_data[category] == level)])
            not_catch_and_shoot = calculate_shooting_percentage(filtered_data[(filtered_data['Catch and Shoot'] == False) & (filtered_data[category] == level)])
            summary_table = pd.concat([summary_table, pd.DataFrame([{'Category': f'{level}', 'Type': 'Catch and Shoot', 'Shooting Percentage': catch_and_shoot}])])
            summary_table = pd.concat([summary_table, pd.DataFrame([{'Category': f'{level}', 'Type': 'After Dribble Shot', 'Shooting Percentage': not_catch_and_shoot}])])

    fig3 = go.Figure()

    fig3.add_trace(go.Bar(
        x=summary_table[summary_table['Type'] == 'Catch and Shoot']['Category'],
        y=summary_table[summary_table['Type'] == 'Catch and Shoot']['Shooting Percentage'],
        name='Catch and Shoot',
        marker_color='royalblue'
    ))

    fig3.add_trace(go.Bar(
        x=summary_table[summary_table['Type'] == 'After Dribble Shot']['Category'],
        y=summary_table[summary_table['Type'] == 'After Dribble Shot']['Shooting Percentage'],
        name='After Dribble Shot',
        marker_color='darkorange'
    ))

    fig3.update_layout(
        barmode='group',
        title='Shooting Percentage Comparison: Catch and Shoot vs After Dribble Shot',
        xaxis_title='Category',
        yaxis_title='Shooting Percentage',
        legend_title_text='Type',
        yaxis=dict(range=[0, 70]),
        bargap=0.38,
        xaxis_tickfont_size=11,
        width=600, height=500
    )

    st.plotly_chart(fig3, use_container_width=True)

# Page 2 - Players Comparison (common filters + player filters)
elif page == "Page 2 - Players Comparison":
    st.header("Shooting Percentage & Shot Count Comparison: Famous NBA Players")

    # Player filters for bubble chart
    st.sidebar.subheader("Bubble Chart Filters")
    famous_players = [
        'LeBron James', 'Kobe Bryant', 'Stephen Curry',
        'Chris Paul', 'Tim Duncan',
        'Kawhi Leonard', 'Russell Westbrook', 'James Harden', 'Carmelo Anthony',
        'Paul Pierce', 'Klay Thompson', 'Pau Gasol', 'Blake Griffin',
        'Anthony Davis', 'Marc Gasol', 'Damian Lillard', 'Giannis Antetokounmpo'
    ]

    selected_players_bubble = st.sidebar.multiselect(
        "Select players for Bubble Chart:",
        options=famous_players,
        default=['LeBron James', 'Stephen Curry', 'Kawhi Leonard', 'James Harden', 'Chris Paul', 'Kobe Bryant', 'Anthony Davis']
    )

    # Player filters for new line/bar chart
    st.sidebar.subheader("Line/Bar Chart Filters")
    selected_players_line = st.sidebar.multiselect(
        "Select up to 2 players for Line/Bar Chart:",
        options=famous_players,
        default=['LeBron James', 'Stephen Curry'],
        max_selections=2
    )

    # Ensure there are always two selected players
    if len(selected_players_line) < 2:
        st.warning("Please select exactly two players to compare.")
        st.stop()

    player1, player2 = selected_players_line

    shot_data = filtered_data

    # Filter data for the selected players
    famous_players_data = shot_data[shot_data['player_name'].isin([player.lower() for player in selected_players_bubble])]

    # Ensure that shot distance is valid for binning
    if famous_players_data['SHOT_DIST'].min() < famous_players_data['SHOT_DIST'].max():
        famous_players_data['Distance'] = pd.cut(famous_players_data['SHOT_DIST'],
                                                 bins=[0, 14, famous_players_data['SHOT_DIST'].max()],
                                                 labels=['Short Distance (0-14 feet)', f'Long Distance (14+ feet)'],
                                                 right=False)
    else:
        st.error("Invalid range for shot distance. Please check the data.")
        st.stop()

    famous_players_data['Time Left'] = pd.cut(famous_players_data['TIME_LEFT'],
                                              bins=[0, 12, 24],
                                              labels=['Low Time Left (0-12 seconds)', 'High Time Left (12-24 seconds)'], right=False)

    famous_players_data['Defender Distance'] = pd.cut(famous_players_data['CLOSE_DEF_DIST'],
                                                      bins=[0, 3.8, famous_players_data['CLOSE_DEF_DIST'].max()],
                                                      labels=['Tight Defense (0-3.8 feet)', f'Loose Defense (3.8+ feet)'], right=False)

    famous_players_data['Dribbles'] = pd.cut(famous_players_data['DRIBBLES'],
                                             bins=[0, 1, famous_players_data['DRIBBLES'].max()],
                                             labels=['Few Dribbles (0-1)', 'Many Dribbles (2+)'], right=False)

    # Define the functions to calculate shooting percentage and count shots
    def count_shots(data):
        return len(data)

    # Create a summary table for each category separately
    categories = ['Distance', 'Time Left', 'Defender Distance', 'Dribbles']
    summary_table = pd.DataFrame(columns=['Category', 'Player', 'Shooting Percentage', 'Shot Count'])

    for category in categories:
        for level in famous_players_data[category].cat.categories:
            for player in selected_players_bubble:
                player_pct = calculate_shooting_percentage(famous_players_data[(famous_players_data['player_name'] == player.lower()) & (famous_players_data[category] == level)])
                player_count = count_shots(famous_players_data[(famous_players_data['player_name'] == player.lower()) & (famous_players_data[category] == level)])
                summary_table = pd.concat([summary_table, pd.DataFrame([{'Category': f'{level}', 'Player': player, 'Shooting Percentage': round(player_pct, 1), 'Shot Count': player_count}])])

    # Ensure that 'Shot Count' is numeric
    summary_table['Shot Count'] = summary_table['Shot Count'].astype(float)

    # Create the Plotly figure for bubble chart
    fig_bubble = go.Figure()

    # Add scatter traces for each selected player
    for player in selected_players_bubble:
        player_data = summary_table[summary_table['Player'] == player]
        fig_bubble.add_trace(go.Scatter(
            x=player_data['Category'],
            y=player_data['Shooting Percentage'],
            mode='markers',
            marker=dict(
                size=player_data['Shot Count'],
                sizemode='area',
                sizeref=2.*max(summary_table['Shot Count'])/(23.**2),  # Size scaling
                line_width=2,
                opacity=0.8  # Set opacity to avoid white bubbles
            ),
            name=player,
            hovertemplate=(
                f'<b>{player}</b><br>' +
                'Category: %{x}<br>' +
                'Shooting Percentage: %{y:.1f}%<br>' +
                'Shot Count: %{marker.size}<br>'
            )
        ))

    # Update the layout of the figure
    fig_bubble.update_layout(
        title='Shooting Percentage & Shot Count Comparison: Famous NBA Players',
        xaxis_title='Category',
        yaxis_title='Shooting Percentage',
        legend_title_text='Player',
        yaxis=dict(range=[20, 70]),  # This sets the y-axis limit
        xaxis_tickangle=28,  # This rotates the x-axis labels to the right
        xaxis_tickfont_size=11,  # This sets the font size for the x-axis labels
        width=1300,  # Increase the width of the chart
        height=500  # Increase the height of the chart
    )

    st.plotly_chart(fig_bubble, use_container_width=True)

    # New Line/Bar chart for selected players
    selected_players_data = shot_data[shot_data['player_name'].isin([player1.lower(), player2.lower()])]

    selected_players_data['Distance'] = pd.cut(selected_players_data['SHOT_DIST'],
                                               bins=[0, 14, selected_players_data['SHOT_DIST'].max()],
                                               labels=['Short Distance (0-14 feet)', f'Long Distance (14+ feet)'], right=False)

    selected_players_data['Time Left'] = pd.cut(selected_players_data['TIME_LEFT'],
                                                bins=[0, 12, 24],
                                                labels=['Low Time Left (0-12 seconds)', 'High Time Left (12-24 seconds)'], right=False)

    selected_players_data['Defender Distance'] = pd.cut(selected_players_data['CLOSE_DEF_DIST'],
                                                        bins=[0, 3.8, selected_players_data['CLOSE_DEF_DIST'].max()],
                                                        labels=['Tight Defense (0-3.8 feet)', f'Loose Defense (3.8+ feet)'], right=False)

    selected_players_data['Dribbles'] = pd.cut(selected_players_data['DRIBBLES'],
                                               bins=[0, 1, selected_players_data['DRIBBLES'].max()],
                                               labels=['Few Dribbles (0-1)', f'Many Dribbles (2+)'], right=False)

    summary_table_line = pd.DataFrame(columns=['Category', 'Player', 'Shooting Percentage', 'Shot Count'])

    for category in ['Distance', 'Time Left', 'Defender Distance', 'Dribbles']:
        for level in selected_players_data[category].cat.categories:
            player1_pct = calculate_shooting_percentage(selected_players_data[(selected_players_data['player_name'] == player1.lower()) & (selected_players_data[category] == level)])
            player2_pct = calculate_shooting_percentage(selected_players_data[(selected_players_data['player_name'] == player2.lower()) & (selected_players_data[category] == level)])
            player1_count = count_shots(selected_players_data[(selected_players_data['player_name'] == player1.lower()) & (selected_players_data[category] == level)])
            player2_count = count_shots(selected_players_data[(selected_players_data['player_name'] == player2.lower()) & (selected_players_data[category] == level)])
            summary_table_line = pd.concat([summary_table_line, pd.DataFrame([{'Category': f'{level}', 'Player': player1, 'Shooting Percentage': player1_pct, 'Shot Count': player1_count}])])
            summary_table_line = pd.concat([summary_table_line, pd.DataFrame([{'Category': f'{level}', 'Player': player2, 'Shooting Percentage': player2_pct, 'Shot Count': player2_count}])])

    fig_line = go.Figure()

    # Add traces for player 1 (line then bar)
    player1_data = summary_table_line[summary_table_line['Player'] == player1]
    fig_line.add_trace(go.Scatter(
        x=player1_data['Category'],
        y=player1_data['Shooting Percentage'],
        mode='lines+markers',
        name=f'{player1} Shooting Percentage',
        line=dict(width=3.8, color='royalblue'),  # Blue line for player 1
        marker=dict(size=12)
    ))

    player2_data = summary_table_line[summary_table_line['Player'] == player2]
    fig_line.add_trace(go.Scatter(
        x=player2_data['Category'],
        y=player2_data['Shooting Percentage'],
        mode='lines+markers',
        name=f'{player2} Shooting Percentage',
        line=dict(width=3.8, color='darkorange'),  # Orange line for player 2
        marker=dict(size=12)
    ))

    # Add bar traces for shot counts
    fig_line.add_trace(go.Bar(
        x=player1_data['Category'],
        y=player1_data['Shot Count'],
        name=f'{player1} Shot Count',
        marker=dict(color='royalblue'),  # Same blue for player 1
        yaxis='y2',
        opacity=0.9
    ))

    fig_line.add_trace(go.Bar(
        x=player2_data['Category'],
        y=player2_data['Shot Count'],
        name=f'{player2} Shot Count',
        marker=dict(color='darkorange'),  # Same orange for player 2
        yaxis='y2',
        opacity=0.9
    ))

    # Update layout with the legend in the top right corner
    fig_line.update_layout(
        title=f'Shooting Percentage & Shot Count Comparison: {player1} vs {player2}',
        xaxis_title='Category',
        yaxis_title='Shooting Percentage',
        legend=dict(
            orientation='v',
            yanchor='top',
            y=1,
            xanchor='right',
            x=1,
            bordercolor='Black',
            borderwidth=1
        ),
        yaxis=dict(range=[10, 70]),  # Set y-axis range from 10% to 70%
        yaxis2=dict(range=[0, 1500], overlaying='y', side='right', title='Shot Count'),  # Set y2-axis range from 0 to 1500
        xaxis_tickangle=28,  # Rotate x-axis labels
        xaxis_tickfont_size=12,  # Increase font size for x-axis labels
        width=1380,  # Wider figure for better readability
        height=900,  # Adjust height accordingly
        template='plotly_white',  # Use a white theme
        font=dict(size=15),  # Increase overall font size
    )

    st.plotly_chart(fig_line, use_container_width=True)


# Define the third page for Teams Comparison
elif page == "Page 3 - Teams Comparison":
    st.header("Shooting Percentage Comparison Teams")

    # Sidebar filters for team selection (up to 2 teams)
    selected_teams = st.sidebar.multiselect(
        "Select Teams to display:",
        options=shot_data['team_name'].unique(),
        default=['Golden State Warriors', 'Atlanta Hawks'],
        max_selections=2
    )

    # Check for selected teams and display warning if none selected
    if len(selected_teams) == 0:
        st.warning("Please select at least one team to compare.")
    else:
        # Assign teams based on selection
        team1 = selected_teams[0]
        team2 = selected_teams[1] if len(selected_teams) > 1 else None

        shot_data = filtered_data

        # Calculate time left on the shot clock
        shot_data['TIME_LEFT'] =  shot_data['SHOT_CLOCK']

        # Define thresholds manually
        thresholds = {
            'SHOT_DIST': 'Distance',
            'TIME_LEFT': 'Time Left',
            'CLOSE_DEF_DIST': 'Defender Distance',
            'DRIBBLES': 'Dribbles'
        }

        # Define function to categorize data into categories with descriptive names and ranges
        def categorize_data(data, column):
            if column == 'DRIBBLES':
                bins = [0, 1, data[column].astype(float).max()]
                labels = ['Few Dribbles (0-1)', f'Many Dribbles (2+)']
            elif column == 'SHOT_DIST':
                bins = [0, 14, data[column].astype(float).max()]
                labels = ['Short Distance (0-14 feet)', f'Long Distance (14+ feet)']
            elif column == 'TIME_LEFT':
                bins = [0, 12, 24]
                labels = ['Low Time Left (0-12 seconds)', 'High Time Left (12-24 seconds)']
            elif column == 'CLOSE_DEF_DIST':
                bins = [0, 3.8, data[column].astype(float).max()]
                labels = ['Tight Defense (0-3.8 feet)', f'Loose Defense (3.8+ feet)']
            return pd.cut(data[column].astype(float), bins=bins, labels=labels, right=False)

        # Apply categorization to the data
        for column, label in thresholds.items():
            shot_data[f'{label}_category'] = categorize_data(shot_data, column)

        # Prepare the data for the visualizations
        def prepare_data_for_plotting(data):
            categories_summary = []
            for column, label in thresholds.items():
                shooting_percentage = data.groupby(f'{label}_category', observed=True)['FGM'].mean() * 100
                categories_summary.extend([(lvl, pct) for lvl, pct in shooting_percentage.items()])
            categories_summary.sort(key=lambda x: x[1])
            return categories_summary

        team1_data = shot_data[shot_data['team_name'] == team1]
        team2_data = shot_data[shot_data['team_name'] == team2] if team2 else None

        team1_summary = prepare_data_for_plotting(team1_data)
        team2_summary = prepare_data_for_plotting(team2_data) if team2 else []

        # Create Plotly figures for individual team comparisons
        def create_plotly_bar(summary, team_color, title):
            labels, values = zip(*summary)
            fig = go.Figure(go.Bar(
                x=values,
                y=labels,
                orientation='h',
                marker=dict(color=team_color)
            ))
            fig.update_layout(
                title=title,
                xaxis_title='Shooting Percentage',
                yaxis_title='Category',
                height=400,
                xaxis=dict(range=[0, 60]),  # Extend x-axis to 60
            )
            return fig

        # Layout with columns for side-by-side comparison
        col1, col2 = st.columns([1, 1])

        # Left Column: Individual team comparisons
        with col1:
            team1_fig = create_plotly_bar(team1_summary, '#1f77b4', f'Shooting Percentage by Category for {team1}')
            st.plotly_chart(team1_fig, use_container_width=True)
            
            if team2:
                team2_fig = create_plotly_bar(team2_summary, '#ff7f0e', f'Shooting Percentage by Category for {team2}')
                st.plotly_chart(team2_fig, use_container_width=True)

        # Right Column: Comparison figure between the two teams
        with col2:
            if team2:
                with st.container():
                    comparison_labels, comparison_values, team1_better = zip(*[(label, abs(g_value - a_value), g_value > a_value) for (label, g_value), (_, a_value) in zip(team1_summary, team2_summary)])

                    comparison_df = pd.DataFrame({
                        'Category': comparison_labels,
                        'Difference': comparison_values,
                        'Team': [team1 if is_team1 else team2 for is_team1 in team1_better]
                    }).sort_values(by='Difference')

                    comparison_fig = go.Figure(go.Bar(
                        x=comparison_df['Difference'],
                        y=comparison_df['Category'],
                        orientation='h',
                        marker=dict(color=['#1f77b4' if team == team1 else '#ff7f0e' for team in comparison_df['Team']])
                    ))
                    comparison_fig.update_layout(
                        title='Absolute Difference in Shooting Percentage',
                        xaxis_title='Absolute Difference in Shooting Percentage',
                        yaxis_title='Category',
                        height=400,
                        xaxis=dict(range=[0, comparison_df['Difference'].max() + 2])  # Extend x-axis to max + 2
                    )

                    st.plotly_chart(comparison_fig, use_container_width=True)

        # Section for multi-team comparison
        st.subheader("Comparison of Multiple Teams")

        # New filter for selecting multiple teams (no max limit)
        selected_teams_multi = st.multiselect(
            "Select Teams for Multi-Team Comparison:",
            options=shot_data['team_name'].unique(),
            default=['Golden State Warriors', 'Los Angeles Lakers', 'Atlanta Hawks']
        )

        # Prepare and display the multi-team comparison chart
        if selected_teams_multi:
            team_data = filtered_data[filtered_data['team_name'].isin(selected_teams_multi)]
            team_summaries = []

            for team in selected_teams_multi:
                team_df = team_data[team_data['team_name'] == team]
                team_summary = []
                for label in thresholds.values():
                    shooting_percentage = team_df.groupby(f'{label}_category')['FGM'].mean() * 100
                    team_summary.extend([(team, lvl, pct) for lvl, pct in shooting_percentage.items()])
                team_summaries.extend(team_summary)

            comparison_df_multi = pd.DataFrame(team_summaries, columns=['Team', 'Category', 'Shooting Percentage'])

            fig_multi = px.bar(
                comparison_df_multi, 
                x='Shooting Percentage', 
                y='Category', 
                color='Team', 
                orientation='h', 
                barmode='group',
                color_discrete_sequence=px.colors.qualitative.Plotly
            )

            fig_multi.update_layout(
                title='Shooting Percentage Comparison for Multiple Teams',
                xaxis_title='Shooting Percentage',
                yaxis_title='Category',
                xaxis=dict(range=[0, 60]),
                height=600
            )

            st.plotly_chart(fig_multi, use_container_width=True)
