import pandas as pd
import fastf1
from google.cloud import storage
import config as cfg


def write_to_bucket(target_bucket_name, fast_df, save_name):
    """
    target_bucket: name of bucket in storage
    fast_df: df object to write to bucket
    save_name: name of file to save as
    """
    store_client = storage.Client()
    bucket = store_client.get_bucket(target_bucket_name)
    bucket.blob(save_name).upload_from_string(fast_df.to_csv(index=False))


# def main():
    # print(cfg.RAW_BUCKET_NAME)
    # write_to_bucket(cfg.RAW_BUCKET_NAME, )

# if __name__ == "__main__":
#     main()