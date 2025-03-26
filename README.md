# Flai - Travel Planning Assistant

Flai is a ChatGPT-inspired travel planning assistant that helps users plan their trips with a clean, modern interface.

## Features

- ChatGPT-like interface for conversational travel planning
- Save and manage travel plans
- User profile management
- Mock integrations with GPT and Amadeus APIs (for flight and hotel search)

## Project Structure

- `app.py` - Flask backend with routes for the API endpoints
- `main.py` - Entry point for running the Flask application
- `models.py` - Database models (placeholder for future implementation)
- `static/` - Directory containing static assets
  - `css/styles.css` - Main stylesheet
  - `js/script.js` - JavaScript for frontend functionality
- `templates/` - Directory containing HTML templates
  - `index.html` - Main application page

## Running the Application

1. Ensure you have Python and Flask installed
2. Run the application:
```bash
python main.py
