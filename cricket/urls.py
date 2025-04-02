from django.urls import path
from . import views
from .views import signup_view, login_view, logout_view

urlpatterns = [
    path('', views.home, name='home'),  # Homepage
    path('players/', views.player_list, name='player_list'),  # Player list
    path('players/<int:player_id>/', views.player_detail, name='player_detail'),  # Player details
    path('matches/', views.match_list, name='match_list'),  # Match list
    path('players/add/', views.add_player, name='add_player'),  # Add player
    path('matches/add/', views.add_match, name='add_match'),  # Add match
    path('matches/start-game/', views.start_game, name='start_game'),
    path('matches/live/<int:match_id>/', views.live_match, name='live_match'),
    path('select_next_bowler/<int:match_id>/', views.select_next_bowler, name='select_next_bowler'),
    path('matches/<int:match_id>/', views.match_details, name='match_details'),  # View match details
    path('matches/delete/<int:match_id>/', views.delete_match, name='delete_match'),  # Delete match
    path('matches/delete-all/', views.delete_all_matches, name='delete_all_matches'),
    path('clear-message-flag/', views.clear_message_flag, name='clear_message_flag'),
    path('live-match/<int:match_id>/data/', views.get_live_match_data, name='get_live_match_data'),
    path('update-match/', views.update_match, name='update_match'),
    path('set-bowler/<int:match_id>/', views.set_bowler, name='set_bowler'),
    path('match/<int:match_id>/select-next-batter/', views.select_next_batter, name='select_next_batter'),
    path('signup/', signup_view, name='signup'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
]
