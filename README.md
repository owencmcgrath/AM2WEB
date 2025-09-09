# Apple Music Stats Analyzer

A Flask web application that transforms your Apple Music library export into beautiful, detailed analytics about your listening habits and music preferences.

## Why This Was Built

Ever wondered what your music listening habits really look like? Apple Music provides basic year-end summaries, but what about the deeper insights hiding in your library data? This project was born from curiosity about personal music analytics - discovering patterns in listening behavior, identifying songs that have grown on you over time, and visualizing how your musical taste has evolved across decades.

The goal was to create a comprehensive tool that goes beyond simple play counts, offering insights like skip ratios, listening patterns by time of day, album completion rates, and artist consistency metrics that Apple Music doesn't provide.

## How This Was Built

This application processes Apple Music's XML library exports to extract detailed listening data and presents it through an intuitive web interface. The development approach focused on:

- **Data Processing**: Custom XML parser to handle Apple Music's complex export format
- **Analytics Engine**: SQL queries designed to uncover meaningful patterns in listening behavior
- **User Experience**: Clean, responsive interface that makes complex data accessible
- **Privacy-First**: User authentication system ensuring personal music data stays private

The entire stack was chosen for simplicity and reliability - Flask for rapid development, MySQL for robust data handling, and vanilla CSS/JavaScript for a lightweight frontend.

## Features

### 📊 Library Overview
- Total songs, artists, albums, and listening hours
- Play count statistics and favorite track metrics
- Recent activity and library growth tracking

### 🎵 Listening Patterns
- **Temporal Analysis**: Most active listening months, time of day preferences, and day-of-week patterns
- **Song Insights**: Longest and shortest tracks, most skipped songs, and never-skip favorites
- **Play Frequency**: Songs with highest plays-per-day since being added to your library

### 🎨 Artist & Album Analytics
- **Artist Growth**: Timeline of when you discovered artists and how your collection grew
- **Consistency Metrics**: Artists with the most consistent play patterns across their catalog
- **Album Completion**: Which albums you own the most complete versions of
- **Most Played**: Albums with highest total and average plays per track

### 📈 Music Evolution
- **Decade Distribution**: Visual breakdown of your music collection across time periods
- **Genre Evolution**: How your musical preferences have changed over decades
- **Listening Time**: Total hours invested in each genre with average song lengths

### 💎 Personal Favorites
- **Growers**: Songs that have steadily gained plays over time since being added
- **Never Skip**: Tracks with perfect completion rates that you always listen through
- **Skip Analysis**: Identify patterns in songs you tend to skip most often

## Technology Stack

- **Backend**: Flask (Python) - Lightweight web framework for rapid development
- **Database**: MySQL - Reliable relational database for complex music data queries
- **Frontend**: HTML/CSS/JavaScript - Clean, responsive interface without framework overhead
- **Security**: Werkzeug - Password hashing and session management
- **Data Processing**: Custom XML parser built specifically for Apple Music exports

## Usage

### Getting Your Data
1. **Export from Apple Music**: File → Library → Export Library
2. **Create Account**: Register on the web application
3. **Upload XML File**: Drag and drop or select your exported library file
4. **Explore Analytics**: View your personalized music statistics dashboard

### Understanding Your Stats
The dashboard provides multiple views of your music data:
- **Overview cards** show high-level library statistics
- **Charts and graphs** visualize listening patterns over time
- **Detailed lists** rank songs, artists, and albums by various metrics
- **Interactive elements** let you explore different aspects of your musical preferences

Your data remains completely private and is only accessible through your personal account. You can reset your data or logout at any time.

---

Made with 👾 by [Owen McGrath](https://owencmcgrath.com)
