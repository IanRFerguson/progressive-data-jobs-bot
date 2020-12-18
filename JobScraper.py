# ----------- Imports
from bs4 import BeautifulSoup
import requests
import pandas as pd
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import datetime


# ----------- Misc Functions
def today():
    return datetime.datetime.now().strftime('%A')                               # Returns day of the week


# ----------- Scrape Functions
def scrapePDJ():
    """
    Scrapes 'grid-job' objects from PDJ
    Returns a BeatifulSoup object
    """

    url = "https://www.progressivedatajobs.org/job-postings/"                   # Base URL
    r = requests.get(url)                                                       # Scrape PDJ url
    soup = BeautifulSoup(r.content, 'html.parser')                              # Prettify scraped HTML
    return soup.find_all('div', class_="grid-job")


def fillJSON(SOUP):
    """
    Parses text from BeautifulSoup
    Stores data in JSON dictionary
    """

    output = {'Position': [],                                                   # Empty dictionary to append into
              'Company': [],
              'Date': [],
              'Link': []}

    for gig in SOUP:
        # Likely to break if PDJ changes their website...
        try:
            output['Position'].append(gig.find('h2', class_='grid-heading').text)
        except:
            output['Position'].append('NA')
        try:
            output['Company'].append(gig.find('strong').text)
        except:
            output['Company'].append('NA')
        try:
            output['Date'].append(gig.find('span', class_='grid-date').text)
        except:
            output['Date'].append('NA')
        try:
            output['Link'].append(gig.find('a', href=True)['href'])
        except:
            output['Link'].append('NA')

    return output


def stackSoup(JSON):
    """
    Unstacks JSON to DF format
    Cleans date column (strips down to calendar date)
    Days == Days since posting
    Returns DF object
    """

    temp = pd.DataFrame(JSON)                                                   # Flatten JSON to DataFrame

    for ix, val in enumerate(temp['Date']):
        val = val.split('on')[-1].strip()                                       # Isolate posting date
        val = pd.to_datetime(val).strftime("%m/%d/%Y")                          # Convert date to datetime object
        temp['Date'][ix] = val                                                  # Reassign to DataFrame

    # Caluclate time delta between today and the posting date
    temp['Days'] = temp['Date'].apply(lambda x: (datetime.datetime.now() - pd.to_datetime(x)).days)
    return temp


def jobs2String(DF):
    """
    Formats job postings in string format
    Returns string
    """

    DF = DF[DF['Days'] <= 7]                                                    # Isolate postings in the last week

    if len(DF) == 0:
        return "<b><i>No jobs posted in the last week</i></b><br>"
    else:
        output = ""                                                             # Empty string to append to

        for row in DF.values:
            # Format job details in string format
            string = """
            <b>{}</b> @ {}<br>
            Posted on {} | <a href={} target=_blank>Link</a><br><br>
            """.format(row[0], row[1], row[2], row[3])

            output += string                                                    # Append to string

        return output


# ----------- Email Functions
def emailCredentials():
    """
    Opens local text file with email credentials
    """

    with open("Email-Credentials.txt", "r") as incoming:
        return json.load(incoming)


def sendEmailMessage(DF):
    """
    Connects to gmail server
    Fills body of email with data jobs in string format
    Sends email and closes server
    """

    # Setup SMTP server connection with local email credentials
    credentials = emailCredentials()
    port = 587
    smtp_server = 'smtp.gmail.com'
    my_address = credentials["Email Address"]
    password = credentials["Password"]
    receiver_address = "IanFergusonRVA@gmail.com"
    s = smtplib.SMTP(host=smtp_server, port=port)
    s.ehlo()
    s.starttls()
    s.login(user=my_address, password=password)

    body = formatEmail(DF)                                                      # Format HTML message body

    msg = MIMEMultipart()
    msg["From"] = "Progressive Data Jobs Bot"
    msg["To"] = "Ian Richard Ferguson"
    msg["Subject"] = ("Progressive Data Jobs Update: {}".format(datetime.datetime.now().strftime("%x")))
    msg.attach(MIMEText(body, "html"))

    s.sendmail(my_address, receiver_address, msg.as_string())
    s.quit()


def formatEmail(DF):
    """
    Formats email body in aesthetically pleasing way
    Returns string
    """

    email_jobs = jobs2String(DF)                                                # Push jobs to HTML friendly string

    msg = """
    Hi Ian,
    <br><br>
    Here are the postings from
    <a href="https://www.progressivedatajobs.org/" target=_blank><b>Progressive Data Jobs</b></a>
    in the past week:
    <br><br>{}<br>
    Onward, <br>
    <b>The Progressive Data Jobs Bot</b>
    """.format(email_jobs)

    return msg
