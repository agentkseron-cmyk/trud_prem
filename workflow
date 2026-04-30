name: Update HTML page

on:
  schedule:
    - cron: '0 * * * *'      # запуск каждый час (в 00 минут, по UTC)
  workflow_dispatch:          # запуск вручную из вкладки Actions

jobs:
  run-script:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repo
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          if [ -f requirements.txt ]; then
            pip install -r requirements.txt
          else
            echo "No requirements.txt, skipping"
          fi

      - name: Run update script
        run: |
          python 7.py

      - name: Commit and push changes
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add .
          if git diff --cached --quiet; then
            echo "No changes to commit"
          else
            git commit -m "Auto update HTML page"
            git push
          fi
