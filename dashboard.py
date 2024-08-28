import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import warnings
import numpy as np
import plotly.express as px
import plotly.io as pio
from plotly.subplots import make_subplots


# Initial setup
warnings.filterwarnings('ignore')
st.set_page_config(page_title="NBA Shot Analysis!!!", page_icon=":bar_chart:", layout="wide")
st.title(" :bar_chart: NBA Shot Analysis Dashboard :basketball: ")

st.sidebar.header("Choose your filter: ")

# Load the data
shot_data = pd.read_csv("shot_logs.csv", encoding="ISO-8859-1")
shot_data['TIME_LEFT'] = 24 - shot_data['SHOT_CLOCK']


player_df = pd.read_csv('players_teams.csv')
shot_data = shot_data.merge(player_df, how='left', left_on='player_name', right_on='Player')
shot_data = shot_data.drop(columns=['Player'])


before_filter = shot_data



# filter for the data
famous_players = [
    'LeBron James', 'Kobe Bryant', 'Stephen Curry', 'Kevin Durant',
    'Chris Paul', 'Tim Duncan', 'Dirk Nowitzki', 'Dwyane Wade',
    'Kawhi Leonard', 'Russell Westbrook', 'James Harden', 'Carmelo Anthony',
    'Paul Pierce', 'Klay Thompson', 'Pau Gasol', 'Blake Griffin',
    'Anthony Davis', 'Marc Gasol', 'Damian Lillard', 'Giannis Antetokounmpo'
]

# Player selection filter
selected_players = st.sidebar.multiselect(
    "Select players to display:",
    options=famous_players,
    default=['LeBron James', 'Stephen Curry']
)

# implement filter nulti value for team name , team name is in the column team_name
selected_teams = st.sidebar.multiselect(
    "Select Teams to display:",
    options=shot_data['team_name'].unique(),
    default=['Los Angeles Lakers', 'Golden State Warriors']
)

# Implement the Home/Away filter
game_location = st.sidebar.selectbox(
    "Select Game Location",
    options=["All","Home", "Away"],
    index=0  # Default to "Home"
)
game_quarter = st.sidebar.selectbox(
    "Select Game Quarter",
    options=["All","1", "2","3","4"],
    index=0  # Default to "Home"
)

# add filter for shoot type 2 or 3 points or All
shoot_type = st.sidebar.selectbox(
    "Select Shoot Type",
    options=["All","2 Points", "3 Points"],
    index=0  # Default to "Home"
)


game_close = st.sidebar.selectbox(
    "Select final Game Margin",
    options=["All","Below 5 points", "More than 5 points"],
    index=0  # Default to "Home"
)

if game_location == "Home":
    game_location = "H"
elif game_location == "Away":   
    game_location = "A"
else :
    game_location = "All"

# Filter the data based on the selected game location
if game_location == "All":
    filtered_data = shot_data
else:
    filtered_data = shot_data[shot_data['LOCATION'] == game_location]

# Filter the data based on the selected game quarter
if game_quarter != "All":
    filtered_data = filtered_data[filtered_data['PERIOD'] == int(game_quarter)]


# Filter the data based on the selected game margin
if game_close == "Below 5 points":
    filtered_data = filtered_data[abs(filtered_data['FINAL_MARGIN']) <= 5]    
elif game_close == "More than 5 points":
    filtered_data = filtered_data[abs(filtered_data['FINAL_MARGIN']) > 5]

# Filter the data based on the selected shoot type PTS_TYPE values are 2 or 3
if shoot_type == "2 Points":
    filtered_data = filtered_data[filtered_data['PTS_TYPE'] == 2]
elif shoot_type == "3 Points":
    filtered_data = filtered_data[filtered_data['PTS_TYPE'] == 3]





# Visualization 1: Shots Taken and Shooting Percentage by Time Left on Shot Clock
#appy the filter to the data
shot_data = filtered_data

# Create shot clock categories
shot_data['SHOT_CLOCK_CATEGORY'] = pd.cut(shot_data['SHOT_CLOCK'], bins=[0, 5, 10, 15, 20, 24], labels=['0-5', '5-10', '10-15', '15-20', '20-24'])

# Calculate the number of shots and shooting percentage by shot clock category
shot_clock_summary = shot_data.groupby('SHOT_CLOCK_CATEGORY').agg({
    'SHOT_CLOCK': 'count',
    'FGM': 'sum'
}).rename(columns={'SHOT_CLOCK': 'Shots'}).reset_index()

# Calculate shooting percentage
shot_clock_summary['Shooting_Percentage'] = (shot_clock_summary['FGM'] / shot_clock_summary['Shots']) * 100

# Create the dual-axis chart
fig_dual = go.Figure()

# Add the bar trace for 'Shots Taken'
fig_dual.add_trace(go.Bar(
    x=shot_clock_summary['SHOT_CLOCK_CATEGORY'],
    y=shot_clock_summary['Shots'],
    name='Shots Taken',
    marker=dict(color='lightblue'),
    yaxis='y'
))

# Add the line trace for 'Shooting Percentage'
fig_dual.add_trace(go.Scatter(
    x=shot_clock_summary['SHOT_CLOCK_CATEGORY'],
    y=shot_clock_summary['Shooting_Percentage'],
    mode='lines+markers',
    name='Shooting Percentage',
    line=dict(color='darkgreen', width=4, dash='dash'),
    yaxis='y2'
))

# Update the layout for the dual-axis chart
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
    showlegend=True
)

# Visualization 2: Shooting Percentage & Shot Count Comparison for Famous NBA Players
# apply the filter to the data
shot_data = filtered_data


# Filter data for the selected players
famous_players_data = shot_data[shot_data['player_name'].isin([
    player.lower() for player in selected_players
])]

# Define bins and labels with descriptive names including ranges
famous_players_data['Distance'] = pd.cut(famous_players_data['SHOT_DIST'],
                                         bins=[0, 14, famous_players_data['SHOT_DIST'].max()],
                                         labels=['Short Distance (0-14 feet)',
                                                 f'Long Distance (14+ feet)'], right=False)

famous_players_data['Time Left'] = pd.cut(famous_players_data['TIME_LEFT'],
                                          bins=[0, 12, 24],
                                          labels=['Low Time Left (0-12 seconds)',
                                                  'High Time Left (12-24 seconds)'], right=False)

famous_players_data['Defender Distance'] = pd.cut(famous_players_data['CLOSE_DEF_DIST'],
                                                  bins=[0, 3.8, famous_players_data['CLOSE_DEF_DIST'].max()],
                                                  labels=['Tight Defense (0-3.8 feet)',
                                                          f'Loose Defense (3.8+ feet)'], right=False)

famous_players_data['Dribbles'] = pd.cut(famous_players_data['DRIBBLES'],
                                         bins=[0, 1, famous_players_data['DRIBBLES'].max()],
                                         labels=['Few Dribbles (0-1)',
                                                 'Many Dribbles (2+)'], right=False)

# Define the functions to calculate shooting percentage and count shots
def calculate_shooting_percentage(data):
    return (data['FGM'].sum() / len(data)) * 100

def count_shots(data):
    return len(data)

# Create a summary table for each category separately
categories = ['Distance', 'Time Left', 'Defender Distance', 'Dribbles']
summary_table = pd.DataFrame(columns=['Category', 'Player', 'Shooting Percentage', 'Shot Count'])

for category in categories:
    for level in famous_players_data[category].cat.categories:
        for player in selected_players:
            player_pct = calculate_shooting_percentage(famous_players_data[(famous_players_data['player_name'] == player.lower()) & (famous_players_data[category] == level)])
            player_count = count_shots(famous_players_data[(famous_players_data['player_name'] == player.lower()) & (famous_players_data[category] == level)])
            summary_table = pd.concat([summary_table, pd.DataFrame([{'Category': f'{level}', 'Player': player, 'Shooting Percentage': round(player_pct, 1), 'Shot Count': player_count}])])

# Ensure that 'Shot Count' is numeric
summary_table['Shot Count'] = summary_table['Shot Count'].astype(float)

# Create the Plotly figure
fig = go.Figure()

# Add scatter traces for each selected player
for player in selected_players:
    player_data = summary_table[summary_table['Player'] == player]
    fig.add_trace(go.Scatter(
        x=player_data['Category'],
        y=player_data['Shooting Percentage'],
        mode='markers',
        marker=dict(
            size=player_data['Shot Count'],
            sizemode='area',
            sizeref=2.*max(summary_table['Shot Count'])/(23.**2),  # Size scaling
            line_width=2,
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
fig.update_layout(
    title='Shooting Percentage & Shot Count Comparison: Famous NBA Players ',
    xaxis_title='Category',
    yaxis_title='Shooting Percentage',
    legend_title_text='Player',
    yaxis=dict(range=[20, 70]),  # This sets the y-axis limit
    xaxis_tickangle=28,  # This rotates the x-axis labels to the right
    xaxis_tickfont_size=11,  # This sets the font size for the x-axis labels
    width=1300,  # Increase the width of the chart
    height=500  # Increase the height of the chart
)



# Visualization 3: Shooting Percentage Comparison: Catch and Shoot vs After Dribble Shot
# apply the filter to the data
shot_data = filtered_data

if 'shot_data' in locals():
    shot_data['SHOT_CLOCK'].fillna(0, inplace=True)
    shot_data['TIME_LEFT'] = 24 - shot_data['SHOT_CLOCK']


    
    
    

    # Continue preparing the filtered data
    filtered_data['SHOT_DIST'] = np.ceil(filtered_data['SHOT_DIST'])
    filtered_data['TIME_LEFT'] = np.ceil(filtered_data['TIME_LEFT'])
    filtered_data['CLOSE_DEF_DIST'] = np.ceil(filtered_data['CLOSE_DEF_DIST'])

    # Classify shots as Catch and Shoot or not
    filtered_data['Catch and Shoot'] = filtered_data['DRIBBLES'] < 1.0

    # Create categories with descriptive names and ranges
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

    # Define a function to calculate shooting percentage
    def calculate_shooting_percentage(data):
        return (data['FGM'].sum() / len(data)) * 100

    # Create summary tables for Catch and Shoot and Not Catch and Shoot
    categories = ['Distance', 'Time Left', 'Defender Distance']
    summary_table = pd.DataFrame(columns=['Category', 'Type', 'Shooting Percentage'])

    for category in categories:
        for level in filtered_data[category].cat.categories:
            catch_and_shoot = calculate_shooting_percentage(filtered_data[(filtered_data['Catch and Shoot']) & (filtered_data[category] == level)])
            not_catch_and_shoot = calculate_shooting_percentage(filtered_data[(filtered_data['Catch and Shoot'] == False) & (filtered_data[category] == level)])
            summary_table = pd.concat([summary_table, pd.DataFrame([{'Category': f'{level}', 'Type': 'Catch and Shoot', 'Shooting Percentage': catch_and_shoot}])])
            summary_table = pd.concat([summary_table, pd.DataFrame([{'Category': f'{level}', 'Type': 'After Dribble Shot', 'Shooting Percentage': not_catch_and_shoot}])])

    # Create a grouped bar chart using Plotly Graph Objects
    fig3 = go.Figure()

    # Add bars for Catch and Shoot
    fig3.add_trace(go.Bar(
        x=summary_table[summary_table['Type'] == 'Catch and Shoot']['Category'],
        y=summary_table[summary_table['Type'] == 'Catch and Shoot']['Shooting Percentage'],
        name='Catch and Shoot',
        marker_color='royalblue'
    ))

    # Add bars for After Dribble Shot
    fig3.add_trace(go.Bar(
        x=summary_table[summary_table['Type'] == 'After Dribble Shot']['Category'],
        y=summary_table[summary_table['Type'] == 'After Dribble Shot']['Shooting Percentage'],
        name='After Dribble Shot',
        marker_color='darkorange'
    ))

    # Update layout
    fig3.update_layout(
        barmode='group',  # Group bars together for each category
        title=f'Shooting Percentage Comparison: Catch and Shoot vs After Dribble Shot',
        xaxis_title='Category',
        yaxis_title='Shooting Percentage',
        legend_title_text='Type',
        yaxis=dict(range=[0, 70]),  # This sets the y-axis limit to 70
        bargap=0.38,  # Gap between bars
        xaxis_tickfont_size=11  # This sets the font size for the x-axis labels
    )



# Visualization 4: Teams Comparison
shot_data = filtered_data



# Prepare the data
if 'shot_data' in locals():
    shot_data['SHOT_CLOCK'].fillna(0, inplace=True)

    # Calculate time left on the shot clock
    shot_data['TIME_LEFT'] = 24 - shot_data['SHOT_CLOCK']

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

        short = data[data[column].astype(float) <= bins[1]]
        long = data[data[column].astype(float) > bins[1]]
        return short, long, labels, bins

    # Create bins for each threshold
    shot_data_categories = {}
    for column, label in thresholds.items():
        short, long, category_labels, category_bins = categorize_data(shot_data, column)
        shot_data[f'{label}_category'] = pd.cut(shot_data[column].astype(float), bins=category_bins, labels=category_labels, right=False)
        shot_data_categories[label] = (category_labels, category_bins)


     # Filter data based on selected teams
    team_data = shot_data[shot_data['team_name'].isin(selected_teams)]

    # Calculate shooting percentage for each category for each team
    team_summaries = []
    for team in selected_teams:
        team_df = team_data[team_data['team_name'] == team]
        team_summary = []
        for label in thresholds.values():
            shooting_percentage = team_df.groupby(f'{label}_category')['FGM'].mean() * 100
            team_summary.extend([(team, lvl, pct) for lvl, pct in shooting_percentage.items()])
        team_summaries.extend(team_summary)

    # Prepare data for plotting
    comparison_df = pd.DataFrame(team_summaries, columns=['Team', 'Category', 'Shooting Percentage'])

    # Create the plot using Plotly
    fig4 = px.bar(
        comparison_df, 
        x='Shooting Percentage', 
        y='Category', 
        color='Team', 
        orientation='h', 
        barmode='group',
        color_discrete_sequence=px.colors.qualitative.Plotly
    )

    # Customize the layout
    fig4.update_layout(
        title='Shooting Percentage Comparison Teams',
        xaxis_title='Shooting Percentage',
        yaxis_title='Category',
        xaxis=dict(range=[0, 60]),  # Extend x-axis to 60
        height=600
    )



# every visualization same size
width = 600
height = 500
# Update the layout of the figures
fig_dual.update_layout(width=width, height=height)  
fig.update_layout(width=width, height=height)
fig3.update_layout(width=width, height=height)
fig4.update_layout(width=width, height=height)



# Add a second row for the third visualization
col3, col4 = st.columns(2)

with col3:
    st.plotly_chart(fig4, use_container_width=True)  # Third visualization in the second row

with col4:
    # present visualization 4

    st.plotly_chart(fig, use_container_width=True)

# Create a grid layout with 2 visualizations per row
col1, col2 = st.columns(2)

with col1:
    st.plotly_chart(fig_dual, use_container_width=True)

with col2:
    st.plotly_chart(fig3, use_container_width=True)





