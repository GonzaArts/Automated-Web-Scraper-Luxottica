# Luxottica Image Extraction Tool

This repository contains a Python script designed to automate the process of logging into the EssilorLuxottica website, scraping product data, downloading images, converting them to PNG format, and sending a notification email upon completion.

## Overview

The script performs the following actions:

1. **Session Initialization**: It starts by opening a headless Chrome browser, logging into the EssilorLuxottica website, and storing session cookies for subsequent requests.
2. **Data Scraping**: For each product listed in the provided CSV file, the script scrapes product data from the EssilorLuxottica website using the saved cookies.
3. **Image Downloading and Conversion**: Images for each product are downloaded and converted from AVIF to PNG format using ImageMagick's `convert` command.
4. **Data Compilation**: It compiles the image paths into a CSV file, associating each SKU with its corresponding image.
5. **Notification**: Once the entire process is complete, it sends an email notification indicating that the extraction and conversion are finished, along with the time of completion.

## Setup

Before running the script, ensure that you have the following prerequisites installed:

- Python 3.x
- Selenium WebDriver for Chrome
- ChromeDriver compatible with the version of Google Chrome installed on your system
- ImageMagick for image conversion
- Required Python packages: `selenium`, `pandas`, `requests`, `subprocess`, `datetime`

Install the necessary Python packages using:

```bash
pip install selenium pandas requests python-dotenv

```

## Usage

- Update the archivo.csv with the product SKUs and names you want to process.
- Place your login credentials and SMTP configuration in a .env file or directly in the script (not recommended for security reasons).

Run the script:

```bash
python scraper.py
```
- Check the output CSV files for the results and logs for any potential errors.

## Contributing

Contributions to the project are welcome. Please follow the standard fork-and-pull request workflow.

## Contact

For any queries or assistance, please open an issue on this repository or contact gonzalo@powerlinedesign.es
