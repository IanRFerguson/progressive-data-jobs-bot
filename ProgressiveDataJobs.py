"""
Goals of this project

* Scrape job information from Progressive Data Jobs
* Convert recent jobs to string
* Deliver formatted list to my inbox
"""

from JobScraper import *

# ------------ Run That Puppy
raw = fillJSON(scrapePDJ())
frame = stackSoup(raw)
credentials = emailCredentials()
sendEmailMessage(frame)
