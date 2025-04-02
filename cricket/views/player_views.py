from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from cricket.models import Player
from cricket.forms import PlayerForm

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