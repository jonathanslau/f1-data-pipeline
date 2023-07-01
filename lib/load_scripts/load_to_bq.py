from google.cloud import bigquery


def load_table_from_storage(target_bucket_name, object_name, target_table_id):
    """
    target_bucket_name: name of bucket as defined in google cloud storage
    object_name: name of object in storage to load to bigquery 
    target_table_id: name of target table in bigquery
    """
    query_client = bigquery.Client()
    job_config = bigquery.LoadJobConfig(
        # autodetect = True,    
        skip_leading_rows=1,
        source_format=bigquery.SourceFormat.CSV
    )
    uri = f"gs://{target_bucket_name}/{object_name}"

    load_job = query_client.load_table_from_uri(
        uri, target_table_id, job_config=job_config
    )

    # Waits for the job to complete.
    load_job.result()

    destination_table = query_client.get_table(target_table_id) 

    return print(f"loaded {destination_table.num_rows} rows")


# def main():
#     load_table_from_storage('fastf1-data-raw', 'f1-data-pipeline.f1_raw_data.event_schedule', 'event_schedule.csv')
    

# if __name__ == "__main__":
#    main()