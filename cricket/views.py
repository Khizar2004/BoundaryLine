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
            return redirect('home')  # Redirect to homepage on successful login
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

            # Calculate overs bowled
            total_overs_bowled = match.balls_bowled // 6
            if total_overs_bowled >= match.overs_per_side:
                return JsonResponse({'error': 'Maximum overs reached. No further updates allowed.'}, status=400)

            # Handle actions
            if action.startswith('add_run_'):
                runs = int(action.split('_')[-1])
                if match.batting_team == match.team1_name:
                    match.team1_runs += runs
                else:
                    match.team2_runs += runs

                # Update striker's score
                match.striker.runs += runs
                match.striker.save()

                # Rotate strike for odd runs
                if runs % 2 == 1:
                    match.striker, match.non_striker = match.non_striker, match.striker

                # Increment balls bowled
                match.balls_bowled += 1

            elif action == 'add_wide':
                # Add runs without incrementing balls
                if match.batting_team == match.team1_name:
                    match.team1_runs += 1
                else:
                    match.team2_runs += 1

            elif action == 'add_no_ball':
                # Add runs and set free hit
                if match.batting_team == match.team1_name:
                    match.team1_runs += 1
                else:
                    match.team2_runs += 1
                match.is_free_hit = True

            elif action == 'add_wicket':
                # Wickets disabled on free hits
                if match.is_free_hit:
                    return JsonResponse({'error': 'Wickets are disabled on a Free Hit'}, status=400)

                # Increment wickets based on the batting team
                if match.batting_team == match.team1_name:
                    match.team1_wickets += 1
                else:
                    match.team2_wickets += 1

                # Mark striker as out
                match.striker.is_out = True
                match.striker.save()

                # Optionally, create an OutPlayer entry for record-keeping
                OutPlayer.objects.create(match=match, player=match.striker)

                # Increment balls bowled
                match.balls_bowled += 1

                # Reset free hit if it was active
                if match.is_free_hit:
                    match.is_free_hit = False

                # Check for remaining batters
                remaining_batters = match.batters.filter(is_out=False).exclude(id=match.striker.id)
                has_remaining_batters = remaining_batters.exists()

                # Handle over completion
                if match.balls_bowled % 6 == 0:
                    match.current_bowler = None  # Force bowler change
                    match.striker, match.non_striker = match.non_striker, match.striker

                # Save the match state before responding
                match.save()

                # Calculate overs
                balls_bowled = match.balls_bowled
                overs = balls_bowled // 6 + (balls_bowled % 6) / 10

                # Prepare the response data with additional flags
                response_data = {
                    'team1_runs': match.team1_runs,
                    'team1_wickets': match.team1_wickets,
                    'team2_runs': match.team2_runs,
                    'team2_wickets': match.team2_wickets,
                    'overs': overs,
                    'current_bowler': match.current_bowler.name if match.current_bowler else "Not Set",
                    'striker': match.striker.name if match.striker else "Not Set",
                    'striker_runs': match.striker.runs if match.striker else 0,
                    'non_striker': match.non_striker.name if match.non_striker else "Not Set",
                    'non_striker_runs': match.non_striker.runs if match.non_striker else 0,
                    'is_free_hit': match.is_free_hit,
                    'require_new_bowler': match.current_bowler is None,
                    'wicket': True,  # Flag to indicate a wicket has fallen
                    'has_remaining_batters': has_remaining_batters,  # Flag to indicate if new batters are available
                }

                return JsonResponse(response_data)

            elif action == 'set_new_bowler':
                # Handle setting a new bowler
                bowler_id = data.get('bowler_id')
                new_bowler = get_object_or_404(Player, id=bowler_id)
                match.current_bowler = new_bowler
                match.save()
                return JsonResponse({'success': True, 'current_bowler': match.current_bowler.name})

            # Reset free hit after valid delivery
            if action != 'add_no_ball':
                match.is_free_hit = False

            # Handle over completion
            if match.balls_bowled % 6 == 0:
                match.current_bowler = None  # Force bowler change
                match.striker, match.non_striker = match.non_striker, match.striker

            # Save match state
            match.save()
            
            balls_bowled = match.balls_bowled
            overs = balls_bowled // 6 + (balls_bowled % 6) / 10

            # Return updated match data
            return JsonResponse({
                'team1_runs': match.team1_runs,
                'team1_wickets': match.team1_wickets,  # Corrected
                'team2_runs': match.team2_runs,
                'team2_wickets': match.team2_wickets,  # Corrected
                'overs': overs,
                'current_bowler': match.current_bowler.name if match.current_bowler else "Not Set",
                'striker': match.striker.name if match.striker else "Not Set",
                'striker_runs': match.striker.runs if match.striker else 0,
                'non_striker': match.non_striker.name if match.non_striker else "Not Set",
                'non_striker_runs': match.non_striker.runs if match.non_striker else 0,
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
    remaining_batters = match.batters.filter(is_out=False)
    
    if request.method == 'POST':
        batter_id = request.POST['batter_id']
        next_batter = match.batters.get(id=batter_id)
        match.current_batter = next_batter
        match.save()
        return redirect('live_match', match_id=match.id)
    
    context = {
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
    }

    # Check if bowler selection is needed
    if not match.current_bowler and match.balls_bowled > 0:
        context['select_next_bowler'] = True

    return render(request, 'cricket/live_match.html', context)