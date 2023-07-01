"""
script to load dataframe into google cloud storage
"""
from google.cloud import storage


def write_to_bucket(target_bucket_name, save_name, target_df):
    """
    target_bucket: name of bucket in storage
    save_name: name of file to save as
    target_df: df object to write to bucket
    """
    store_client = storage.Client()
    bucket = store_client.get_bucket(target_bucket_name)
    bucket.blob(save_name).upload_from_string(target_df.to_csv(index=False))

