from django.shortcuts import get_object_or_404
from cricket.models import Player, Match

def get_player_by_id(player_id):
    """Retrieve a player by their ID or return 404 if not found."""
    return get_object_or_404(Player, id=player_id)

def get_team_players(team_name):
    """Get all players for a specific team."""
    return Player.objects.filter(team=team_name)

def get_available_batters(match):
    """
    Get all batters available to bat for the current batting team.
    
    Args:
        match: Match object with the current match state
    
    Returns:
        QuerySet of Player objects available to bat
    """
    batting_team = match.batting_team
    # Get all players in the batting team
    batting_team_players = Player.objects.filter(team=batting_team)
    
    # Filter out players who are already out
    available_batters = batting_team_players.filter(is_out=False)
    
    # Filter out players currently batting
    if match.striker:
        available_batters = available_batters.exclude(id=match.striker.id)
    if match.non_striker:
        available_batters = available_batters.exclude(id=match.non_striker.id)
    
    return available_batters

def get_available_bowlers(match):
    """
    Get all bowlers available to bowl for the current bowling team.
    
    Args:
        match: Match object with the current match state
    
    Returns:
        QuerySet of Player objects available to bowl
    """
    bowling_team = match.get_bowling_team()
    # Get all players in the bowling team
    bowling_team_players = Player.objects.filter(team=bowling_team)
    
    # Exclude the previous bowler to enforce bowling rotation
    if match.previous_bowler:
        bowling_team_players = bowling_team_players.exclude(id=match.previous_bowler.id)
    
    return bowling_team_players

def set_player_out(player):
    """Mark a player as out and save the change."""
    player.is_out = True
    player.save()
    return player 