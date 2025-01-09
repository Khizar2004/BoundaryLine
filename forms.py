from django import forms
from .models import Player, Match

class PlayerForm(forms.ModelForm):
    class Meta:
        model = Player
        fields = ['name', 'team', 'runs', 'wickets']  # Ensure all relevant fields are listed

class MatchForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = ['match_date', 'location', 'team1_name', 'team2_name', 'overs_per_side']
        widgets = {
            'team1_name': forms.TextInput(attrs={'class': 'form-control'}),
            'team2_name': forms.TextInput(attrs={'class': 'form-control'}),
            'match_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'overs_per_side': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class StartGameForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = ['team1_name', 'team2_name', 'match_date', 'overs_per_side']
        widgets = {
            'team1_name': forms.TextInput(attrs={'class': 'form-control'}),
            'team2_name': forms.TextInput(attrs={'class': 'form-control'}),
            'match_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'overs_per_side': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class PlayerSelectionForm(forms.Form):
    bowler = forms.ModelChoiceField(queryset=Player.objects.all(), required=True, label="Select Bowler")
    striker = forms.ModelChoiceField(queryset=Player.objects.all(), required=True, label="Select Striker")
    non_striker = forms.ModelChoiceField(queryset=Player.objects.all(), required=True, label="Select Non-Striker")

class TeamSelectionForm(forms.Form):
    team1_players = forms.ModelMultipleChoiceField(
        queryset=Player.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-select'})
    )
    team2_players = forms.ModelMultipleChoiceField(
        queryset=Player.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-select'})
    )

    def clean_team1_players(self):
        team1 = self.cleaned_data.get('team1_players')
        if team1 and team1.count() < 2:
            raise forms.ValidationError("At least 2 players must be selected for Team 1.")
        return team1

    def clean_team2_players(self):
        team2 = self.cleaned_data.get('team2_players')
        if team2 and team2.count() < 2:
            raise forms.ValidationError("At least 2 players must be selected for Team 2.")
        return team2

    def clean(self):
        cleaned_data = super().clean()
        team1 = cleaned_data.get('team1_players')
        team2 = cleaned_data.get('team2_players')

        if team1 and team2:
            overlapping_players = set(team1) & set(team2)
            if overlapping_players:
                self.add_error('team1_players', "Players cannot be selected for both teams.")
                self.add_error('team2_players', "Players cannot be selected for both teams.")