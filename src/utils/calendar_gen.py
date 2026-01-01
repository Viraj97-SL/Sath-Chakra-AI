from icalendar import Calendar, Event
from datetime import datetime
import os


def create_ics_file(events_list, user_id):
    """
    Creates an iCalendar (.ics) file for the user's re-check milestones.
    Standard: RFC 5545
    """
    cal = Calendar()
    cal.add('prodid', '-//Sath-Chakra AI//Life Strategy//EN')
    cal.add('version', '2.0')

    for entry in events_list:
        # Expected format from Agent: "DATE: YYYY-MM-DD | TITLE: Name"
        try:
            parts = entry.split('|')
            date_str = parts[0].replace('DATE:', '').strip()
            title = parts[1].replace('TITLE:', '').strip()

            event = Event()
            event.add('summary', title)
            event.add('dtstart', datetime.strptime(date_str, '%Y-%m-%d').date())
            event.add('description', 'Sath-Chakra 3-Month Strategic Re-check. Review your 2026 Roadmap.')
            cal.add_component(event)
        except Exception as e:
            print(f"Skipping malformed event line: {entry}")

    output_dir = "data/calendars"
    os.makedirs(output_dir, exist_ok=True)
    file_path = f"{output_dir}/roadmap_{user_id}.ics"

    with open(file_path, 'wb') as f:
        f.write(cal.to_ical())

    return file_path