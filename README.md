Auto-updated clan rating
This repository uses an automated Python script (7.py) to keep the rating HTML page up to date.

What 7.py does
Fetches the latest clan data via HTTP requests using requests.

Parses the responses and HTML content using BeautifulSoup from the beautifulsoup4 package.

Recalculates the clan rating and builds an updated ranking table.

Updates the rating_trud_premiya_clans.html file in this repository by inserting the latest data into the HTML page.

As a result, the published GitHub Pages site always shows the current clan rating without manual edits.

How it runs (GitHub Actions)
The automation is handled by the workflow .github/workflows/update-page.yml:

The workflow is triggered every hour using a cron schedule (0 * * * *) and can also be started manually from the Actions → Update HTML page tab.

The GitHub Actions runner automatically installs dependencies:

requests

beautifulsoup4

Then it runs:

bash
python 7.py
If the script modifies any files (for example rating_trud_premiya_clans.html), the workflow:

creates a commit with the message Auto update HTML page,

pushes the changes to the main branch.

GitHub Pages then publishes the updated site from the latest commit.

Manual run
To trigger an update manually:

Go to the Actions tab in this repository.

Select the Update HTML page workflow.

Click Run workflow and wait for it to complete.

After a successful run, a new commit from github-actions[bot] will appear, and the HTML page will be refreshed.
