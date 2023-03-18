import os
import pandas as pd


def update_dataframe(csv_path, new_dataframe):
    """
    Load a Pandas dataframe CSV if it exists, update it given a new dataframe by adding the rows of the new dataframe
    (check that the column names match), and return a new combined dataframe. Avoids adding duplicate rows.
    """
    # check if CSV file exists
    if os.path.exists(csv_path):
        # load existing dataframe
        existing_dataframe = pd.read_csv(csv_path)

        # check if column names match
        if set(existing_dataframe.columns) == set(new_dataframe.columns):
            # drop duplicates from new dataframe
            new_dataframe = new_dataframe.drop_duplicates()

            # concatenate dataframes and drop duplicates
            combined_dataframe = pd.concat([existing_dataframe, new_dataframe], ignore_index=True)
            combined_dataframe = combined_dataframe.drop_duplicates()

            return combined_dataframe
        else:
            print("Column names do not match.")
    else:
        # CSV file does not exist, return new dataframe
        return new_dataframe
