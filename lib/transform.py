import pandas as pd


def column_names_to_lowercase(target_df):
    """
    target_df: target df to edit column names for
    """
    target_df.columns = target_df.columns.str.lower()

    return target_df