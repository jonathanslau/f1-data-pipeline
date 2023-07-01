import config as cfg
import transform
import pandas as pd
import fastf1
import fast_to_bucket


def main():
    event_schedule = fastf1.get_event_schedule(2022, include_testing=False)
    event_schedule = transform.column_names_to_lowercase(event_schedule)
    event_schedule['season'] = 2022

    fast_to_bucket.write_to_bucket(cfg.RAW_BUCKET_NAME, event_schedule, 'event_schedule' + '.csv')


if __name__ == "__main__":
    main()