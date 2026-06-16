# Analytics Project

A small automation project that downloads Excel exports from EasyBee, transforms the data with Python, and inserts the cleaned dataset into a MySQL database. It also includes a local Metabase/Postgres compose setup for analytics.

## Repository Structure

- `export_axia/`
  - `export_from_axia.js` - Puppeteer script to login to EasyBee and download the Excel export.
  - `package.json` - Node dependency manifest for the export scripts.
- `import_pandas.py` - Python script that reads the downloaded Excel file, cleans and transforms columns, and loads it through `insert_db.py`.
- `insert_db.py` - database insert helper using SQLAlchemy and PyMySQL.
- `requirements.txt` - Python dependencies for the data transform workflow.
- `metabase-postgres/docker-compose.yml` - sample Metabase + Postgres container config.
- `.env` - database connection settings for the Python import script.

## Prerequisites

- Node.js (v18+ recommended)
- Python 3.10+ (or later)
- `pip` for Python package installation
- Access to the EasyBee site and the expected Excel export flow
- MySQL server reachable from this machine

## Setup

### Install Node dependencies

```powershell
cd export_axia
npm install
```

### Install Python dependencies

```powershell
cd ..
python -m pip install -r requirements.txt
```

### Configure the database

Copy or update the `.env` file in the repo root with your database credentials:

```env
DB_HOST=your-db-host
DB_PORT=3306
DB_NAME=analytics
DB_USER=your-user
DB_PASSWORD=your-password
```

## Usage

### 1. Download the Excel export

Run the export script from `export_axia/`:

```powershell
cd export_axia
node export_from_axia.js
```

This script logs into EasyBee and saves the downloaded file into the configured download folder.

### 2. Transform and insert data

After the file is downloaded, run the Python import script:

```powershell
python import_pandas.py
```

The script expects the Excel file at:

```text
export_axia/downloads/ListeVersements.xlsx
```

It will clean several columns, compute derived values, normalize region names, and insert the result into the `list_versement` table.

## Database

The `insert_db.py` script creates or replaces the `list_versement` table, writes the DataFrame to SQL, and then alters the `id` column to be an auto-increment primary key.

## Metabase (Optional)

A sample `docker-compose.yml` is provided under `metabase-postgres/` for running Metabase with Postgres. This is separate from the main EasyBee export and MySQL load workflow.

```powershell
cd metabase-postgres
docker compose up -d
```

## Notes

- The Excel import uses `python_calamine` to read the workbook and `pandas` for cleaning.
- The export script currently uses Puppeteer and Firefox configuration for downloads.
- If the downloaded file path changes, update `import_pandas.py` accordingly.

## Improvements

- Add command-line arguments to select the download folder and input file path.
- Add a dedicated script to validate `.env` values before inserting into the database.
- Add logging and error handling for download failures and Excel schema changes.
