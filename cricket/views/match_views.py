from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from cricket.models import Match, Player
from cricket.forms import MatchForm, StartGameForm, TeamSelectionForm
from cricket.services import match_service, player_service
import json
from datetime import date

@login_required
def match_list(request):
    """Display list of all matches created by the user."""
    matches = Match.objects.filter(created_by=request.user).order_by('-match_date')
    return render(request, 'cricket/match_list.html', {'matches': matches})

@login_required
def add_match(request):
    """Handle adding a new match."""
    if request.method == 'POST':
        form = MatchForm(request.POST)
        if form.is_valid():
            match = form.save(commit=False)
            match.created_by = request.user
            match.save()
            return redirect('match_list')
    else:
        form = MatchForm()
    return render(request, 'cricket/add_match.html', {'form': form})

@login_required
def match_details(request, match_id):
    """Display details of a specific match."""
    match = match_service.get_match_by_id(match_id)
    return render(request, 'cricket/match_details.html', {'match': match})

@login_required
def delete_match(request, match_id):
    """Handle deleting a match."""
    match = match_service.get_match_by_id(match_id)
    
    if request.method == 'POST':
        match.delete()
        return redirect('match_list')
    
    return render(request, 'cricket/delete_match.html', {'match': match})

@login_required
def delete_all_matches(request):
    """Handle deleting all matches created by the user."""
    if request.method == 'POST':
        Match.objects.filter(created_by=request.user).delete()
        return redirect('match_list')
    
    return render(request, 'cricket/delete_all_matches.html')

@login_required
def start_game(request):
    """Handle the game setup and starting a new match."""
    if request.method == 'POST':
        form = StartGameForm(request.POST)
        if form.is_valid():
            # Save basic match details
            match = form.save(commit=False)
            match.created_by = request.user
            match.location = "Home Ground"  # Default location
            match.match_date = date.today()  # Use today's date
            match.save()
            
            # Redirect to team selection
            return render(request, 'cricket/start_game.html', {
                'match': match,
                'team_form': TeamSelectionForm(),
                'step': 'team_selection'
            })
    elif request.method == 'GET' and 'match_id' in request.GET and 'step' in request.GET:
        # Handle team selection form submission
        match_id = request.GET.get('match_id')
        step = request.GET.get('step')
        match = match_service.get_match_by_id(match_id)
        
        if step == 'team_selection' and request.GET.get('form_submitted') == 'true':
            team_form = TeamSelectionForm(request.GET)
            if team_form.is_valid():
                # Process team selections
                team1_players = team_form.cleaned_data['team1_players']
                team2_players = team_form.cleaned_data['team2_players']
                
                # Update team for players
                with transaction.atomic():
                    for player in team1_players:
                        player.team = match.team1_name
                        player.save()
                        match.batters.add(player)
                    
                    for player in team2_players:
                        player.team = match.team2_name
                        player.save()
                        match.bowlers.add(player)
                
                # Set initial batting team
                match.batting_team = match.team1_name
                match.save()
                
                # Proceed to selecting opening batsmen and bowler
                return redirect('set_bowler', match_id=match.id)
        
        return render(request, 'cricket/start_game.html', {
            'match': match,
            'team_form': TeamSelectionForm(),
            'step': 'team_selection',
            'error': 'Please complete all required fields.'
        })
    else:
        # Initial form
        form = StartGameForm()
    
    return render(request, 'cricket/start_game.html', {
        'form': form,
        'step': 'match_details'
    })

@login_required
def live_match(request, match_id):
    """Display the live match scoring interface."""
    match = match_service.get_match_by_id(match_id)
    
    # Check if match is already completed
    if match.is_completed:
        return redirect('match_details', match_id=match.id)
    
    # Check if we need a bowler
    if not match.current_bowler:
        return redirect('set_bowler', match_id=match.id)
    
    # Check if we need batters
    if not match.striker or not match.non_striker:
        return redirect('select_next_batter', match_id=match.id)
    
    return render(request, 'cricket/live_match.html', {'match': match})

def get_live_match_data(request, match_id):
    """AJAX endpoint to get live match data."""
    match = match_service.get_match_by_id(match_id)
    
    # Calculate overs
    overs_completed = match.balls_bowled // 6
    # Use the property instead of calculating
    balls_in_current_over = match.balls_in_current_over
    
    data = {
        'team1_name': match.team1_name,
        'team2_name': match.team2_name,
        'team1_runs': match.team1_runs,
        'team2_runs': match.team2_runs,
        'team1_wickets': match.team1_wickets,
        'team2_wickets': match.team2_wickets,
        'overs': f"{overs_completed}.{balls_in_current_over}",
        'batting_team': match.batting_team,
        'is_free_hit': match.is_free_hit,
        'striker_name': match.striker.name if match.striker else "No striker",
        'non_striker_name': match.non_striker.name if match.non_striker else "No non-striker",
        'bowler_name': match.current_bowler.name if match.current_bowler else "No bowler",
        'striker_runs': match.striker.runs if match.striker else 0,
        'striker_balls': match.striker.balls_faced if match.striker else 0,
        'is_completed': match.is_completed,
        'winner': match.winner,
    }
    
    # Add required run rate for 2nd innings
    if match.batting_team == match.team2_name:
        data['target'] = match.team1_runs + 1
        
        # Calculate required runs and required run rate
        runs_required = data['target'] - match.team2_runs
        balls_remaining = (match.overs_per_side * 6) - match.balls_bowled
        
        data['runs_required'] = runs_required
        data['balls_remaining'] = balls_remaining
        
        if balls_remaining > 0:
            data['required_run_rate'] = round((runs_required * 6) / balls_remaining, 2)
        else:
            data['required_run_rate'] = 0
    
    return JsonResponse(data)

def update_match(request):
    """AJAX endpoint to update match score."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            action = data.get('action')
            match_id = data.get('match_id')
            match = match_service.get_match_by_id(match_id)
            
            # Check if match is already completed
            if match.is_completed:
                return JsonResponse({'error': 'Match is already completed'}, status=400)
            
            # Process special cases
            if action == 'add_wicket':
                return JsonResponse({'redirect': f'/match/{match_id}/select-next-batter/'})
            
            # Handle normal actions: add_run_X, add_wide, add_no_ball
            if action.startswith('add_run_'):
                runs = int(action.split('_')[-1])
                match, error = match_service.update_match_score(match, 'add_run', runs)
            elif action == 'add_wide':
                match, error = match_service.update_match_score(match, action)
            elif action == 'add_no_ball':
                match, error = match_service.update_match_score(match, action)
            
            if error:
                return JsonResponse(error, status=400)
            
            # Check for innings completion
            is_complete, response_data = match_service.check_innings_completion(match)
            if is_complete:
                return JsonResponse(response_data)
            
            # If match state requires new bowler (end of over)
            if not match.current_bowler:
                return JsonResponse({'redirect': f'/select_next_bowler/{match_id}/'})
            
            # Regular score update response
            return JsonResponse({
                'team1_runs': match.team1_runs,
                'team2_runs': match.team2_runs,
                'team1_wickets': match.team1_wickets,
                'team2_wickets': match.team2_wickets,
                'balls_bowled': match.balls_bowled,
                'is_free_hit': match.is_free_hit,
                'overs': match.overs_display,
                'striker_runs': match.striker.runs if match.striker else 0,
                'striker_balls': match.striker.balls_faced if match.striker else 0,
                'striker_name': match.striker.name if match.striker else "No striker",
                'non_striker_name': match.non_striker.name if match.non_striker else "No non-striker",
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
            
    return JsonResponse({'error': 'Invalid request method'}, status=405) 