"""
Statistella Strategic Dashboard
NBA Analytics Platform for the Statistella Business Festival

Author: Chief Data Strategist
Purpose: Transform raw NBA data into actionable business insights
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="Statistella Strategic Dashboard | NBA Analytics",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for premium styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.8rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #888;
        text-align: center;
        margin-bottom: 2rem;
    }
    .insight-box {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-left: 4px solid #667eea;
        padding: 1rem;
        border-radius: 0 8px 8px 0;
        margin: 1rem 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #0f0f23 0%, #1a1a40 100%);
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        border: 1px solid #333;
    }
    .section-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #667eea;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #667eea;
        padding-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# DATA LOADING & CLEANING
# ============================================================================
@st.cache_data
def load_and_clean_data():
    """Load and preprocess all NBA data files."""
    import zipfile
    import os
    
    # Extract CSVs from zips if they don't exist
    zip_files = ['games.csv.zip', 'ranking.csv.zip', 'games_details.csv.zip']
    for zf in zip_files:
        csv_name = zf.replace('.zip', '')
        if not os.path.exists(csv_name) and os.path.exists(zf):
            with zipfile.ZipFile(zf, 'r') as z:
                z.extractall('.')
    
    # Load CSVs
    games = pd.read_csv('games.csv')
    teams = pd.read_csv('teams.csv')
    ranking = pd.read_csv('ranking.csv')
    games_details = pd.read_csv('games_details.csv', low_memory=False)
    
    # Clean games data
    games['GAME_DATE_EST'] = pd.to_datetime(games['GAME_DATE_EST'], errors='coerce')
    games['SEASON'] = games['SEASON'].astype(int)
    games = games[games['SEASON'] >= 2004]  # Filter for 2004 onwards
    
    # Handle missing values - drop games with missing scores for accurate analysis
    games = games.dropna(subset=['PTS_home', 'PTS_away'])
    games['PTS_home'] = games['PTS_home'].astype(float)
    games['PTS_away'] = games['PTS_away'].astype(float)
    
    # Create Total Points column for game excitement analysis
    games['TOTAL_POINTS'] = games['PTS_home'] + games['PTS_away']
    
    # Merge games with teams for home and visitor names
    games = games.merge(
        teams[['TEAM_ID', 'ABBREVIATION', 'NICKNAME', 'CITY']],
        left_on='HOME_TEAM_ID',
        right_on='TEAM_ID',
        how='left'
    ).rename(columns={'ABBREVIATION': 'HOME_ABBR', 'NICKNAME': 'HOME_TEAM', 'CITY': 'HOME_CITY'})
    
    games = games.merge(
        teams[['TEAM_ID', 'ABBREVIATION', 'NICKNAME', 'CITY']],
        left_on='VISITOR_TEAM_ID',
        right_on='TEAM_ID',
        how='left',
        suffixes=('', '_visitor')
    ).rename(columns={'ABBREVIATION': 'VISITOR_ABBR', 'NICKNAME': 'VISITOR_TEAM', 'CITY': 'VISITOR_CITY'})
    
    # Clean ranking data
    # SEASON_ID format: SeasonType (1-2 digits) + Year (4 digits), e.g., 22022 = Regular 2022-23
    # Extract the year portion correctly
    ranking['SEASON_YEAR'] = ranking['SEASON_ID'].apply(
        lambda x: int(str(x)[-4:]) if len(str(x)) >= 4 else int(str(x))
    )
    ranking = ranking[ranking['SEASON_YEAR'] >= 2004]
    
    # Clean games_details
    games_details['PTS'] = pd.to_numeric(games_details['PTS'], errors='coerce').fillna(0)
    games_details['FGA'] = pd.to_numeric(games_details['FGA'], errors='coerce').fillna(0)
    games_details['FGM'] = pd.to_numeric(games_details['FGM'], errors='coerce').fillna(0)
    games_details['AST'] = pd.to_numeric(games_details['AST'], errors='coerce').fillna(0)
    games_details['REB'] = pd.to_numeric(games_details['REB'], errors='coerce').fillna(0)
    
    return games, teams, ranking, games_details


# Load data
try:
    games, teams, ranking, games_details = load_and_clean_data()
    data_loaded = True
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.info("Please ensure all CSV files (games.csv, teams.csv, ranking.csv, games_details.csv) are in the current directory.")
    data_loaded = False

if data_loaded:
    # ============================================================================
    # SIDEBAR FILTERS
    # ============================================================================
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2534/2534594.png", width=80)
    st.sidebar.markdown("## 🎯 **Dashboard Filters**")
    st.sidebar.markdown("---")
    
    # Season filter
    available_seasons = sorted(games['SEASON'].unique(), reverse=True)
    selected_season = st.sidebar.selectbox(
        "📅 Select Season",
        options=available_seasons,
        index=0
    )
    
    # Team filter
    team_options = sorted(teams['NICKNAME'].dropna().unique())
    selected_team = st.sidebar.selectbox(
        "🏀 Select Team",
        options=['All Teams'] + team_options,
        index=0
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Quick Stats")
    
    # Calculate quick stats
    total_games = len(games)
    total_seasons = len(games['SEASON'].unique())
    avg_score = games['TOTAL_POINTS'].mean()
    
    st.sidebar.metric("Total Games Analyzed", f"{total_games:,}")
    st.sidebar.metric("Seasons Covered", total_seasons)
    st.sidebar.metric("Avg Points/Game", f"{avg_score:.1f}")
    
    # ============================================================================
    # MAIN DASHBOARD
    # ============================================================================
    st.markdown('<h1 class="main-header">🏀 Statistella Strategic Dashboard</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Transforming NBA Data into Business Intelligence | 2004–Present</p>', unsafe_allow_html=True)
    
    # Create tabs for different sections
    tab1, tab2, tab3 = st.tabs(["📈 **Macro Trends**", "🏆 **Team & Conference Dynamics**", "👤 **Player Impact Analysis**"])
    
    # ============================================================================
    # TAB 1: MACRO VIEW (STRATEGIC TRENDS)
    # ============================================================================
    with tab1:
        st.markdown('<p class="section-title">Strategic League Trends: The Evolution of NBA Scoring</p>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Average League Scoring per Season
            scoring_trend = games.groupby('SEASON').agg({
                'PTS_home': 'mean',
                'PTS_away': 'mean',
                'TOTAL_POINTS': 'mean'
            }).reset_index()
            
            fig_scoring = go.Figure()
            
            fig_scoring.add_trace(go.Scatter(
                x=scoring_trend['SEASON'],
                y=scoring_trend['TOTAL_POINTS'],
                mode='lines+markers',
                name='Total Points',
                line=dict(color='#667eea', width=3),
                marker=dict(size=8),
                fill='tozeroy',
                fillcolor='rgba(102, 126, 234, 0.2)'
            ))
            
            fig_scoring.update_layout(
                title=dict(text='Average Total Points Per Game (2004–Present)', font=dict(size=18)),
                xaxis_title='Season',
                yaxis_title='Average Points',
                template='plotly_dark',
                height=400,
                hovermode='x unified'
            )
            
            # Add annotation for 3-point revolution
            if 2015 in scoring_trend['SEASON'].values:
                pts_2015 = scoring_trend[scoring_trend['SEASON'] == 2015]['TOTAL_POINTS'].values
                if len(pts_2015) > 0:
                    fig_scoring.add_annotation(
                        x=2015, y=pts_2015[0] + 5,
                        text="3-Point Revolution Era Begins",
                        showarrow=True,
                        arrowhead=2,
                        arrowcolor='#ff6b6b',
                        font=dict(color='#ff6b6b', size=11)
                    )
            
            st.plotly_chart(fig_scoring, use_container_width=True)
        
        with col2:
            st.markdown("### 📊 Key Insights")
            
            # Calculate trend
            recent_avg = scoring_trend[scoring_trend['SEASON'] >= 2018]['TOTAL_POINTS'].mean()
            early_avg = scoring_trend[scoring_trend['SEASON'] <= 2010]['TOTAL_POINTS'].mean()
            pct_change = ((recent_avg - early_avg) / early_avg) * 100
            
            trend_direction = "📈 **Upward Trend**" if pct_change > 0 else "📉 **Downward Trend**"
            
            st.markdown(f"""
            <div class="insight-box">
            <strong>{trend_direction}</strong><br><br>
            NBA scoring has changed by <strong>{pct_change:.1f}%</strong> from the early 2000s to recent seasons.<br><br>
            <em>Note the spike in scoring post-2015, correlating with the league-wide 
            shift to perimeter shooting and pace-and-space offense.</em>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Home vs Away Win Percentage Analysis
        st.markdown('<p class="section-title">Home Court Advantage: A Strategic Analysis</p>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Calculate home vs away wins
            total_games_played = len(games.dropna(subset=['HOME_TEAM_WINS']))
            home_wins = games['HOME_TEAM_WINS'].sum()
            away_wins = total_games_played - home_wins
            
            home_pct = (home_wins / total_games_played) * 100
            away_pct = (away_wins / total_games_played) * 100
            
            fig_home_away = go.Figure(data=[
                go.Bar(
                    name='Home Wins',
                    x=['Win Rate'],
                    y=[home_pct],
                    marker_color='#667eea',
                    text=[f'{home_pct:.1f}%'],
                    textposition='auto'
                ),
                go.Bar(
                    name='Away Wins',
                    x=['Win Rate'],
                    y=[away_pct],
                    marker_color='#f093fb',
                    text=[f'{away_pct:.1f}%'],
                    textposition='auto'
                )
            ])
            
            fig_home_away.update_layout(
                title='Global Home vs Away Win Percentage',
                template='plotly_dark',
                barmode='group',
                height=350,
                yaxis_title='Win Percentage (%)'
            )
            
            st.plotly_chart(fig_home_away, use_container_width=True)
        
        with col2:
            # Home advantage trend over seasons
            home_adv_trend = games.groupby('SEASON').agg({
                'HOME_TEAM_WINS': ['sum', 'count']
            }).reset_index()
            home_adv_trend.columns = ['SEASON', 'HOME_WINS', 'TOTAL_GAMES']
            home_adv_trend['HOME_WIN_PCT'] = (home_adv_trend['HOME_WINS'] / home_adv_trend['TOTAL_GAMES']) * 100
            
            fig_home_trend = px.line(
                home_adv_trend,
                x='SEASON',
                y='HOME_WIN_PCT',
                markers=True,
                title='Home Court Advantage Trend by Season'
            )
            
            fig_home_trend.add_hline(y=50, line_dash="dash", line_color="red", 
                                      annotation_text="50% Baseline")
            
            fig_home_trend.update_traces(line_color='#764ba2', line_width=2)
            fig_home_trend.update_layout(
                template='plotly_dark',
                height=350,
                yaxis_title='Home Win %'
            )
            
            st.plotly_chart(fig_home_trend, use_container_width=True)
        
        # Business insight for home advantage
        st.markdown(f"""
        <div class="insight-box">
        <strong>🏠 Strategic Insight: Home Court Advantage</strong><br><br>
        Historically, home teams win approximately <strong>{home_pct:.1f}%</strong> of games, 
        representing a <strong>{home_pct - 50:.1f}%</strong> advantage over pure chance.<br><br>
        <em>This has significant implications for playoff seeding strategy and 
        ticket revenue projections. Teams should prioritize securing home court advantage 
        in playoff positioning.</em>
        </div>
        """, unsafe_allow_html=True)
    
    # ============================================================================
    # TAB 2: TEAM & CONFERENCE DYNAMICS
    # ============================================================================
    with tab2:
        st.markdown('<p class="section-title">Conference Comparison: East vs West</p>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Conference win rates from ranking data
            # Get the latest standings date per season for accuracy
            latest_rankings = ranking.loc[ranking.groupby(['SEASON_ID', 'TEAM_ID'])['STANDINGSDATE'].idxmax()]
            
            conf_comparison = latest_rankings.groupby(['SEASON_YEAR', 'CONFERENCE']).agg({
                'W_PCT': 'mean'
            }).reset_index()
            
            fig_conf = px.line(
                conf_comparison,
                x='SEASON_YEAR',
                y='W_PCT',
                color='CONFERENCE',
                markers=True,
                title='Average Win Rate by Conference Over Time',
                color_discrete_map={'East': '#667eea', 'West': '#f093fb'}
            )
            
            fig_conf.update_layout(
                template='plotly_dark',
                height=400,
                yaxis_title='Average Win %',
                xaxis_title='Season'
            )
            
            st.plotly_chart(fig_conf, use_container_width=True)
        
        with col2:
            # Overall conference comparison for selected season
            season_ranking = latest_rankings[latest_rankings['SEASON_YEAR'] == selected_season]
            
            if not season_ranking.empty:
                conf_box = px.box(
                    season_ranking,
                    x='CONFERENCE',
                    y='W_PCT',
                    color='CONFERENCE',
                    title=f'Win % Distribution by Conference ({selected_season})',
                    color_discrete_map={'East': '#667eea', 'West': '#f093fb'}
                )
                conf_box.update_layout(template='plotly_dark', height=400)
                st.plotly_chart(conf_box, use_container_width=True)
            else:
                st.info(f"No ranking data available for {selected_season}")
        
        st.markdown("---")
        st.markdown('<p class="section-title">Selected Team Performance Analysis</p>', unsafe_allow_html=True)
        
        if selected_team != 'All Teams':
            # Get team ID
            team_info = teams[teams['NICKNAME'] == selected_team]
            
            if not team_info.empty:
                team_id = team_info['TEAM_ID'].values[0]
                
                # Filter games for selected team and season
                team_home = games[(games['HOME_TEAM_ID'] == team_id) & (games['SEASON'] == selected_season)]
                team_away = games[(games['VISITOR_TEAM_ID'] == team_id) & (games['SEASON'] == selected_season)]
                
                # Calculate wins and losses
                home_wins = len(team_home[team_home['HOME_TEAM_WINS'] == 1])
                home_losses = len(team_home[team_home['HOME_TEAM_WINS'] == 0])
                away_wins = len(team_away[team_away['HOME_TEAM_WINS'] == 0])
                away_losses = len(team_away[team_away['HOME_TEAM_WINS'] == 1])
                
                total_wins = home_wins + away_wins
                total_losses = home_losses + away_losses
                
                col1, col2, col3, col4 = st.columns(4)
                
                col1.metric("Total Wins", total_wins)
                col2.metric("Total Losses", total_losses)
                col3.metric("Home Record", f"{home_wins}-{home_losses}")
                col4.metric("Road Record", f"{away_wins}-{away_losses}")
                
                # Create win/loss trend over the season
                team_games = pd.concat([
                    team_home.assign(IS_HOME=1, WIN=team_home['HOME_TEAM_WINS']),
                    team_away.assign(IS_HOME=0, WIN=1 - team_away['HOME_TEAM_WINS'])
                ])
                
                if not team_games.empty:
                    team_games = team_games.sort_values('GAME_DATE_EST')
                    team_games['CUMULATIVE_WINS'] = team_games['WIN'].cumsum()
                    team_games['GAMES_PLAYED'] = range(1, len(team_games) + 1)
                    team_games['WIN_PCT'] = team_games['CUMULATIVE_WINS'] / team_games['GAMES_PLAYED']
                    
                    fig_trend = go.Figure()
                    
                    fig_trend.add_trace(go.Scatter(
                        x=team_games['GAMES_PLAYED'],
                        y=team_games['WIN_PCT'] * 100,
                        mode='lines+markers',
                        name='Win %',
                        line=dict(color='#667eea', width=3),
                        fill='tozeroy',
                        fillcolor='rgba(102, 126, 234, 0.3)'
                    ))
                    
                    fig_trend.add_hline(y=50, line_dash="dash", line_color="orange",
                                         annotation_text=".500 Record")
                    
                    fig_trend.update_layout(
                        title=f'{selected_team} Win Percentage Trend ({selected_season})',
                        xaxis_title='Games Played',
                        yaxis_title='Win Percentage (%)',
                        template='plotly_dark',
                        height=400
                    )
                    
                    st.plotly_chart(fig_trend, use_container_width=True)
                    
                    # Business insight
                    final_win_pct = (total_wins / (total_wins + total_losses)) * 100 if (total_wins + total_losses) > 0 else 0
                    
                    st.markdown(f"""
                    <div class="insight-box">
                    <strong>🎯 Team Performance Summary: {selected_team}</strong><br><br>
                    The {selected_team} finished the {selected_season} season with a 
                    <strong>{final_win_pct:.1f}%</strong> win rate ({total_wins}-{total_losses}).<br><br>
                    <em>{'Strong playoff contender status maintained.' if final_win_pct >= 60 else 
                       'Reliable mid-tier performance.' if final_win_pct >= 45 else
                       'Rebuilding phase indicated.'}</em>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning(f"No game data found for {selected_team} in {selected_season}")
            else:
                st.warning("Team not found in database")
        else:
            st.info("👆 Select a specific team from the sidebar to view detailed performance analysis.")
    
    # ============================================================================
    # TAB 3: PLAYER IMPACT (EFFICIENCY)
    # ============================================================================
    with tab3:
        st.markdown('<p class="section-title">Player Efficiency Analysis: Usage vs. Output</p>', unsafe_allow_html=True)
        
        st.markdown("""
        This analysis identifies key performers by comparing their **shot attempts (Usage)** 
        against **points scored (Efficiency)**. Players in the upper-right quadrant 
        represent high-volume, high-efficiency scorers.
        """)
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            # Get games for the selected season
            season_games = games[games['SEASON'] == selected_season]['GAME_ID'].unique()
            
            # Filter player stats for those games
            season_player_stats = games_details[games_details['GAME_ID'].isin(season_games)]
            
            # Aggregate player stats
            player_agg = season_player_stats.groupby('PLAYER_NAME').agg({
                'FGA': 'sum',
                'PTS': 'sum',
                'FGM': 'sum',
                'AST': 'sum',
                'REB': 'sum',
                'GAME_ID': 'count'
            }).reset_index()
            
            player_agg.columns = ['PLAYER_NAME', 'TOTAL_FGA', 'TOTAL_PTS', 'TOTAL_FGM', 'TOTAL_AST', 'TOTAL_REB', 'GAMES_PLAYED']
            
            # Filter for players with sufficient attempts
            min_games = st.slider("Minimum Games Played", 10, 50, 20)
            min_fga = st.slider("Minimum Field Goal Attempts", 50, 500, 200)
            
            qualified_players = player_agg[
                (player_agg['GAMES_PLAYED'] >= min_games) & 
                (player_agg['TOTAL_FGA'] >= min_fga)
            ]
            
            qualified_players['FG_PCT'] = qualified_players['TOTAL_FGM'] / qualified_players['TOTAL_FGA'] * 100
            qualified_players['PPG'] = qualified_players['TOTAL_PTS'] / qualified_players['GAMES_PLAYED']
            qualified_players['USAGE_RATE'] = qualified_players['TOTAL_FGA'] / qualified_players['GAMES_PLAYED']
            
            st.markdown(f"**{len(qualified_players)}** players qualified")
        
        with col2:
            if not qualified_players.empty:
                fig_player = px.scatter(
                    qualified_players,
                    x='USAGE_RATE',
                    y='PPG',
                    size='GAMES_PLAYED',
                    color='FG_PCT',
                    hover_name='PLAYER_NAME',
                    hover_data={
                        'USAGE_RATE': ':.1f',
                        'PPG': ':.1f',
                        'FG_PCT': ':.1f',
                        'GAMES_PLAYED': True
                    },
                    title=f'Player Usage (FGA/Game) vs Efficiency (PPG) - {selected_season}',
                    color_continuous_scale='Viridis'
                )
                
                fig_player.update_layout(
                    template='plotly_dark',
                    height=500,
                    xaxis_title='Usage (FGA per Game)',
                    yaxis_title='Points per Game',
                    coloraxis_colorbar_title='FG%'
                )
                
                # Add quadrant lines
                median_x = qualified_players['USAGE_RATE'].median()
                median_y = qualified_players['PPG'].median()
                
                fig_player.add_hline(y=median_y, line_dash="dot", line_color="gray", opacity=0.5)
                fig_player.add_vline(x=median_x, line_dash="dot", line_color="gray", opacity=0.5)
                
                st.plotly_chart(fig_player, use_container_width=True)
                
                # Top performers
                st.markdown("### 🌟 Top Performers (High Usage + High Efficiency)")
                
                top_performers = qualified_players[
                    (qualified_players['USAGE_RATE'] > median_x) & 
                    (qualified_players['PPG'] > median_y)
                ].nlargest(10, 'PPG')[['PLAYER_NAME', 'PPG', 'USAGE_RATE', 'FG_PCT', 'GAMES_PLAYED']]
                
                top_performers.columns = ['Player', 'PPG', 'FGA/Game', 'FG%', 'Games']
                
                st.dataframe(
                    top_performers.style.format({
                        'PPG': '{:.1f}',
                        'FGA/Game': '{:.1f}',
                        'FG%': '{:.1f}%'
                    }),
                    use_container_width=True,
                    hide_index=True
                )
                
                # Business insight
                if len(top_performers) > 0:
                    top_player = top_performers.iloc[0]['Player']
                    st.markdown(f"""
                    <div class="insight-box">
                    <strong>💎 Player Efficiency Insight</strong><br><br>
                    <strong>{top_player}</strong> leads as the most impactful scorer in {selected_season}, 
                    combining elite volume shooting with exceptional efficiency.<br><br>
                    <em>Players in the upper-right quadrant are the "franchise cornerstones" — 
                    they can handle high-volume offensive responsibility while maintaining 
                    above-average conversion rates. These are the assets worth investing in.</em>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning("No players meet the minimum criteria. Try lowering the filters.")
    
    # ============================================================================
    # FOOTER
    # ============================================================================
    st.markdown("---")
    max_season = max(games['SEASON'].unique())
    st.markdown(f"""
    <div style='text-align: center; color: #666; padding: 2rem 0;'>
        <p><strong>Statistella Strategic Dashboard</strong> | NBA Analytics Platform</p>
        <p>Data Coverage: 2004–{max_season} | Built with Streamlit & Plotly</p>
        <p style='font-size: 0.8rem;'>© 2026 Chief Data Strategist | Statistella Business Festival</p>
    </div>
    """, unsafe_allow_html=True)

