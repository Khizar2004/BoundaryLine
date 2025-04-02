# 🏏 BoundaryLine - Cricket Match Management System

<div align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/Django-4.0+-green.svg" alt="Django 4.0+">
  <img src="https://img.shields.io/badge/Bootstrap-5.3-purple.svg" alt="Bootstrap 5.3">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT">
</div>

<div align="center">
  <h3>🏆 A modern, feature-rich cricket scoring and analytics platform</h3>
</div>

## 📋 Overview

BoundaryLine is a robust cricket match management system designed to help cricket clubs, teams, and enthusiasts track matches, player statistics, and performance metrics. With its intuitive interface and comprehensive feature set, BoundaryLine provides everything needed to manage cricket matches from start to finish.

## ✨ Features

### 🏏 Match Management
- Create and manage cricket matches with detailed scorecards
- Real-time scoring updates with ball-by-ball commentary
- Support for various cricket formats (T20, ODI, Test)
- Track detailed match statistics (runs, wickets, extras, etc.)

### 👥 Player Management
- Comprehensive player profiles with performance history
- Detailed batting and bowling statistics
- Career tracking and performance analysis
- Player availability management

### 📊 Analytics & Insights
- Interactive dashboards for match and player statistics
- Performance trend visualization
- Team and player rankings
- Historical data analysis

### 🎨 User Experience
- Responsive design that works on desktop and mobile devices
- Dark/light theme support for comfortable viewing
- Real-time notifications for match updates
- User authentication and role-based access control

## 🚀 Installation

### Prerequisites
- Python 3.8+
- pip (Python package manager)
- Virtual environment tool (recommended)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/boundaryline.git
   cd boundaryline
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create a superuser**
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server**
   ```bash
   python manage.py runserver
   ```

7. **Access the application**
   
   Open your browser and navigate to `http://127.0.0.1:8000`

## 🔧 Usage

### Creating a New Match
1. Log in to your account
2. Navigate to the Matches section
3. Click "Create New Match"
4. Fill in the match details (teams, venue, format)
5. Add players to each team
6. Start the match scoring

### Live Scoring
1. Select the active match
2. Use the scoring panel to record each ball
3. Track wickets, extras, and other events
4. Update overs and innings as the match progresses

### Viewing Player Statistics
1. Navigate to the Players section
2. Select a player to view their profile
3. Explore batting, bowling, and fielding statistics
4. View performance trends and match history

## 🎯 Future Roadmap

- Mobile application for on-the-go scoring
- Advanced analytics with machine learning predictions
- Video integration for match highlights
- API for third-party integrations
- Tournament and league management

## 👥 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Contact

Project Maintainer - [Your Name](mailto:your.email@example.com)

---

<div align="center">
  <p>Made with ❤️ by cricket enthusiasts for cricket enthusiasts</p>
</div> 