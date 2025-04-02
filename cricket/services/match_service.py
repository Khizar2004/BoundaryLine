from django.shortcuts import get_object_or_404
from cricket.models import Match, Player, OutPlayer
from django.http import JsonResponse
from django.db import transaction

def get_match_by_id(match_id):
    """Retrieve a match by its ID or return 404 if not found."""
    return get_object_or_404(Match, id=match_id)

def update_match_score(match, action, runs=0):
    """
    Update match score based on action.
    
    Args:
        match: Match object to update
        action: String action type (add_run, add_wide, add_no_ball, add_wicket)
        runs: Number of runs to add (for add_run action)
    
    Returns:
        Updated match object
    """
    batting_team = match.batting_team
    
    if action == 'add_run':
        # Update team score
        if batting_team == match.team1_name:
            match.team1_runs += runs
        else:
            match.team2_runs += runs
        
        # Update bowler stats if available
        if match.current_bowler:
            match.current_bowler.runs_given += runs
            match.current_bowler.save()
        
        # Update striker's score
        match.striker.runs += runs
        match.striker.balls_faced += 1
        match.striker.save()
        
        # Increment balls bowled (only for valid deliveries)
        match.balls_bowled += 1
        
        # Reset free hit after a valid delivery
        match.is_free_hit = False
        
        # Rotate strike for odd runs
        if runs % 2 == 1:
            # Swap striker and non-striker
            match.striker, match.non_striker = match.non_striker, match.striker
        
        # End of over handling
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
            match.current_bowler.runs_given += 1
            match.current_bowler.save()
    
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
            match.current_bowler.runs_given += 1
            match.current_bowler.save()
        
        # Set next ball as free hit
        match.is_free_hit = True
    
    elif action == 'add_wicket':
        # Check if free hit is active
        if match.is_free_hit:
            return None, {'error': 'Wickets are disabled on a Free Hit'}
        
        # Update team wickets
        if batting_team == match.team1_name:
            match.team1_wickets += 1
        else:
            match.team2_wickets += 1
        
        # Update batter as out
        if match.striker:
            match.striker.is_out = True
            match.striker.save()
            
            # Create OutPlayer record
            OutPlayer.objects.create(
                match=match,
                player=match.striker,
                runs_scored=match.striker.runs,
                balls_faced=match.striker.balls_faced
            )
            
            # Reset striker (will be chosen in next view)
            match.striker = None
        
        # Increment balls bowled
        match.balls_bowled += 1
        
        # Reset free hit
        match.is_free_hit = False
        
        # End of over handling
        if match.balls_bowled % 6 == 0:
            # Only swap if non-striker exists
            if match.non_striker:
                match.striker = match.non_striker
                match.non_striker = None
            # Reset current bowler
            match.current_bowler = None
    
    match.save()
    return match, None  # Return updated match and no error

def check_innings_completion(match):
    """
    Check if the current innings is complete.
    
    Args:
        match: Match object to check
    
    Returns:
        (is_complete, data) tuple where:
            is_complete: Boolean indicating if innings is complete
            data: Dictionary with response data for the client
    """
    batting_team = match.batting_team
    bowling_team = match.get_bowling_team()
    
    # Calculate current over and balls
    overs_completed = match.balls_bowled // 6
    balls_in_current_over = match.balls_in_current_over
    
    # Check for all out
    if (batting_team == match.team1_name and match.team1_wickets >= 10) or \
       (batting_team == match.team2_name and match.team2_wickets >= 10):
        # All out - innings over
        if batting_team == match.team1_name:
            # Switch innings to team 2
            with transaction.atomic():
                match.batting_team = match.team2_name
                match.balls_bowled = 0
                match.is_free_hit = False
                match.current_bowler = None
                match.striker = None
                match.non_striker = None
                match.save()
            
            return True, {
                'innings_complete': True,
                'message': f"{match.team1_name} all out for {match.team1_runs}. {match.team2_name} needs {match.team1_runs + 1} runs to win.",
                'team1_runs': match.team1_runs,
                'team1_wickets': match.team1_wickets,
                'team2_runs': match.team2_runs,
                'team2_wickets': match.team2_wickets,
                'overs': f"{overs_completed}.{balls_in_current_over}",
                'target': match.team1_runs + 1
            }
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
            
            with transaction.atomic():
                match.winner = winner
                match.is_completed = True
                match.save()
            
            return True, {
                'match_complete': True,
                'winner': winner,
                'margin': margin,
                'team1_runs': match.team1_runs,
                'team1_wickets': match.team1_wickets,
                'team2_runs': match.team2_runs,
                'team2_wickets': match.team2_wickets,
                'overs': f"{overs_completed}.{balls_in_current_over}"
            }
    
    # Check for overs completion
    if overs_completed >= match.overs_per_side:
        # If first innings is complete, check if match is complete
        if match.team1_name == batting_team:
            # Switch innings to team 2
            with transaction.atomic():
                match.batting_team = match.team2_name
                match.balls_bowled = 0
                match.is_free_hit = False
                match.current_bowler = None
                match.striker = None
                match.non_striker = None
                match.save()
            
            return True, {
                'innings_complete': True,
                'message': f"{match.team1_name} innings complete. {match.team2_name} needs {match.team1_runs + 1} runs to win.",
                'team1_runs': match.team1_runs,
                'team1_wickets': match.team1_wickets,
                'team2_runs': match.team2_runs,
                'team2_wickets': match.team2_wickets,
                'overs': f"{overs_completed}.{balls_in_current_over}",
                'target': match.team1_runs + 1
            }
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
            
            with transaction.atomic():
                match.winner = winner
                match.is_completed = True
                match.save()
            
            return True, {
                'match_complete': True,
                'winner': winner,
                'margin': margin,
                'team1_runs': match.team1_runs,
                'team1_wickets': match.team1_wickets,
                'team2_runs': match.team2_runs,
                'team2_wickets': match.team2_wickets,
                'overs': f"{overs_completed}.{balls_in_current_over}"
            }
    
    # Second innings target check
    if batting_team == match.team2_name:
        # Check if target is reached
        if match.team2_runs > match.team1_runs:
            winner = match.team2_name
            margin = f"by {10 - match.team2_wickets} wickets"
            
            with transaction.atomic():
                match.winner = winner
                match.is_completed = True
                match.save()
            
            return True, {
                'match_complete': True,
                'winner': winner,
                'margin': margin,
                'team1_runs': match.team1_runs,
                'team1_wickets': match.team1_wickets,
                'team2_runs': match.team2_runs,
                'team2_wickets': match.team2_wickets,
                'overs': f"{overs_completed}.{balls_in_current_over}"
            }
    
    # If we get here, innings is not complete
    return False, {} 