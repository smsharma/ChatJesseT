import os
import shutil
import tarfile
import zipfile
import requests
import fnmatch
import subprocess
import re

import pandas as pd
from tqdm import tqdm


def remove_latex_preamble(latex_source):
    """Remove the LaTeX preamble from a string containing LaTeX source."""
    # Regular expression to match the preamble
    preamble_pattern = re.compile(r"\\documentclass.*?(?=\\begin\{document\})", re.DOTALL | re.MULTILINE)

    # Remove the preamble using the re.sub function
    cleaned_latex_source = preamble_pattern.sub("", latex_source)

    return cleaned_latex_source


def get_inspire_hep_papers(author, year_cutoff=2013):
    """Get all papers from Inspire-HEP for a given author."""
    inspire_url = "https://inspirehep.net/api/literature"
    params = {
        "q": f"author:{author} and date > {year_cutoff}-01-01",
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
    # Try to download the source
    try:
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
            else:
                raise ValueError(f"Unknown content type: {content_type}")

            # For papers with the older arXiv ID format, replace the slash with an underscore
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
            else:
                print(f"Downloaded {arxiv_id} as a PDF file: {file_path}")
                return

            main_tex_candidates = []
            for root, _, filenames in os.walk(extracted_folder):
                for filename in fnmatch.filter(filenames, "*.tex"):
                    file = os.path.join(root, filename)
                    main_tex_candidates.append(file)
            print(f"Found {len(main_tex_candidates)} .tex files in {arxiv_id}")
            print(f"They are: {main_tex_candidates}")
            if main_tex_candidates:
                main_tex = max(main_tex_candidates, key=lambda f: os.path.getsize(f))
                print(f"Using {main_tex} as the main .tex file")
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
                main_tex_new_path = os.path.join(output_dir, arxiv_id + "_" + os.path.basename(main_tex))
                shutil.move(main_tex, main_tex_new_path)

                # # Delete the extracted_folder
                # for root, dirs, files in os.walk(extracted_folder, topdown=False):
                #     for file in files:
                #         file_path = os.path.join(root, file)
                #         os.remove(file_path)
                #     for dir in dirs:
                #         dir_path = os.path.join(root, dir)
                #         os.rmdir(dir_path)
                # os.rmdir(extracted_folder)
            else:
                print(f"No main file found for {arxiv_id}")
        else:
            print(f"Error {response.status_code} while downloading {arxiv_id}")
    except:
        # If all else fails, download the PDF
        download_arxiv_pdf(arxiv_id, output_dir=output_dir)
