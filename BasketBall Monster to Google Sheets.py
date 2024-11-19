# 1. First we navigate to each table of data,
# 2. scrape the data into dataframes,
# 3. then add them to Google Sheets

import pandas as pd
from playwright.sync_api import sync_playwright
import time
import gspread
from gspread_dataframe import set_with_dataframe
from google.oauth2.service_account import Credentials


# Constant variables

# If you ever want to run this script from a server, I strongly recommend putting your username,
# password and credentials in a hidden environment, rather than visible here in the code.
username = "####"
password = "####"

login_page = "https://basketballmonster.com/login.aspx"
username_field = "#UsernameTB"
password_field = "#PasswordTB"
signin_btn = "#LoginButton"
tools_nav_btn = "#navbarSupportedContent > ul.navbar-nav.mr-auto > li:nth-child(1) > a"
player_rankings_nav_btn = "#navbarSupportedContent > ul.navbar-nav.mr-auto > li.nav-item.dropdown.show > div > a:nth-child(1)"
ease_rankings_nav_btn = "#navbarSupportedContent > ul.navbar-nav.mr-auto > li.nav-item.dropdown.show > div > a:nth-child(9)"
time_period_drp_menu = "#DateFilterControl" # same on ease page
past_three_weeks_option = "#DateFilterControl > option:nth-child(4)"
past_month_option = "#DateFilterControl > option:nth-child(5)" # same on ease page
value_drp_menu = "#ValueDisplayType"
per_game_value_option = "#ValueDisplayType > option:nth-child(2)"
per_thirty_six_stats_option = "#form1 > div.container-fluid.mb-1.mr-1 > div:nth-child(2) > div > div:nth-child(2) > span > label:nth-child(6)"
player_drp_menu = "#PlayerFilterControl"
all_players_option = "#PlayerFilterControl > option:nth-child(2)"
ease_options_drp_menu = "#ContentPlaceHolder1_PositionDropDownList"
option_pg = "#ContentPlaceHolder1_PositionDropDownList > option:nth-child(2)"
option_sg = "#ContentPlaceHolder1_PositionDropDownList > option:nth-child(3)"
option_sf = "#ContentPlaceHolder1_PositionDropDownList > option:nth-child(4)"
option_pf = "#ContentPlaceHolder1_PositionDropDownList > option:nth-child(5)"
option_c = "#ContentPlaceHolder1_PositionDropDownList > option:nth-child(6)"



table_past_three_weeks = "#form1 > div.container-fluid.mb-1.mr-1 > table"
table_past_month = "#form1 > div.container-fluid.mb-1.mr-1 > table"
table_ease_ratings_pg = "#form1 > div.container-fluid.mb-1.mr-1 > table"
past_three_weeks_GS_name = "Rankings Rankings Past 3 Weeks"
past_month_GS_name = "Player Rankings Past Month"
ease_rankings_PG_GS_name = "Ease Rankings Past Month PG"
ease_rankings_SG_GS_name = "Ease Rankings Past Month SG"
ease_rankings_SF_GS_name = "Ease Rankings Past Month SF"
ease_rankings_PF_GS_name = "Ease Rankings Past Month PF"
ease_rankings_C_GS_name = "Ease Rankings Past Month C"

# 1. NAVIGATING TO TABLES

with sync_playwright() as p:

    # First we set up an automated browser user
    # You can change headless=True to headless=False, if you want to see the browser on-screen
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    # We go to the login page, and login
    page.goto(login_page)
    page.fill(username_field, username)
    page.fill(password_field, password)
    page.click(signin_btn)
    page.wait_for_timeout(2000)

    # Logs in and waits for the nav-bar menu button to be visible before clicking it
    page.is_visible(tools_nav_btn)
    page.click(tools_nav_btn)
    page.is_visible(player_rankings_nav_btn)

    # This redirects logged in to https://basketballmonster.com/playerrankings.aspx
    page.click(player_rankings_nav_btn)

    # We are now on the player data page

    # # first we will select the past 3 weeks option
    page.is_visible(time_period_drp_menu)
    page.click(time_period_drp_menu)
    page.wait_for_timeout(2000)
    # page.keyboard.press('ArrowUp')
    # page.keyboard.press('ArrowUp')
    # page.keyboard.press('ArrowUp')
    # page.keyboard.press('ArrowDown')
    # page.keyboard.press('ArrowDown')
    # page.keyboard.press('ArrowDown')
    # page.keyboard.press('Enter')
    page.select_option(time_period_drp_menu, "LastThreeWeeks") # THIS WORKS!!
    

    # We set the Value to "Per Game Value"
    page.is_visible(value_drp_menu)
    page.click(value_drp_menu)
    page.wait_for_timeout(2000)
    # page.keyboard.press('ArrowUp')
    # page.keyboard.press('ArrowUp')
    # page.keyboard.press('ArrowUp')
    # page.keyboard.press('ArrowDown')
    # page.keyboard.press('Enter')
    page.select_option(value_drp_menu, "PerGame")

    # We set the Display to "Per 36 Stats#
    page.is_visible(per_thirty_six_stats_option)
    page.click(per_thirty_six_stats_option)

    # We set the Filters to "All Players"
    page.is_visible(player_drp_menu)
    page.click(player_drp_menu)
    page.wait_for_timeout(2000)
    # page.keyboard.press('ArrowUp')
    # page.keyboard.press('ArrowUp')
    # page.keyboard.press('ArrowUp')
    # page.keyboard.press('ArrowUp')
    # page.keyboard.press('ArrowUp')
    # page.keyboard.press('ArrowDown')
    # page.keyboard.press('Enter')
    page.select_option(player_drp_menu, "AllPlayers")

    # Let the filtered table load
    page.wait_for_selector(table_past_three_weeks)
    page.wait_for_timeout(10000)
    # Scroll to load all rows
    previous_height = page.evaluate("document.body.scrollHeight")
    while True:
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(3)  # Wait for new rows to load
        new_height = page.evaluate("document.body.scrollHeight")
        if new_height == previous_height:
            break
        previous_height = new_height

    # 2. SCRAPING DATA INTO DATAFRAMES

    # Collect all rows data
    page.wait_for_timeout(10000)
    data = page.evaluate('''
           () => {
               const rows = Array.from(document.querySelectorAll("table tr"));
               return rows.map(row => {
                   const cells = Array.from(row.querySelectorAll("td"));
                   if (cells.length === 0) return null;  // Skip rows without data
                   return {
                       Name: cells[6].innerText,
                       Team: cells[7].innerText,
                       g: cells[11].innerText,
                       "m/g": cells[13].innerText,
                       "p/36": cells[14].innerText,
                       "3/36": cells[15].innerText,
                       "r/36": cells[16].innerText,
                       "a/36": cells[17].innerText
                   };
               }).filter(row => row !== null);
           }
       ''')

    # Convert three weeks data to DataFrame
    df_three_weeks = pd.DataFrame(data)

    # getting data for past month
    page.is_visible(time_period_drp_menu)
    page.click(time_period_drp_menu)
    page.wait_for_timeout(2000)
    # page.keyboard.press('ArrowUp')
    # page.keyboard.press('ArrowUp')
    # page.keyboard.press('ArrowUp')
    # page.keyboard.press('ArrowUp')
    # page.keyboard.press('ArrowUp')
    # page.keyboard.press('ArrowUp')
    # page.keyboard.press('ArrowUp')
    # page.keyboard.press('ArrowUp')
    # page.keyboard.press('ArrowUp')
    # page.keyboard.press('ArrowDown')
    # page.keyboard.press('ArrowDown')
    # page.keyboard.press('ArrowDown')
    # page.keyboard.press('ArrowDown')
    # page.keyboard.press('Enter')
    page.select_option(time_period_drp_menu, "LastMonth")

    # Let the filtered table load
    page.wait_for_selector(table_past_month)
    page.wait_for_timeout(10000)
    # Scroll to load all rows
    previous_height = page.evaluate("document.body.scrollHeight")
    while True:
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(3)  # Wait for new rows to load
        new_height = page.evaluate("document.body.scrollHeight")
        if new_height == previous_height:
            break
        previous_height = new_height

    # Collect all rows data
    page.wait_for_timeout(10000)
    data = page.evaluate('''
           () => {
               const rows = Array.from(document.querySelectorAll("table tr"));
               return rows.map(row => {
                   const cells = Array.from(row.querySelectorAll("td"));
                   if (cells.length === 0) return null;  // Skip rows without data
                   return {
                       Name: cells[6].innerText,
                       Team: cells[7].innerText,
                       g: cells[11].innerText,
                       "m/g": cells[13].innerText,
                       "p/36": cells[14].innerText,
                       "3/36": cells[15].innerText,
                       "r/36": cells[16].innerText,
                       "a/36": cells[17].innerText
                   };
               }).filter(row => row !== null);
           }
       ''')
    # Convert past month data to DataFrame
    df_past_month = pd.DataFrame(data)

    # Logs in and waits for the nav-bar menu button to be visible before clicking it
    page.is_visible(tools_nav_btn)
    page.click(tools_nav_btn)

    # Goes to Ease Rankings page
    page.is_visible(ease_rankings_nav_btn)
    page.click(ease_rankings_nav_btn)
    page.is_visible(time_period_drp_menu)
    page.click(time_period_drp_menu)
    page.wait_for_timeout(2000)
    # page.keyboard.press('ArrowUp')
    # page.keyboard.press('ArrowUp')
    # page.keyboard.press('ArrowUp')
    # page.keyboard.press('ArrowUp')
    # page.keyboard.press('ArrowUp')
    # page.keyboard.press('ArrowUp')
    # page.keyboard.press('ArrowDown')
    # page.keyboard.press('ArrowDown')
    # page.keyboard.press('ArrowDown')
    # page.keyboard.press('ArrowDown')
    # page.keyboard.press('Enter')
    page.select_option(time_period_drp_menu, "LastMonth")

    # PG
    page.is_visible(ease_options_drp_menu)
    page.click(ease_options_drp_menu)
    page.wait_for_timeout(2000)
    # page.keyboard.press('ArrowUp')
    # page.keyboard.press('ArrowUp')
    # page.keyboard.press('ArrowUp')
    # page.keyboard.press('ArrowUp')
    # page.keyboard.press('ArrowUp')
    # page.keyboard.press('ArrowDown')
    # page.keyboard.press('Enter')
    page.select_option(ease_options_drp_menu, "4")

    # Let the filtered table load
    page.wait_for_selector(table_ease_ratings_pg)
    page.wait_for_timeout(10000)
    # Scroll to load all rows
    previous_height = page.evaluate("document.body.scrollHeight")
    while True:
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(3)  # Wait for new rows to load
        new_height = page.evaluate("document.body.scrollHeight")
        if new_height == previous_height:
            break
        previous_height = new_height

    # Collect all rows data
    # Wait for the table to be loaded
    page.wait_for_timeout(10000)
    page.wait_for_selector('table')  # This ensures the table is available before scraping

    # Scrape the table data by extracting rows and columns
    data = page.evaluate('''() => {
        const table = document.querySelector('table');  // Target the first table
        if (!table) return [];  // If no table is found, return an empty array

        const rows = table.querySelectorAll('tr');  // Select all rows
        const data = [];

        rows.forEach(row => {
            const cells = row.querySelectorAll('td, th');  // Select all cells in each row
            const row_data = [];
            cells.forEach(cell => {
                row_data.push(cell.innerText.trim());  // Push the cell text to the row_data
            });
            if (row_data.length > 0) {
                data.push(row_data);  // Push the row data to the main data array
            }
        });

        return data;
    }''')

    # Convert ease ranking pg data to DataFrame
    df_ease_ranking_pg = pd.DataFrame(data)

    #SG
    page.is_visible(ease_options_drp_menu)
    page.click(ease_options_drp_menu)
    page.wait_for_timeout(2000)
    # page.keyboard.press('ArrowUp')
    # page.keyboard.press('ArrowUp')
    # page.keyboard.press('ArrowUp')
    # page.keyboard.press('ArrowUp')
    # page.keyboard.press('ArrowUp')
    # page.keyboard.press('ArrowDown')
    # page.keyboard.press('ArrowDown')
    # page.keyboard.press('Enter')
    page.select_option(ease_options_drp_menu, "5")

    # Let the filtered table load
    page.wait_for_selector(table_ease_ratings_pg)
    page.wait_for_timeout(10000)
    # Scroll to load all rows
    previous_height = page.evaluate("document.body.scrollHeight")
    while True:
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(3)  # Wait for new rows to load
        new_height = page.evaluate("document.body.scrollHeight")
        if new_height == previous_height:
            break
        previous_height = new_height

    # Collect all rows data
    # Wait for the table to be loaded
    page.wait_for_timeout(10000)
    page.wait_for_selector('table')  # This ensures the table is available before scraping

    # Scrape the table data by extracting rows and columns
    data = page.evaluate('''() => {
        const table = document.querySelector('table');  // Target the first table
        if (!table) return [];  // If no table is found, return an empty array

        const rows = table.querySelectorAll('tr');  // Select all rows
        const data = [];

        rows.forEach(row => {
            const cells = row.querySelectorAll('td, th');  // Select all cells in each row
            const row_data = [];
            cells.forEach(cell => {
                row_data.push(cell.innerText.trim());  // Push the cell text to the row_data
            });
            if (row_data.length > 0) {
                data.push(row_data);  // Push the row data to the main data array
            }
        });

        return data;
    }''')
    # Convert ease ranking sg data to DataFrame
    df_ease_ranking_sg = pd.DataFrame(data)

    # SF
    page.is_visible(ease_options_drp_menu)
    page.click(ease_options_drp_menu)
    page.wait_for_timeout(2000)
    # page.keyboard.press('ArrowUp')
    # page.keyboard.press('ArrowUp')
    # page.keyboard.press('ArrowUp')
    # page.keyboard.press('ArrowUp')
    # page.keyboard.press('ArrowUp')
    # page.keyboard.press('ArrowDown')
    # page.keyboard.press('ArrowDown')
    # page.keyboard.press('ArrowDown')
    # page.keyboard.press('Enter')
    page.select_option(ease_options_drp_menu, "6")

    # Let the filtered table load
    page.wait_for_selector(table_ease_ratings_pg)
    page.wait_for_timeout(10000)
    # Scroll to load all rows
    previous_height = page.evaluate("document.body.scrollHeight")
    while True:
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(3)  # Wait for new rows to load
        new_height = page.evaluate("document.body.scrollHeight")
        if new_height == previous_height:
            break
        previous_height = new_height

    # Collect all rows data
    page.wait_for_timeout(10000)
    data = page.evaluate('''() => {
        const table = document.querySelector('table');  // Target the table
        const rows = table.querySelectorAll('tr');  // Select all rows
        const data = [];

        rows.forEach(row => {
            const cells = row.querySelectorAll('td, th');  // Select all cells in each row
            const row_data = [];
            cells.forEach(cell => {
                row_data.push(cell.innerText.trim());  // Push the cell text to the row_data
            });
            if (row_data.length > 0) {
                data.push(row_data);  // Push the row data to the main data array
            }
        });

        return data;
    }''')
    # Convert ease ranking sf data to DataFrame
    df_ease_ranking_sf = pd.DataFrame(data)

    page.is_visible(ease_options_drp_menu)
    page.click(ease_options_drp_menu)
    # PF
    page.wait_for_timeout(2000)
    # page.keyboard.press('ArrowUp')
    # page.keyboard.press('ArrowUp')
    # page.keyboard.press('ArrowUp')
    # page.keyboard.press('ArrowUp')
    # page.keyboard.press('ArrowUp')
    # page.keyboard.press('ArrowDown')
    # page.keyboard.press('ArrowDown')
    # page.keyboard.press('ArrowDown')
    # page.keyboard.press('ArrowDown')
    # page.keyboard.press('Enter')
    page.select_option(ease_options_drp_menu, "7")

    # Let the filtered table load
    page.wait_for_selector(table_ease_ratings_pg)
    page.wait_for_timeout(10000)
    # Scroll to load all rows
    previous_height = page.evaluate("document.body.scrollHeight")
    while True:
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(3)  # Wait for new rows to load
        new_height = page.evaluate("document.body.scrollHeight")
        if new_height == previous_height:
            break
        previous_height = new_height

    # Collect all rows data
    page.wait_for_timeout(10000)
    data = page.evaluate('''() => {
        const table = document.querySelector('table');  // Target the table
        const rows = table.querySelectorAll('tr');  // Select all rows
        const data = [];

        rows.forEach(row => {
            const cells = row.querySelectorAll('td, th');  // Select all cells in each row
            const row_data = [];
            cells.forEach(cell => {
                row_data.push(cell.innerText.trim());  // Push the cell text to the row_data
            });
            if (row_data.length > 0) {
                data.push(row_data);  // Push the row data to the main data array
            }
        });
        return data;
    }''')
    # Convert ease ranking pf data to DataFrame
    df_ease_ranking_pf = pd.DataFrame(data)

    page.is_visible(ease_options_drp_menu)
    page.click(ease_options_drp_menu)
    page.wait_for_timeout(2000)
    # page.keyboard.press('ArrowUp')
    # page.keyboard.press('ArrowUp')
    # page.keyboard.press('ArrowUp')
    # page.keyboard.press('ArrowUp')
    # page.keyboard.press('ArrowUp')
    # page.keyboard.press('ArrowDown')
    # page.keyboard.press('ArrowDown')
    # page.keyboard.press('ArrowDown')
    # page.keyboard.press('ArrowDown')
    # page.keyboard.press('ArrowDown')
    # page.keyboard.press('Enter')
    page.select_option(ease_options_drp_menu, "3")

    # Let the filtered table load
    page.wait_for_selector(table_ease_ratings_pg)
    page.wait_for_timeout(10000)
    # Scroll to load all rows
    previous_height = page.evaluate("document.body.scrollHeight")
    while True:
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(3)  # Wait for new rows to load
        new_height = page.evaluate("document.body.scrollHeight")
        if new_height == previous_height:
            break
        previous_height = new_height

    # Collect all rows data
    page.wait_for_timeout(10000)
    data = page.evaluate('''() => {
        const table = document.querySelector('table');  // Target the table
        const rows = table.querySelectorAll('tr');  // Select all rows
        const data = [];

        rows.forEach(row => {
            const cells = row.querySelectorAll('td, th');  // Select all cells in each row
            const row_data = [];
            cells.forEach(cell => {
                row_data.push(cell.innerText.trim());  // Push the cell text to the row_data
            });
            if (row_data.length > 0) {
                data.push(row_data);  // Push the row data to the main data array
            }
        });

        return data;
    }''')
    # Convert ease ranking c data to DataFrame
    df_ease_ranking_c = pd.DataFrame(data)

    # Adding to Google Sheets
    SERVICE_ACCOUNT_FILE = 'credentials.json'
    SPREADSHEET_ID = '####'
    SCOPE = ["https://www.googleapis.com/auth/spreadsheets"]

    # Authenticate using the service account file
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPE)
    client = gspread.authorize(credentials)

    # Open the Google Sheet
    sheet = client.open_by_key(SPREADSHEET_ID)

    # Writing to google sheets
    # First we grab the past 3 weeks sheet for player data
    worksheet = sheet.worksheet(past_three_weeks_GS_name)
    # Write the first DataFrame to Google Sheets
    set_with_dataframe(worksheet, df_three_weeks)

    # Grabbing Google Sheet and writing second DF to GS
    worksheet = sheet.worksheet(past_month_GS_name)
    set_with_dataframe(worksheet, df_past_month)

    # Grabbing Google Sheet and writing third DF to GS
    worksheet = sheet.worksheet(ease_rankings_PG_GS_name)
    set_with_dataframe(worksheet, df_ease_ranking_pg)

    # Grabbing Google Sheet and writing fourth DF to GS
    worksheet = sheet.worksheet(ease_rankings_SG_GS_name)
    set_with_dataframe(worksheet, df_ease_ranking_sg)

    # Grabbing Google Sheet and writing fifth DF to GS
    worksheet = sheet.worksheet(ease_rankings_SF_GS_name)
    set_with_dataframe(worksheet, df_ease_ranking_sf)

    # Grabbing Google Sheet and writing sixth DF to GS
    worksheet = sheet.worksheet(ease_rankings_PF_GS_name)
    set_with_dataframe(worksheet, df_ease_ranking_pf)

    # Grabbing Google Sheet and writing seventh DF to GS
    worksheet = sheet.worksheet(ease_rankings_C_GS_name)
    set_with_dataframe(worksheet, df_ease_ranking_c)

    # Close the browser
    browser.close()
