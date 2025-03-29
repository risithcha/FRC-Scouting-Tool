import datetime

def register_template_filters(app):
    # Improve user experience by converting things
    
    @app.template_filter('timestamp_to_time')
    def timestamp_to_time(timestamp):
        # Convert unix timestamp to readable time
        if not timestamp:
            return "Unknown"
            
        try:
            dt = datetime.datetime.fromtimestamp(timestamp)
            return dt.strftime("%m/%d/%Y %I:%M %p")
        except:
            return "Invalid timestamp"