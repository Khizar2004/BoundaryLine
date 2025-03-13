from django.shortcuts import render, redirect, get_object_or_404
from .models import Player, Match, Stat, OutPlayer
from .forms import PlayerForm, MatchForm, StartGameForm, PlayerSelectionForm, TeamSelectionForm
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
import json

# Homepage View
def home(request):
    return render(request, 'cricket/home.html')

def handle_wicket(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    current_batter = match.current_batter  # Ensure this field exists in your Match model
    
    if current_batter:
        current_batter.is_out = True
        current_batter.save()
    
        # Optionally, create an OutPlayer entry
        OutPlayer.objects.create(match=match, player=current_batter)
    
    # Redirect to the "Select Next Batter" screen
    return redirect('select_next_batter', match_id=match_id)

def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Signup successful! Please log in.")
            return redirect('login')  # Redirect to login after signup
    else:
        form = UserCreationForm()
    return render(request, 'cricket/signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            # Redirect to 'next' parameter if available, else home
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
        else:
            messages.error(request, "Invalid credentials.")
    else:
        form = AuthenticationForm()
    return render(request, 'cricket/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home')  # Redirect to homepage after logout

# List of Players
def player_list(request):
    players = Player.objects.all()  # Fetch all players from the database
    return render(request, 'cricket/player_list.html', {'players': players})

# List of Matches
@login_required
def match_list(request):
    matches = Match.objects.filter(created_by=request.user).order_by('-match_date')  # Only show user's matches
    return render(request, 'cricket/match_list.html', {'matches': matches})

def update_match(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            action = data.get('action')
            match_id = data.get('match_id')
            match = get_object_or_404(Match, id=match_id)
            
            # Check if match is already completed
            if hasattr(match, 'is_completed') and match.is_completed:
                return JsonResponse({'error': 'Match is already completed'}, status=400)

            # Get current batting and bowling teams
            batting_team = match.batting_team
            bowling_team = match.team2_name if batting_team == match.team1_name else match.team1_name
            
            # Calculate current over and balls
            total_balls_bowled = match.balls_bowled
            overs_completed = total_balls_bowled // 6
            balls_in_current_over = total_balls_bowled % 6
            
            # Check for innings completion
            if overs_completed >= match.overs_per_side:
                # If first innings is complete, check if match is complete
                if match.team1_name == batting_team:
                    # Switch innings to team 2
                    match.batting_team = match.team2_name
                    match.balls_bowled = 0
                    match.is_free_hit = False
                    match.current_bowler = None
                    match.striker = None
                    match.non_striker = None
                    match.save()
                    
                    return JsonResponse({
                        'innings_complete': True,
                        'message': f"{match.team1_name} innings complete. {match.team2_name} needs {match.team1_runs + 1} runs to win.",
                        'team1_runs': match.team1_runs,
                        'team1_wickets': match.team1_wickets,
                        'team2_runs': match.team2_runs,
                        'team2_wickets': match.team2_wickets,
                        'overs': f"{overs_completed}.{balls_in_current_over}",
                        'target': match.team1_runs + 1
                    })
                else:
                    # Both innings complete - determine winner
                    if match.team2_runs > match.team1_runs:
                        winner = match.team2_name
                        margin = f"by {10 - match.team2_wickets} wickets"
                    elif match.team1_runs > match.team2_runs:
                        winner = match.team1_name
                        margin = f"by {match.team1_runs - match.team2_runs} runs"
                    else:
                        winner = "Match Tied"
                        margin = ""
                    
                    match.winner = winner
                    match.is_completed = True
                    match.save()
                    
                    return JsonResponse({
                        'match_complete': True,
                        'winner': winner,
                        'margin': margin,
                        'team1_runs': match.team1_runs,
                        'team1_wickets': match.team1_wickets,
                        'team2_runs': match.team2_runs,
                        'team2_wickets': match.team2_wickets,
                        'overs': f"{overs_completed}.{balls_in_current_over}"
                    })
            
            # Second innings target check
            if batting_team == match.team2_name:
                # Check if target is reached
                if match.team2_runs > match.team1_runs:
                    winner = match.team2_name
                    margin = f"by {10 - match.team2_wickets} wickets"
                    
                    match.winner = winner
                    match.is_completed = True
                    match.save()
                    
                    return JsonResponse({
                        'match_complete': True,
                        'winner': winner,
                        'margin': margin,
                        'team1_runs': match.team1_runs,
                        'team1_wickets': match.team1_wickets,
                        'team2_runs': match.team2_runs,
                        'team2_wickets': match.team2_wickets,
                        'overs': f"{overs_completed}.{balls_in_current_over}"
                    })
            
            # Handle actions based on cricket rules
            if action.startswith('add_run_'):
                runs = int(action.split('_')[-1])
                
                # Update team score
                if batting_team == match.team1_name:
                    match.team1_runs += runs
                else:
                    match.team2_runs += runs
                
                # Update bowler stats if available
                if match.current_bowler:
                    match.current_bowler.runs_given = getattr(match.current_bowler, 'runs_given', 0) + runs
                    match.current_bowler.save()
                
                # Update striker's score
                match.striker.runs += runs
                match.striker.balls_faced = getattr(match.striker, 'balls_faced', 0) + 1
                match.striker.save()
                
                # Increment balls bowled (only for valid deliveries)
                match.balls_bowled += 1
                
                # Reset free hit after a valid delivery
                match.is_free_hit = False
                
                # Rotate strike for odd runs or if over completes
                if runs % 2 == 1:
                    # Swap striker and non-striker
                    match.striker, match.non_striker = match.non_striker, match.striker
                
                # Check if over is complete
                if match.balls_bowled % 6 == 0:
                    # Swap striker and non-striker at end of over
                    match.striker, match.non_striker = match.non_striker, match.striker
                    # Reset current bowler to force selection of new bowler
                    match.current_bowler = None
            
            elif action == 'add_wide':
                # Add extra run for wide
                if batting_team == match.team1_name:
                    match.team1_runs += 1
                    match.team1_wides += 1
                else:
                    match.team2_runs += 1
                    match.team2_wides += 1
                
                # Update bowler statistics
                if match.current_bowler:
                    match.current_bowler.runs_given = getattr(match.current_bowler, 'runs_given', 0) + 1
                    match.current_bowler.save()
                
                # No ball increment, no strike rotation, no free hit reset
            
            elif action == 'add_no_ball':
                # Add runs for no ball
                if batting_team == match.team1_name:
                    match.team1_runs += 1
                    match.team1_no_balls += 1
                else:
                    match.team2_runs += 1
                    match.team2_no_balls += 1
                
                # Update bowler statistics
                if match.current_bowler:
                    match.current_bowler.runs_given = getattr(match.current_bowler, 'runs_given', 0) + 1
                    match.current_bowler.save()
                
                # Set next ball as free hit
                match.is_free_hit = True
            
            elif action == 'add_wicket':
                # Check if free hit is active
                if match.is_free_hit:
                    return JsonResponse({'error': 'Wickets are disabled on a Free Hit'}, status=400)
                
                # Update team wickets
                if batting_team == match.team1_name:
                    match.team1_wickets += 1
                else:
                    match.team2_wickets += 1
                
                # Check for all out
                if (batting_team == match.team1_name and match.team1_wickets >= 10) or \
                   (batting_team == match.team2_name and match.team2_wickets >= 10):
                    # All out - innings over
                    if batting_team == match.team1_name:
                        # Switch innings to team 2
                        match.batting_team = match.team2_name
                        match.balls_bowled = 0
                        match.is_free_hit = False
                        match.current_bowler = None
                        match.striker = None
                        match.non_striker = None
                        match.save()
                        
                        return JsonResponse({
                            'innings_complete': True,
                            'all_out': True,
                            'message': f"{match.team1_name} all out. {match.team2_name} needs {match.team1_runs + 1} runs to win.",
                            'team1_runs': match.team1_runs,
                            'team1_wickets': match.team1_wickets,
                            'team2_runs': match.team2_runs,
                            'team2_wickets': match.team2_wickets,
                            'overs': f"{overs_completed}.{balls_in_current_over}",
                            'target': match.team1_runs + 1
                        })
                    else:
                        # Both innings complete - determine winner
                        if match.team2_runs > match.team1_runs:
                            winner = match.team2_name
                            margin = f"by {10 - match.team2_wickets} wickets"
                        elif match.team1_runs > match.team2_runs:
                            winner = match.team1_name
                            margin = f"by {match.team1_runs - match.team2_runs} runs"
                        else:
                            winner = "Match Tied"
                            margin = ""
                        
                        match.winner = winner
                        match.is_completed = True
                        match.save()
                        
                        return JsonResponse({
                            'match_complete': True,
                            'all_out': True,
                            'winner': winner,
                            'margin': margin,
                            'team1_runs': match.team1_runs,
                            'team1_wickets': match.team1_wickets,
                            'team2_runs': match.team2_runs,
                            'team2_wickets': match.team2_wickets,
                            'overs': f"{overs_completed}.{balls_in_current_over}"
                        })
                
                # Update bowler stats
                if match.current_bowler:
                    match.current_bowler.wickets = getattr(match.current_bowler, 'wickets', 0) + 1
                    match.current_bowler.save()
                
                # Mark striker as out
                match.striker.is_out = True
                match.striker.save()
                
                # Create record of out player
                OutPlayer.objects.create(match=match, player=match.striker)
                
                # Store out player info for response
                out_player_info = {
                    'out_player': match.striker.name,
                    'out_player_runs': match.striker.runs,
                    'out_player_balls': getattr(match.striker, 'balls_faced', 0)
                }
                
                # Increment balls bowled
                match.balls_bowled += 1
                match.balls_in_current_over += 1
                
                # Reset free hit after valid delivery
                match.is_free_hit = False
                
                # Check for remaining batters
                remaining_batters = match.batters.filter(is_out=False).exclude(id=match.non_striker.id)
                has_remaining_batters = remaining_batters.exists()
                
                # Check if over is complete
                if match.balls_bowled % 6 == 0 or match.balls_in_current_over >= 6:
                    match.balls_in_current_over = 0
                    match.current_bowler = None  # Force bowler change
                
                # Clear the striker to force selection of new batter
                match.striker = None
                
                # Save match state
                match.save()
                
                # Calculate overs display
                overs_completed = match.balls_bowled // 6
                balls_in_current_over = match.balls_bowled % 6
                overs_display = f"{overs_completed}.{balls_in_current_over}"
                
                # Prepare response with current run rate
                current_run_rate = 0
                if overs_completed > 0 or balls_in_current_over > 0:
                    total_overs = overs_completed + (balls_in_current_over / 6)
                    if batting_team == match.team1_name:
                        current_run_rate = match.team1_runs / total_overs
                    else:
                        current_run_rate = match.team2_runs / total_overs
                
                # Prepare response data
                response_data = {
                    'team1_runs': match.team1_runs,
                    'team1_wickets': match.team1_wickets,
                    'team2_runs': match.team2_runs,
                    'team2_wickets': match.team2_wickets,
                    'overs': overs_display,
                    'current_run_rate': current_run_rate,
                    'current_bowler': match.current_bowler.name if match.current_bowler else "Not Set",
                    'bowler_overs': f"{getattr(match.current_bowler, 'overs', 0)}.{getattr(match.current_bowler, 'balls', 0) % 6}" if match.current_bowler else "0.0",
                    'bowler_runs': getattr(match.current_bowler, 'runs_given', 0) if match.current_bowler else 0,
                    'bowler_wickets': getattr(match.current_bowler, 'wickets', 0) if match.current_bowler else 0,
                    'striker': match.striker.name if match.striker else "Not Set",
                    'striker_runs': match.striker.runs if match.striker else 0,
                    'striker_balls': getattr(match.striker, 'balls_faced', 0) if match.striker else 0,
                    'non_striker': match.non_striker.name if match.non_striker else "Not Set",
                    'non_striker_runs': match.non_striker.runs if match.non_striker else 0,
                    'non_striker_balls': getattr(match.non_striker, 'balls_faced', 0) if match.non_striker else 0,
                    'is_free_hit': match.is_free_hit,
                    'require_new_bowler': match.current_bowler is None,
                    'wicket': True,
                    'has_remaining_batters': has_remaining_batters,
                    **out_player_info
                }
                
                return JsonResponse(response_data)
            
            elif action == 'set_new_bowler':
                # Handle setting a new bowler
                bowler_id = data.get('bowler_id')
                new_bowler = get_object_or_404(Player, id=bowler_id)
                
                # Check if bowler was the previous over's bowler
                if match.previous_bowler and match.previous_bowler.id == new_bowler.id:
                    return JsonResponse({'error': 'The same bowler cannot bowl consecutive overs'}, status=400)
                
                match.previous_bowler = match.current_bowler
                match.current_bowler = new_bowler
                match.save()
                
                return JsonResponse({
                    'success': True,
                    'current_bowler': match.current_bowler.name
                })
            
            # Save match state
            match.save()
            
            # Calculate overs display
            overs_completed = match.balls_bowled // 6
            balls_in_current_over = match.balls_bowled % 6
            overs_display = f"{overs_completed}.{balls_in_current_over}"
            
            # Calculate current run rate
            current_run_rate = 0
            if overs_completed > 0 or balls_in_current_over > 0:
                total_overs = overs_completed + (balls_in_current_over / 6)
                if batting_team == match.team1_name:
                    current_run_rate = match.team1_runs / total_overs
                else:
                    current_run_rate = match.team2_runs / total_overs
            
            # Calculate required run rate for second innings
            required_run_rate = 0
            target = 0
            balls_remaining = 0
            
            if batting_team == match.team2_name:
                target = match.team1_runs + 1
                runs_required = target - match.team2_runs
                balls_remaining = (match.overs_per_side * 6) - match.balls_bowled
                
                if balls_remaining > 0:
                    required_run_rate = (runs_required * 6) / balls_remaining
            
            # Return updated match data
            return JsonResponse({
                'team1_runs': match.team1_runs,
                'team1_wickets': match.team1_wickets,
                'team2_runs': match.team2_runs,
                'team2_wickets': match.team2_wickets,
                'overs': overs_display,
                'current_run_rate': current_run_rate,
                'required_run_rate': required_run_rate,
                'target': target,
                'runs_required': target - match.team2_runs if batting_team == match.team2_name else 0,
                'balls_remaining': balls_remaining,
                'current_bowler': match.current_bowler.name if match.current_bowler else "Not Set",
                'bowler_overs': f"{getattr(match.current_bowler, 'overs', 0)}.{getattr(match.current_bowler, 'balls', 0) % 6}" if match.current_bowler else "0.0",
                'bowler_runs': getattr(match.current_bowler, 'runs_given', 0) if match.current_bowler else 0,
                'bowler_wickets': getattr(match.current_bowler, 'wickets', 0) if match.current_bowler else 0,
                'striker': match.striker.name if match.striker else "Not Set",
                'striker_runs': match.striker.runs if match.striker else 0,
                'striker_balls': getattr(match.striker, 'balls_faced', 0) if match.striker else 0,
                'non_striker': match.non_striker.name if match.non_striker else "Not Set",
                'non_striker_runs': match.non_striker.runs if match.non_striker else 0,
                'non_striker_balls': getattr(match.non_striker, 'balls_faced', 0) if match.non_striker else 0,
                'is_free_hit': match.is_free_hit,
                'require_new_bowler': match.current_bowler is None
            })
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
        
def set_bowler(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    bowling_team = match.team2_name if match.batting_team == match.team1_name else match.team1_name
    bowling_team_players = Player.objects.filter(team=bowling_team)

    if request.method == 'POST':
        bowler_id = request.POST.get('current_bowler')
        if bowler_id:
            try:
                bowler = Player.objects.get(id=bowler_id, team=bowling_team)
                match.current_bowler = bowler
                match.save()
                messages.success(request, "Next bowler set successfully.")
                return redirect('live_match', match_id=match.id)
            except Player.DoesNotExist:
                messages.error(request, "Selected bowler does not exist.")
        else:
            messages.error(request, "Please select a bowler.")

    return render(request, 'cricket/set_bowler.html', {
        'bowling_team_players': bowling_team_players,
    })

def get_live_match_data(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    data = {
        'team1_runs': match.team1_runs,
        'team2_runs': match.team2_runs,
        'overs': f"{match.balls_bowled // 6}.{match.balls_bowled % 6}",
        'current_bowler': match.current_bowler.name if match.current_bowler else "Not Set",
        'striker': match.striker.name if match.striker else "Not Set",
        'non_striker': match.non_striker.name if match.non_striker else "Not Set",
    }
    return JsonResponse(data)
    
def add_player(request):
    if request.method == 'POST':
        form = PlayerForm(request.POST)
        if form.is_valid():
            form.save()  # Save the new player to the database
            return redirect('add_player')  # Redirect to the same page to add more players
    else:
        form = PlayerForm()  # Initialize an empty form for GET requests
    return render(request, 'cricket/add_player.html', {'form': form})

def add_match(request):
    if request.method == 'POST':
        form = MatchForm(request.POST)
        if form.is_valid():
            form.save()  # Save the new match to the database
            return redirect('match_list')  # Redirect to the match list page
    else:
        form = MatchForm()
    return render(request, 'cricket/add_match.html', {'form': form})

def match_details(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    players_team1 = Player.objects.filter(team=match.team1_name)
    players_team2 = Player.objects.filter(team=match.team2_name)
    return render(request, 'cricket/match_details.html', {
        'match': match,
        'players_team1': players_team1,
        'players_team2': players_team2,
    })
    
def delete_match(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    if request.method == 'POST':  # Confirm deletion
        match.delete()
        messages.success(request, "Match deleted successfully!")
        return redirect('match_list')
    return render(request, 'cricket/delete_match.html', {'match': match})

def delete_all_matches(request):
    if request.method == 'POST':
        Match.objects.all().delete()
        if not request.session.get('delete_all_message_shown', False):  # Prevent duplicate
            messages.success(request, "All matches have been deleted!")
            request.session['delete_all_message_shown'] = True  # Track message
        return redirect('match_list')
    return render(request, 'cricket/delete_all_matches.html')

def clear_message_flag(request):
    if request.method == 'POST':
        # Clear all session-based message flags or specific ones
        if 'delete_all_message_shown' in request.session:
            del request.session['delete_all_message_shown']
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'failed', 'reason': 'Invalid method'}, status=405)

@login_required
def start_game(request):
    if request.method == 'POST':
        match_form = StartGameForm(request.POST)
        team_form = TeamSelectionForm(request.POST)
        if match_form.is_valid() and team_form.is_valid():
            with transaction.atomic():
                match = match_form.save(commit=False)
                match.batting_team = match.team1_name  # Set the initial batting team
                match.created_by = request.user  # Assign the currently logged-in user as the creator
                match.save()
                
                # Assign players to teams
                team1_players = team_form.cleaned_data['team1_players']
                team2_players = team_form.cleaned_data['team2_players']
                
                # Assign Team 1 Players
                for player in team1_players:
                    player.team = match.team1_name
                    player.runs = 0  # Reset runs
                    player.is_out = False  # Reset out status
                    player.save()
                
                # Assign Team 2 Players
                for player in team2_players:
                    player.team = match.team2_name
                    player.runs = 0  # Reset runs
                    player.is_out = False  # Reset out status
                    player.save()
                
                # Initialize match-related fields
                match.balls_bowled = 0
                match.balls_in_current_over = 0
                match.team1_runs = 0
                match.team2_runs = 0
                match.team1_wickets = 0
                match.team2_wickets = 0
                match.is_free_hit = False
                match.winner = None  # Reset winner
                match.save()

            messages.success(request, "Game started successfully!")
            return redirect('live_match', match_id=match.id)
        else:
            # Debugging: Print form errors to console
            print("Match Form Errors:", match_form.errors)
            print("Team Form Errors:", team_form.errors)

            messages.error(request, "There were errors in the form. Please correct them and try again.")
    else:
        match_form = StartGameForm()
        team_form = TeamSelectionForm()
    
    return render(request, 'cricket/start_game.html', {
        'match_form': match_form,
        'team_form': team_form,
    })

# def set_openers(request):
#     if request.method == 'POST':
#         striker = request.POST.get('striker')
#         non_striker = request.POST.get('non_striker')

#         # Validate and save the data
#         if striker != non_striker:
#             game = Game.objects.get(id=request.session['game_id'])
#             game.striker = striker
#             game.non_striker = non_striker
#             game.save()

#             # Redirect to the next step in the game setup
#             return redirect('next_step_url')  # Replace with the appropriate view name

#         else:
#             messages.error(request, "Striker and Non-Striker cannot be the same.")
    
#     # Render the same form if GET or invalid submission
#     players = Player.objects.all()
#     return render(request, 'set_openers.html', {'players': players})

# cricket/views.py

def select_next_bowler(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    bowling_team = match.team2_name if match.batting_team == match.team1_name else match.team1_name
    bowling_team_players = Player.objects.filter(team=bowling_team)

    if request.method == 'POST':
        bowler_id = request.POST.get('current_bowler')
        if bowler_id:
            try:
                bowler = Player.objects.get(id=bowler_id, team=bowling_team)
                match.current_bowler = bowler
                match.save()
                messages.success(request, "Next bowler set successfully.")
                return redirect('live_match', match_id=match.id)
            except Player.DoesNotExist:
                messages.error(request, "Selected bowler does not exist.")
        else:
            messages.error(request, "Please select a bowler.")

    return render(request, 'cricket/set_bowler.html', {
        'bowling_team_players': bowling_team_players,
    })


def select_next_batter(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    remaining_batters = match.batters.filter(is_out=False).exclude(id=match.non_striker.id if match.non_striker else None)
    
    if not remaining_batters.exists():
        messages.error(request, "No remaining batters available!")
        return redirect('live_match', match_id=match.id)
    
    if request.method == 'POST':
        batter_id = request.POST.get('batter_id')
        if batter_id:
            try:
                next_batter = get_object_or_404(Player, id=batter_id)
                # Check that the selected batter is not already the non-striker
                if match.non_striker and next_batter.id == match.non_striker.id:
                    messages.error(request, "Cannot select non-striker as the new batter.")
                    return redirect('select_next_batter', match_id=match.id)
                
                # Update the match with the new striker
                match.striker = next_batter
                match.save()
                
                messages.success(request, f"{next_batter.name} is now batting.")
                return redirect('live_match', match_id=match.id)
            except Player.DoesNotExist:
                messages.error(request, "Selected player not found.")
        else:
            messages.error(request, "Please select a batter.")
    
    context = {
        'match': match,
        'remaining_batters': remaining_batters
    }
    return render(request, 'cricket/select_next_batter.html', context)
    
def live_match(request, match_id):
    # Retrieve the match object or return 404 if not found
    match = get_object_or_404(
        Match.objects.select_related('current_bowler', 'striker', 'non_striker'),
        id=match_id
    )

    # Determine the bowling team based on the batting team
    bowling_team = match.team2_name if match.batting_team == match.team1_name else match.team1_name

    # Fetch players for both teams
    bowling_team_players = Player.objects.filter(team=bowling_team)
    batting_team_players = Player.objects.filter(team=match.batting_team)

    # Calculate team sizes and maximum wickets
    team1_size = Player.objects.filter(team=match.team1_name).count()
    team2_size = Player.objects.filter(team=match.team2_name).count()
    max_wickets_team1 = team1_size - 1
    max_wickets_team2 = team2_size - 1

    # -----------------------------
    # Step 1: Set Openers
    # -----------------------------
    if not match.striker or not match.non_striker:
        if request.method == 'POST' and request.POST.get('form_type') == 'set_openers':
            striker_id = request.POST.get('striker')
            non_striker_id = request.POST.get('non_striker')
            if striker_id and non_striker_id:
                try:
                    striker = Player.objects.get(id=striker_id, team=match.batting_team)
                    non_striker = Player.objects.get(id=non_striker_id, team=match.batting_team)
                    if striker == non_striker:
                        messages.error(request, "Striker and Non-Striker cannot be the same player.")
                    else:
                        match.striker = striker
                        match.non_striker = non_striker
                        match.save()
                        messages.success(request, "Openers set successfully.")
                        return redirect('live_match', match_id=match.id)
                except Player.DoesNotExist:
                    messages.error(request, "Selected player does not exist in the batting team.")
            else:
                messages.error(request, "Please select both openers.")
        # Render the set_openers form
        return render(request, 'cricket/set_openers.html', {
            'batting_team_players': batting_team_players,
        })

    # -----------------------------
    # Step 2: Set Opening Bowler
    # -----------------------------
    if not match.current_bowler and match.balls_bowled == 0:
        if request.method == 'POST' and request.POST.get('form_type') == 'set_bowler':
            bowler_id = request.POST.get('current_bowler')
            if bowler_id:
                try:
                    bowler = Player.objects.get(id=bowler_id, team=bowling_team)
                    match.current_bowler = bowler
                    match.save()
                    messages.success(request, "Opening bowler set successfully.")
                    return redirect('live_match', match_id=match.id)
                except Player.DoesNotExist:
                    messages.error(request, "Selected bowler does not exist in the bowling team.")
            else:
                messages.error(request, "Please select a bowler.")
        # Render the set_bowler form
        return render(request, 'cricket/set_bowler.html', {
            'bowling_team_players': bowling_team_players,
        })

    # -----------------------------
    # Step 3: Handle Match Updates
    # -----------------------------
    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'update_match':
            action = request.POST.get('action')

            # Handle Adding Runs
            if action and action.startswith('add_run_'):
                try:
                    run_value = int(action.split('_')[-1])
                except ValueError:
                    messages.error(request, "Invalid run value.")
                    return redirect('live_match', match_id=match.id)

                # Update team runs based on batting team
                if match.batting_team == match.team1_name:
                    match.team1_runs += run_value
                else:
                    match.team2_runs += run_value

                # Update striker's runs
                if match.striker:
                    match.striker.runs += run_value
                    match.striker.save()  # Ensure the striker's runs are saved

                # Handle strike rotation on odd runs
                if run_value % 2 == 1 and match.striker and match.non_striker:
                    match.striker, match.non_striker = match.non_striker, match.striker

                # Increment balls bowled and in current over
                match.balls_bowled += 1
                match.balls_in_current_over += 1

                match.save()  # Save the updated match state
                messages.success(request, f"Added {run_value} runs.")
                return redirect('live_match', match_id=match.id)

            # Handle Adding Wide
            elif action == 'add_wide':
                # Update team runs based on batting team
                if match.batting_team == match.team1_name:
                    match.team1_runs += 1
                else:
                    match.team2_runs += 1

                match.save()
                messages.success(request, "Added 1 Wide.")
                return redirect('live_match', match_id=match.id)

            # Handle Adding No Ball
            elif action == 'add_no_ball':
                # Update team runs based on batting team
                if match.batting_team == match.team1_name:
                    match.team1_runs += 1
                else:
                    match.team2_runs += 1

                match.is_free_hit = True
                match.save()
                messages.success(request, "Added 1 No Ball. Next delivery is a Free Hit.")
                return redirect('live_match', match_id=match.id)

            # Handle Adding Wicket
            elif action == 'add_wicket':
                if match.is_free_hit:
                    messages.error(request, "Wickets are disabled during a Free Hit!")
                    return redirect('live_match', match_id=match.id)

                # Update wickets based on the batting team
                if match.batting_team == match.team1_name:
                    if match.team1_wickets < max_wickets_team1:
                        match.team1_wickets += 1
                    else:
                        messages.error(request, "Maximum wickets reached for Team 1.")
                        return redirect('live_match', match_id=match.id)
                else:
                    if match.team2_wickets < max_wickets_team2:
                        match.team2_wickets += 1
                    else:
                        messages.error(request, "Maximum wickets reached for Team 2.")
                        return redirect('live_match', match_id=match.id)

                # Mark the striker as out
                OutPlayer.objects.create(match=match, player=match.striker)
                match.striker.is_out = True
                match.striker.save()

                # Increment balls bowled and in current over
                match.balls_bowled += 1
                match.balls_in_current_over += 1

                # Redirect to select next batter
                remaining_batters = batting_team_players.exclude(
                    id__in=OutPlayer.objects.filter(match=match).values_list('player_id', flat=True)
                ).exclude(id=match.striker.id)

                if remaining_batters.exists():
                    messages.info(request, "Wicket taken! Please select the next batsman.")
                    return redirect('select_next_batter', match_id=match.id)
                else:
                    messages.info(request, "All batters are out. Innings completed.")
                    match.batting_team = None
                    match.save()

                return redirect('live_match', match_id=match.id)

            else:
                messages.error(request, "Invalid action.")
                return redirect('live_match', match_id=match.id)

        elif form_type == 'select_next_bowler':
            # Handle bowler selection (existing logic)
            next_bowler_id = request.POST.get('next_bowler')
            if next_bowler_id:
                try:
                    next_bowler = Player.objects.get(id=next_bowler_id, team=bowling_team)
                    if next_bowler != match.current_bowler:
                        match.current_bowler = next_bowler
                        match.save()
                        messages.success(request, "Next bowler set successfully.")
                        return redirect('live_match', match_id=match.id)
                    else:
                        messages.error(request, "Cannot select the same bowler consecutively.")
                except Player.DoesNotExist:
                    messages.error(request, "Selected bowler does not exist.")
            else:
                messages.error(request, "You must select a new bowler to continue.")
                return render(request, 'cricket/live_match.html', {
                    'match': match,
                    'overs_display': f"{match.balls_bowled // 6}.{match.balls_bowled % 6}",
                    'bowling_team_players': bowling_team_players,
                    'select_next_bowler': True,
                })

        elif form_type == 'select_next_batter':
            # Handle batsman selection
            next_batter_id = request.POST.get('next_batter')
            if next_batter_id:
                try:
                    next_batter = Player.objects.get(id=next_batter_id, team=match.batting_team)
                    # Check if the selected batter is already out
                    if OutPlayer.objects.filter(match=match, player=next_batter).exists():
                        messages.error(request, "Selected batsman is already out.")
                    else:
                        match.striker = next_batter
                        match.save()
                        messages.success(request, "Next batsman set successfully.")
                        return redirect('live_match', match_id=match.id)
                except Player.DoesNotExist:
                    messages.error(request, "Selected batsman does not exist.")
            else:
                messages.error(request, "Please select a batsman.")
            context = {
                'match': match,
                'select_next_batter': True,
            }
            return render(request, 'cricket/live_match.html', context)

    # Check for over completion after update
    if match.balls_in_current_over >= 6:
        match.balls_in_current_over = 0
        match.current_bowler = None  # Force bowler selection for the next over
        match.save()
        messages.info(request, "Over completed. Please select a new bowler.")
        return redirect('select_next_bowler', match_id=match.id)

    # Check for End of Innings or Match
    if (match.balls_bowled >= match.overs_per_side * 6) or \
       (match.batting_team == match.team1_name and match.team1_wickets >= max_wickets_team1) or \
       (match.batting_team == match.team2_name and match.team2_wickets >= max_wickets_team2):

        if match.batting_team == match.team1_name:
            match.batting_team = match.team2_name
            match.balls_bowled = 0
            match.balls_in_current_over = 0
            # Initialize new innings batters
            new_batters = batting_team_players[:2]
            if len(new_batters) >= 2:
                match.striker, match.non_striker = new_batters[:2]
            elif len(new_batters) == 1:
                match.striker = new_batters[0]
                match.non_striker = None
            # Assign initial bowler for the new innings
            if bowling_team_players.exists():
                match.current_bowler = bowling_team_players.first()
            else:
                match.current_bowler = None
        else:
            # Match ends; determine the winner
            if match.team1_runs > match.team2_runs:
                match.winner = match.team1_name
                messages.success(request, f"{match.team1_name} wins!")
            elif match.team2_runs > match.team1_runs:
                match.winner = match.team2_name
                messages.success(request, f"{match.team2_name} wins!")
            else:
                messages.info(request, "It's a tie!")

        match.save()

    # Calculate overs after all updates
    total_balls = match.balls_bowled
    overs = total_balls // 6
    remaining_balls = total_balls % 6
    overs_display = f"{overs}.{remaining_balls}"
    
    # Calculate progress percentage for the progress bar
    total_overs_decimal = overs + (remaining_balls / 6)
    progress_percentage = min(100, round((total_overs_decimal / match.overs_per_side) * 100))

    # Prepare context for GET requests and after POST redirects
    context = {
        'match': match,
        'overs_display': overs_display,
        'bowling_team_players': bowling_team_players,
        'batting_team_players': batting_team_players,
        'out_players': OutPlayer.objects.filter(match=match),
        'runs_options': [1, 2, 3, 4, 6],  # Removed 0 as runs button not present
        'max_wickets_team1': max_wickets_team1,
        'max_wickets_team2': max_wickets_team2,
        'progress_percentage': progress_percentage,
    }

    # Check if bowler selection is needed
    if not match.current_bowler and match.balls_bowled > 0:
        context['select_next_bowler'] = True

    return render(request, 'cricket/live_match.html', context)