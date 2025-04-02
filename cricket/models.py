from django.db import models
from django.contrib.auth.models import User

# Model for Players
class Player(models.Model):
    name = models.CharField(max_length=100)
    team = models.CharField(max_length=100, null=True, blank=True)
    runs = models.IntegerField(default=0)
    wickets = models.IntegerField(default=0)
    is_out = models.BooleanField(default=False)
    # Additional statistics
    balls_faced = models.IntegerField(default=0)
    fours_hit = models.IntegerField(default=0)
    sixes_hit = models.IntegerField(default=0)
    runs_given = models.IntegerField(default=0)  # Runs given as bowler
    overs_bowled = models.FloatField(default=0.0)  # Overs bowled

    def __str__(self):
        return self.name
    
    @property
    def strike_rate(self):
        """Calculate batting strike rate"""
        if self.balls_faced > 0:
            return (self.runs / self.balls_faced) * 100
        return 0.0
    
    @property
    def economy(self):
        """Calculate bowling economy rate"""
        if self.overs_bowled > 0:
            return self.runs_given / self.overs_bowled
        return 0.0

# Match model
class Match(models.Model):
    team1_name = models.CharField(max_length=50, default="Team 1")
    team2_name = models.CharField(max_length=50, default="Team 2")
    match_date = models.DateField()
    location = models.CharField(max_length=100)
    overs_per_side = models.IntegerField(default=6)
    
    # Extras tracking
    team1_wides = models.IntegerField(default=0)
    team2_wides = models.IntegerField(default=0)
    team1_no_balls = models.IntegerField(default=0)
    team2_no_balls = models.IntegerField(default=0)
    
    # Ball status
    is_free_hit = models.BooleanField(default=False)  # Track if the next ball is a free hit
    
    # Players on field
    current_bowler = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True, related_name="current_bowler")
    previous_bowler = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True, related_name="previous_bowler")
    striker = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True, related_name="striker")
    non_striker = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True, related_name="non_striker")

    # Match progress tracking
    team1_runs = models.IntegerField(default=0)
    team2_runs = models.IntegerField(default=0)
    team1_wickets = models.IntegerField(default=0)
    team2_wickets = models.IntegerField(default=0)
    balls_bowled = models.IntegerField(default=0)
    batting_team = models.CharField(max_length=100, null=True, blank=True)  # Current batting team
    
    # Match status
    is_completed = models.BooleanField(default=False)
    winner = models.CharField(max_length=100, null=True, blank=True)
    
    # Relations
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='matches')
    batters = models.ManyToManyField(Player, related_name='batting_matches', blank=True)
    bowlers = models.ManyToManyField(Player, related_name='bowling_matches', blank=True)

    def __str__(self):
        return f"{self.team1_name} vs {self.team2_name} on {self.match_date}"

    def get_bowling_team(self):
        """Returns the name of the bowling team."""
        return self.team2_name if self.batting_team == self.team1_name else self.team1_name

    def get_bowling_team_players(self):
        """Returns players of the bowling team."""
        bowling_team = self.get_bowling_team()
        return Player.objects.filter(team=bowling_team)
    
    @property
    def balls_in_current_over(self):
        """Get the number of balls in the current over."""
        return self.balls_bowled % 6
    
    @property
    def current_run_rate(self):
        """Calculate current run rate for the batting team"""
        overs_completed = self.balls_bowled // 6
        balls_in_current_over = self.balls_in_current_over
        
        if overs_completed > 0 or balls_in_current_over > 0:
            total_overs = overs_completed + (balls_in_current_over / 6)
            if self.batting_team == self.team1_name:
                return self.team1_runs / total_overs
            else:
                return self.team2_runs / total_overs
        return 0.0
    
    @property
    def required_run_rate(self):
        """Calculate required run rate for the second innings"""
        if self.batting_team != self.team2_name:
            return 0.0
            
        target = self.team1_runs + 1
        runs_required = target - self.team2_runs
        balls_remaining = (self.overs_per_side * 6) - self.balls_bowled
        
        if balls_remaining > 0:
            return (runs_required * 6) / balls_remaining
        return 0.0
    
    @property
    def overs_display(self):
        """Return overs in the format of X.Y"""
        overs_completed = self.balls_bowled // 6
        balls_in_current_over = self.balls_in_current_over
        return f"{overs_completed}.{balls_in_current_over}"
    
# Record of out players
class OutPlayer(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='out_players')
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    out_at = models.DateTimeField(auto_now_add=True)
    runs_scored = models.IntegerField(default=0)
    balls_faced = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.player.name} out in {self.match}"
    
# Model for tracking detailed stats
class Stat(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    
    # Batting stats
    runs_scored = models.IntegerField(default=0)
    balls_faced = models.IntegerField(default=0)
    fours_hit = models.IntegerField(default=0)
    sixes_hit = models.IntegerField(default=0)
    
    # Bowling stats
    overs_bowled = models.FloatField(default=0.0)
    runs_given = models.IntegerField(default=0)
    wickets_taken = models.IntegerField(default=0)
    wides = models.IntegerField(default=0)
    no_balls = models.IntegerField(default=0)
    
    # Fielding stats
    catches = models.IntegerField(default=0)
    run_outs = models.IntegerField(default=0)
    
    def __str__(self):
        return f"Stats for {self.player.name} in {self.match}"
        
    @property
    def strike_rate(self):
        """Calculate batting strike rate"""
        if self.balls_faced > 0:
            return (self.runs_scored / self.balls_faced) * 100
        return 0.0
    
    @property
    def economy(self):
        """Calculate bowling economy rate"""
        if self.overs_bowled > 0:
            return self.runs_given / self.overs_bowled
        return 0.0