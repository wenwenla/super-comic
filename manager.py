from datetime import timezone, timedelta

from app import create_app

app = create_app()


@app.template_filter('utc_plus_8')
def format_datetime(value, pattern="%Y-%m-%d %H:%M:%S"):
    """Format a date time to (Default): d Mon YYYY HH:MM P"""
    if value is None:
        return ""
    value = value.replace(tzinfo=timezone.utc)
    tzutc_8 = timezone(timedelta(hours=8))
    value = value.astimezone(tzutc_8)
    return value.strftime(pattern)


if __name__ == '__main__':
    app.run()

'''gunicorn -w 2 -b 0.0.0.0:80 manager:app'''
