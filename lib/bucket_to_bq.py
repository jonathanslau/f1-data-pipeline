from google.cloud import bigquery
#import sys
# sys.path.insert(1, '/lib/schema-sql')
# import table_definitions


def load_table_from_storage(target_bucket_name, table_id, object_name):
    """

    """
    query_client = bigquery.Client()
    job_config = bigquery.LoadJobConfig(
        # autodetect = True,    
        skip_leading_rows=1,
        source_format=bigquery.SourceFormat.CSV
    )
    uri = f"gs://{target_bucket_name}/{object_name}"

    load_job = query_client.load_table_from_uri(
        uri, table_id, job_config=job_config
    )

    # Waits for the job to complete.
    load_job.result()

    destination_table = query_client.get_table(table_id)  # Make an API request.
    return print("Loaded {} rows.".format(destination_table.num_rows))


def main():
    load_table_from_storage('fastf1-data-raw', 'f1-data-pipeline.f1_raw_data.event_schedule', 'event_schedule.csv')
    

if __name__ == "__main__":
    main()