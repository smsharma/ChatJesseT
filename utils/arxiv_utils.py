import os
import shutil
import tarfile
import zipfile
import requests
import fnmatch
import subprocess

import pandas as pd
from tqdm import tqdm


def get_inspire_hep_papers(author):
    """Get all papers from Inspire-HEP for a given author."""
    inspire_url = "https://inspirehep.net/api/literature"
    params = {
        "q": f"author:{author}",
        "size": 1000,  # Increase this value if the author has more than 1000 papers
        "fields": "arxiv_eprints",
    }
    response = requests.get(inspire_url, params=params)
    data = response.json()
    papers = data["hits"]["hits"]
    return papers


def extract_arxiv_ids(papers):
    """Extract the arXiv IDs from the Inspire-HEP papers."""
    arxiv_ids = []
    for paper in papers:
        arxiv_eprints = paper["metadata"].get("arxiv_eprints", [])
        if arxiv_eprints:
            arxiv_id = arxiv_eprints[0]["value"]
            arxiv_ids.append(arxiv_id)
    return arxiv_ids


def download_arxiv_pdf(arxiv_id, output_dir="../data/papers"):
    """Download the PDF of a paper from arXiv."""
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    response = requests.get(pdf_url)

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{arxiv_id}.pdf".replace("/", "_"))

    with open(output_path, "wb") as f:
        f.write(response.content)


def download_arxiv_source(arxiv_id, output_dir="../data/papers"):
    """Download the source code of a paper from arXiv; if failed, download the PDF instead."""
    try:  # Try to download the source
        url = f"https://arxiv.org/e-print/{arxiv_id}"
        response = requests.get(url, stream=True)

        if response.status_code == 200:
            content_type = response.headers["content-type"]
            extension = None

            if "application/x-eprint-tar" in content_type:
                extension = ".tar"
            elif "application/x-eprint-pdf" in content_type:
                extension = ".pdf"
            elif "application/x-eprint" in content_type:
                extension = ".gz"
            elif "application/zip" in content_type:
                extension = ".zip"
            elif "application/x-eprint-z" in content_type:
                extension = ".Z"
            else:
                raise ValueError(f"Unknown content type: {content_type}")

            arxiv_id = arxiv_id.replace("/", "_")
            filename = f"{arxiv_id}{extension}"
            file_path = os.path.join(output_dir, filename)

            with open(file_path, "wb") as f:
                shutil.copyfileobj(response.raw, f)

            extracted_folder = os.path.join(output_dir, arxiv_id)
            os.makedirs(extracted_folder, exist_ok=True)

            if extension == ".tar":
                with tarfile.open(file_path, "r") as tar:
                    tar.extractall(extracted_folder)
                os.remove(file_path)
            elif extension == ".gz":
                with tarfile.open(file_path, "r:gz") as tar:
                    tar.extractall(extracted_folder)
                os.remove(file_path)
            elif extension == ".zip":
                with zipfile.ZipFile(file_path, "r") as zip_ref:
                    zip_ref.extractall(extracted_folder)
                os.remove(file_path)
            elif extension == ".Z":
                with open(file_path, "wb") as f:
                    shutil.copyfileobj(response.raw, f)
                try:
                    subprocess.run(["uncompress", file_path], check=True)
                    file_path = file_path[:-2]  # Remove the .Z extension
                except subprocess.CalledProcessError as e:
                    print(f"Error while uncompressing {arxiv_id}: {str(e)}")
                    os.remove(file_path)
                    return
                extension = os.path.splitext(file_path)[-1]

            else:
                print(f"Downloaded {arxiv_id} as a PDF file: {file_path}")
                return

            main_tex_candidates = []
            for root, _, filenames in os.walk(extracted_folder):
                for filename in fnmatch.filter(filenames, "*.tex"):
                    file = os.path.join(root, filename)
                    main_tex_candidates.append(file)

            if main_tex_candidates:
                main_tex = max(main_tex_candidates, key=lambda f: os.path.getsize(f))
                for root, dirs, files in os.walk(extracted_folder, topdown=False):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if file_path != main_tex:
                            os.remove(file_path)
                    for dir in dirs:
                        dir_path = os.path.join(root, dir)
                        if not os.listdir(dir_path):
                            os.rmdir(dir_path)

                # Move the main .tex file to the parent output_folder
                main_tex_new_path = os.path.join(output_dir, os.path.basename(main_tex))
                shutil.move(main_tex, main_tex_new_path)

                # Delete the extracted_folder
                for root, dirs, files in os.walk(extracted_folder, topdown=False):
                    for file in files:
                        file_path = os.path.join(root, file)
                        os.remove(file_path)
                    for dir in dirs:
                        dir_path = os.path.join(root, dir)
                        os.rmdir(dir_path)
                os.rmdir(extracted_folder)
            else:
                print(f"No main file found for {arxiv_id}")
        else:
            print(f"Error {response.status_code} while downloading {arxiv_id}")
    except:  # If all else fails, download the PDF
        download_arxiv_pdf(arxiv_id, output_dir=output_dir)


def get_pdf_filenames(directory):
    """Get the filenames of all PDF files in a directory."""
    all_files = os.listdir(directory)
    pdf_files = [file for file in all_files if file.lower().endswith(".pdf")]
    return pdf_files


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
