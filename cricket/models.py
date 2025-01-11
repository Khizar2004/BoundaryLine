from django.db import models
from django.contrib.auth.models import User

# Model for Players
class Player(models.Model):
    name = models.CharField(max_length=100)
    team = models.CharField(max_length=100, null=True, blank=True)
    runs = models.IntegerField(default=0)
    wickets = models.IntegerField(default=0)
    is_out = models.BooleanField(default=False)  # New field to track player status

    def __str__(self):
        return self.name

# models.py
class Match(models.Model):
    team1_name = models.CharField(max_length=50, default="Team 1")
    team2_name = models.CharField(max_length=50, default="Team 2")
    match_date = models.DateField()
    location = models.CharField(max_length=100)
    overs_per_side = models.IntegerField(default=6)
    team1_wides = models.IntegerField(default=0)
    team2_wides = models.IntegerField(default=0)
    team1_no_balls = models.IntegerField(default=0)
    team2_no_balls = models.IntegerField(default=0)
    is_free_hit = models.BooleanField(default=False)  # Track ifcn the next ball is a free hit
    current_bowler = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True, related_name="current_bowler")
    striker = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True, related_name="striker")
    non_striker = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True, related_name="non_striker")

    # Tracking fields
    team1_runs = models.IntegerField(default=0)
    team2_runs = models.IntegerField(default=0)
    team1_wickets = models.IntegerField(default=0)
    team2_wickets = models.IntegerField(default=0)
    balls_bowled = models.IntegerField(default=0)
    balls_in_current_over = models.IntegerField(default=0)  # New Field
    batting_team = models.CharField(max_length=100, null=True, blank=True)  # Batting team
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='matches')

    def __str__(self):
        return f"{self.team1} vs {self.team2} on {self.match_date}"

    def get_bowling_team(self):
        """Returns the name of the bowling team."""
        return self.team2 if self.batting_team == self.team1 else self.team1

    def get_bowling_team_players(self):
        """Returns players of the bowling team."""
        bowling_team = self.get_bowling_team()
        return Player.objects.filter(team=bowling_team)
    
# models.py
class OutPlayer(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='out_players')
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    out_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.player.name} out in {self.match}"
    
# Model for Stats (e.g., wides, no-balls)
class Stat(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    wides = models.IntegerField(default=0)
    no_balls = models.IntegerField(default=0)

    def __str__(self):
        return f"Stats for {self.player.name} in {self.match}"