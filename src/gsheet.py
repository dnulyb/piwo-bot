import pygsheets


# Writes 'values' to the given 'range'.
# Example: 
#   range = "A2:A3", values = "[1,2]"
def google_sheet_write(range, values, rows, spreadsheet_name, sheet_number, credentials_filename):

    # Authorize with google
    gc = pygsheets.authorize(service_account_file=credentials_filename)

    # Get working sheet
    sheets = gc.open(spreadsheet_name)
    wks = sheets[sheet_number]

    # Update sheet with the new values
    if rows:
        wks.update_values(crange=range, values=[values])
    else:
        wks.update_values(crange=range, values=[values], majordim='COLUMNS')


# Writes the 'values' list to the given spreadsheet.
# Will insert at the first non-empty row.
# Assumes there are no empty rows in between non-empty rows.
def google_sheet_write_full_row(values, spreadsheet_name, sheet_number, credentials_filename):

    # Authorize with google
    gc = pygsheets.authorize(service_account_file=credentials_filename)

    # Get working sheet
    sheets = gc.open(spreadsheet_name)
    wks = sheets[sheet_number]

    # Extract all non-empty rows
    cells = wks.get_all_values(include_tailing_empty_rows=False, include_tailing_empty=False, returnas='matrix')
    nonEmptyRows = []
    for i in cells:
        if i != []:
            nonEmptyRows.append(i)

    # Get length of all non-empty rows 
    countOfnonEmptyRows = len(nonEmptyRows)    
    
    # Insert at the first empty row
    wks.insert_rows(countOfnonEmptyRows, 1, values, inherit=True)
    
