# setup
import sys
sys.path.append('lib/extract_scripts')
import extract_from_fastf1
sys.path.append('lib/load_scripts')
# sys.path.append('schema_sql')
# sys.path.append('load_sql')
import load_to_bq
import load_to_storage

import config as cfg
import pandas as pd
import fastf1

"""
Outline
- main py that inits everything
- modular py that pulls from f1
- modular py that writes it to storage
- modular py that takes it from storage into bq
- modular py for transforms
- py that inits all schemas
- .sql that holds all schemas
"""

def main():
    # grab a season's calendar
    event_schedule = extract_from_fastf1.extract_schedule(2023)
    load_to_storage.write_to_bucket(cfg.RAW_BUCKET_NAME, 'event_schedule.csv', event_schedule)
    load_to_bq.load_table_from_storage(cfg.RAW_BUCKET_NAME, 'event_schedule.csv', 'f1-data-pipeline.f1_raw_data.event_schedule' )


if __name__ == "__main__":
    main()