# FRC Scouting Tool

An indevelopment scouting tool.

## Setup

1. Clone this repository:
   ```
   git clone https://github.com/Risith-Kankanamge/FRC-Scouting-Tool.git
   cd frc-scouting-tool
   ```

2. Copy the example environment file and configure your API keys:
   ```
   cp .env.youchange .env
   ```
   Then edit `.env` and add:
   - The TBA API key
   - A Flask secret key (any random string)

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Run the application:
   ```
   python app.py
   ```

5. Open http://localhost:5000 in your browser or the link given in terminal