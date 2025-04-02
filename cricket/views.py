# Redirect imports to new view modules
from cricket.views.auth_views import signup_view, login_view, logout_view
from cricket.views.match_views import (
    match_list, add_match, match_details, delete_match, delete_all_matches,
    start_game, live_match, get_live_match_data, update_match
)
from cricket.views.player_views import player_list, add_player
from cricket.views.game_flow_views import (
    set_bowler, select_next_bowler, select_next_batter, handle_wicket
)
from cricket.views.base_views import home, clear_message_flag

# Export all views to maintain backward compatibility with URLs
__all__ = [
    'signup_view', 'login_view', 'logout_view',
    'match_list', 'add_match', 'match_details', 'delete_match', 'delete_all_matches',
    'start_game', 'live_match', 'get_live_match_data', 'update_match',
    'player_list', 'add_player',
    'set_bowler', 'select_next_bowler', 'select_next_batter', 'handle_wicket',
    'home', 'clear_message_flag'
]