# guiabolso2csv
Python scraper using selenium-wire to get Statement data from Guia Bolso and export to CSV

[update Jun/2021] - There is now a reCaptcha in the login page, which is not supported by the script. The current workaround was adding a breakpoint which allows for manual resolutio of the challenge and once logged in, proceeding with ```c``` as per pdb documentation


Requires:
- [selenium-wire](https://pypi.org/project/selenium-wire/)
- [chromedriver] (https://chromedriver.chromium.org/)

Tested with Chromedriver.
Chromedriver binary needs to be placed in the same directory as the .py and needs to be added in PATH.

Usage:
```
python3 guiabolso.py -username <guia_bolso_username> -password <password> -output_file_name <filename with path>
```
