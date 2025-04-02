from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from cricket.models import Match, Player, OutPlayer
from cricket.forms import PlayerSelectionForm
from cricket.services import match_service, player_service

def handle_wicket(request, match_id):
    """Handle a wicket and redirect to the next batter selection screen."""
    match = match_service.get_match_by_id(match_id)
    
    if match.striker:
        player_service.set_player_out(match.striker)
        
        # Create an OutPlayer entry
        OutPlayer.objects.create(
            match=match,
            player=match.striker,
            runs_scored=match.striker.runs,
            balls_faced=match.striker.balls_faced
        )
        
        # Clear the striker
        match.striker = None
        match.save()
    
    # Redirect to the "Select Next Batter" screen
    return redirect('select_next_batter', match_id=match_id)

@login_required
def set_bowler(request, match_id):
    """Handle selecting a bowler for the next over."""
    match = match_service.get_match_by_id(match_id)
    
    # Check if match is already completed
    if match.is_completed:
        return redirect('match_details', match_id=match.id)
    
    available_bowlers = player_service.get_available_bowlers(match)
    
    if request.method == 'POST':
        bowler_id = request.POST.get('bowler')
        if bowler_id:
            # Set new bowler
            bowler = player_service.get_player_by_id(bowler_id)
            match.previous_bowler = match.current_bowler
            match.current_bowler = bowler
            match.save()
            
            return redirect('live_match', match_id=match.id)
    
    return render(request, 'cricket/set_bowler.html', {
        'match': match,
        'available_bowlers': available_bowlers,
    })

@login_required
def select_next_bowler(request, match_id):
    """Select the next bowler after an over is completed."""
    # Reuse the set_bowler view to avoid code duplication
    return set_bowler(request, match_id)

@login_required
def select_next_batter(request, match_id):
    """Handle selecting the next batter after a wicket."""
    match = match_service.get_match_by_id(match_id)
    
    # Check if match is already completed
    if match.is_completed:
        return redirect('match_details', match_id=match.id)
    
    available_batters = player_service.get_available_batters(match)
    
    if request.method == 'POST':
        batter_id = request.POST.get('batter')
        if batter_id:
            # Set new batter
            batter = player_service.get_player_by_id(batter_id)
            
            # If striker is empty, fill it, otherwise assume non-striker is empty
            if not match.striker:
                match.striker = batter
            else:
                match.non_striker = batter
            
            match.save()
            
            # Check if we need a new bowler (end of over)
            if match.balls_bowled % 6 == 0 and match.balls_bowled > 0:
                return redirect('select_next_bowler', match_id=match.id)
            
            return redirect('live_match', match_id=match.id)
    
    return render(request, 'cricket/select_next_batter.html', {
        'match': match,
        'available_batters': available_batters,
    }) 