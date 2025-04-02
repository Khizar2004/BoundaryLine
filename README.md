# BoundaryLine 🏏

A simple yet powerful cricket scoring app to track matches and player stats.

## What is BoundaryLine?

BoundaryLine is a Django-based web application I built to help track cricket matches, player stats, and team performances. As a cricket fan, I wanted a clean, easy-to-use platform that doesn't overwhelm users with complexity while still providing all the essential features needed for cricket scoring and analysis.

## Current Features

Here's what you can do with BoundaryLine right now:

### Match Management
- Create and track cricket matches
- Record scores, wickets, and basic match stats
- View match history and results

### Player Tracking
- Add and manage players
- Track basic player statistics
- View player performance history

### User Experience
- Modern, responsive design that works on all devices
- Dark/light mode toggle for comfortable viewing
- Smooth page transitions and loading effects
- User authentication (login/signup/logout)

## Tech Stack

BoundaryLine is built with:
- **Backend**: Django (Python)
- **Frontend**: HTML, CSS, JavaScript
- **CSS Framework**: Bootstrap 5
- **Icons**: Font Awesome
- **Fonts**: Google Fonts (Inter, Poppins)

## Getting Started

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Setup

1. Clone the repo and enter the directory
```bash
git clone https://github.com/yourusername/boundaryline.git
cd boundaryline
```

2. Set up a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the requirements
```bash
pip install -r requirements.txt
```

4. Run migrations
```bash
python manage.py migrate
```

5. Create an admin user
```bash
python manage.py createsuperuser
```

6. Start the development server
```bash
python manage.py runserver
```

7. Open your browser and go to http://127.0.0.1:8000

## How to Use

### Creating a Match
1. Log in to your account
2. Go to the Matches page
3. Click "Add Match" 
4. Fill in the basic details (teams, location, date)
5. Save the match

### Tracking Player Stats
1. Navigate to Players
2. Click on a player to view their stats
3. Stats are automatically updated when matches are scored

## Planned Features

I'm actively working on adding these features:

- Live ball-by-ball scoring
- Detailed player statistics and analytics
- Match commentary
- Team management
- Tournament brackets
- Performance graphs and visualizations

## Contributing

Want to help make BoundaryLine better? Contributions are welcome! Just fork the repo, make your changes, and submit a pull request.

## License

This project is open-source and available under the MIT License.

---

Made with ❤️ for cricket lovers, by a cricket lover. 