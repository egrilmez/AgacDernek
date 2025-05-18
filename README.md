# AIMSAD Company and LinkedIn Employee Scraper

This project scrapes company information from AIMSAD's website and their corresponding employee information from LinkedIn.

## Features

- Scrapes all company details from AIMSAD website
- Searches companies on LinkedIn
- Extracts employee information from LinkedIn company pages
- Saves data in CSV format with proper Turkish character encoding
- Implements rate limiting and anti-detection measures
- Provides detailed logging

## Prerequisites

- Python 3.8+
- Chrome browser installed
- LinkedIn account

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file:
Copy `.env.example` to `.env` and fill in your LinkedIn credentials and other configurations:
```bash
cp .env.example .env
```

## Configuration

Edit the `.env` file with your settings:

```env
LINKEDIN_USERNAME=your_email@example.com
LINKEDIN_PASSWORD=your_password
OUTPUT_DIR=output
CSV_FILENAME=company_employees.csv
```

## Usage

Run the main script:
```bash
python src/main.py
```

The script will:
1. Scrape company information from AIMSAD
2. Search each company on LinkedIn
3. Extract employee information
4. Save results to CSV file

## Output

The script generates:
- A CSV file with company and employee information
- A log file (`scraping.log`) with detailed execution information

CSV columns:
- Company details: name, address, phone, fax, email, categories
- Employee details: name, title, location

## Notes

- The script implements random delays and anti-detection measures
- LinkedIn scraping is done carefully to avoid rate limiting
- Progress is saved after each company in case of interruption
- Turkish characters are properly handled in the output

## Error Handling

- Failed company searches are logged and skipped
- Failed employee extractions are logged and the script continues
- All errors are logged to `scraping.log`

## Legal Notice

This tool is for educational purposes only. Make sure to comply with the terms of service of both AIMSAD and LinkedIn when using this scraper. 