import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Function to authenticate and fetch data from Google Sheets
def fetch_data_from_sheets():
    # Define the scope for Google Sheets API access
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    # /home/sayan/Desktop/Work/Levitas/performance_project/credentials.json
    
    # Authorize the client to interact with the Sheets API
    client = gspread.authorize(creds)
    
    # Open the sheet by its URL
    sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/14Y5mlPI-MqPMkI-5tIrnGDVs_otWJsqSXrDgh2_6ab4/edit?gid=0").sheet1
    
    # Get all records from the sheet
    data = sheet.get_all_records()

    # Return data as a pandas DataFrame
    import pandas as pd
    df = pd.DataFrame(data)
    return df
