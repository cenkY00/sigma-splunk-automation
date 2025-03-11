import requests
import json
import subprocess
import splunklib.client as client
import splunklib.results as results
import time

# Install sigma-cli if not already installed
def install_sigma_cli():
    subprocess.run(
        ["powershell.exe", "-Command", "python -m pip install sigma-cli"],
        capture_output=True, text=True
    )



# Configuration variables
SPLUNK_HOST = "localhost"
SPLUNK_PORT = 8089
USERNAME = "***"
PASSWORD = "***"
SESSION_KEY = "***"
SIGMA_RULE_PATH = './win_powershell_screenshout.yml'  # Path to Sigma rule file
SPLUNK_SEARCH_WINDOW = "-24h"



# Convert Sigma rule to Splunk query using sigma-cli
def convert_sigma_to_splunk(sigma_rule):
    try:
        result = subprocess.run(
            ["powershell.exe", "-Command", f"sigma convert -t splunk --without-pipeline {sigma_rule}"],
            capture_output=True, text=True
        )
        return result.stdout.strip()
    except Exception as e:
        print(f"Failed to convert Sigma rule to Splunk query: {e}")
        return None



# Connect to the Splunk service
def connect_to_splunk():
    try:
        service = client.connect(
            host=SPLUNK_HOST,
            port=SPLUNK_PORT,
            username=USERNAME,
            password=PASSWORD,
            token=SESSION_KEY
        )
        return service
    except Exception as e:
        print(f"Failed to connect to Splunk: {e}")
        return None



# Execute the Splunk query and fetch results
def execute_splunk_search(service, splunk_query):
    kwargs_export = {
        "earliest_time": SPLUNK_SEARCH_WINDOW,
        "latest_time": "now",
        "search_mode": "normal",
        "output_mode": "json"
    }

    try:
        search_job = service.jobs.create(f'search {splunk_query}', **kwargs_export)

        # Wait for the search job to complete
        while not search_job.is_done():
            time.sleep(2)

        # Fetch search results
        search_results = search_job.results(output_mode="json")
        return json.loads(search_results.readall())
    except Exception as e:
        print(f"Error executing Splunk search: {e}")
        return None




def main():
    # If already installed, you can comment out this line.
    # install_sigma_cli()

    # Convert Sigma rule to Splunk query
    splunk_query = convert_sigma_to_splunk(SIGMA_RULE_PATH)
    if not splunk_query:
        print("No Splunk query generated.")
        return

    # Connect to Splunk
    service = connect_to_splunk()
    if not service:
        print("Splunk connection failed.")
        return

    # Execute Splunk search
    results = execute_splunk_search(service, splunk_query)


    if len(results.get('results')) == 0:
        print("Search completed, no results found")
    else:
        print(f"Search results: {json.dumps(results, indent=4)}")
        

# Entry point
if __name__ == '__main__':
    main()
