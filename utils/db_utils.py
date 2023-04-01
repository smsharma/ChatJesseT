import os
import pandas as pd
import requests
from bs4 import BeautifulSoup


def scrape_website_text(url):
    """Scrape the text contents of a website."""
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove script and style tags
        for script in soup(["script", "style"]):
            script.decompose()

        # Get text and remove leading/trailing whitespaces
        text = soup.get_text(separator="\n")

        # Preserve line breaks
        clean_text = ""
        for line in text.split("\n"):
            clean_text += line.strip() + "\n"

        return clean_text.strip()

    except requests.exceptions.RequestException as e:
        print(f"Error while fetching URL {url}: {e}")
        return None


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


def delete_files_except_extensions(directory_path, extensions_list):
    """Delete all files and folders from a directory except those whose extension is in the specified list."""
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            file_path = os.path.join(root, file)
            file_extension = os.path.splitext(file_path)[1]
            if file_extension not in extensions_list:
                os.remove(file_path)
        for dir in dirs:
            dir_path = os.path.join(root, dir)
            if not os.listdir(dir_path):
                os.rmdir(dir_path)


def get_filenames_with_extensions(directory, extensions_list):
    """Get the filenames of all files with specified extensions in a directory."""
    all_files = os.listdir(directory)
    filtered_files = [file for file in all_files if os.path.splitext(file)[1].lower() in extensions_list]
    return filtered_files
