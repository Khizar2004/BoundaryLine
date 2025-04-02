from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from cricket.models import Player
from cricket.forms import PlayerForm
from cricket.services import player_service

def player_list(request):
    """Display list of all players."""
    players = Player.objects.all()
    return render(request, 'cricket/player_list.html', {'players': players})

@login_required
def add_player(request):
    """Handle adding a new player."""
    if request.method == 'POST':
        form = PlayerForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('player_list')
    else:
        form = PlayerForm()
    return render(request, 'cricket/add_player.html', {'form': form})

def player_detail(request, player_id):
    """Display details of a specific player."""
    player = player_service.get_player_by_id(player_id)
    
    # Get statistics
    matches_played = player.batting_matches.count() + player.bowling_matches.count()
    
    # Calculate additional stats
    context = {
        'player': player,
        'matches_played': matches_played,
        'total_runs': player.runs,
        'total_wickets': player.wickets,
        'economy': player.economy,
        'strike_rate': player.strike_rate
    }
    
    return render(request, 'cricket/player_detail.html', context) 