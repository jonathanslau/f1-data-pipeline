import pandas as pd
import fastf1
"""
script to handle extracting dataframes from fastf1
"""

def extract_schedule(season):
    """
    season: int, year of f1 season
    """

    # access api
    event_schedule = fastf1.get_event_schedule(season, include_testing=False)
    event_schedule.columns = event_schedule.columns.str.lower()

    # create new field season
    event_schedule['season'] = season

    return event_schedule
    