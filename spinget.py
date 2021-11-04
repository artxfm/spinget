#!/usr/bin/env python3

# usage:
#
#  spinget.py 11/20/2021 10:00 2
#     capture 2 hours starting at 10:00pm on November 20, 2021.
#
# Requires python3 and the requests lib.
# `pip install requests` should do it.
#
#
# version 1, by mathias for WXOX


import argparse
import sys
import os
from datetime import datetime, date, time, timezone, timedelta
import requests


BASEURL="https://ark-wxox.s3.us-east-1.amazonaws.com/"
URLTMPL = BASEURL+"WXOX-{0}.mp3"


# Get a 5 minute chunk using the passed datetime (which must be multiple of 5 minutes).
# Returns the name of file written or empty string if request fails.
def get5MinChunk(utcdt):
    chunkID = utcdt.strftime("%Y%m%dT%H%M00Z")  
    url = URLTMPL.format(chunkID)
    print("fetch chunk {0}".format(chunkID))
    print("  => ", url)

    headers = {
        'Connection': 'keep-alive',
        'sec-ch-ua': '"Google Chrome";v="95", "Chromium";v="95", ";Not A Brand";v="99"',
        'DNT': '1',
        'sec-ch-ua-mobile': '?0',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.#54 Safari/537.36',
        'sec-ch-ua-platform': '"macOS"',
        'Accept': '*/*',
        'Origin': 'https://spinitron.com',
        'Sec-Fetch-Site': 'cross-site',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Referer': 'https://spinitron.com/',
        'Accept-Language': 'en-US,en;q=0.9'
    }

    r = requests.get(url, headers=headers, stream=True)
    if r.status_code != requests.codes.ok:
        print("  * request failed: {0}".format(r.status_code))
        return ""

    chunkFile = "wxox_{0}.tmp.mp3".format(chunkID)
    print("  output to: {0}".format(chunkFile))
    with open(chunkFile, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=128):
            fd.write(chunk)
    return chunkFile



# concat all the files listed in `input` to a file named `output`.
# If `remove` is true then also delete the input files.
def concat(inputs, output, rm):
    with open(output, 'wb') as fdout:
        for fn in inputs:
            with open(fn, 'rb') as fdin:
                fdout.write(fdin.read())
            if rm:
                os.remove(fn)


# getHour gets an hour of audio by downloading each 5min chunk. Then combines
# all the chunks into one file, returning the filename.  Returns empty string on
# error.
def getHour(utcdt):
    hourID = utcdt.strftime("%Y%m%dT%H%M00Z")  
    chunks = []
    cur = utcdt
    for n in range(0, 12):
        cfile = get5MinChunk(cur)
        if len(cfile) > 0:
            chunks.append(cfile)
        cur = cur + timedelta(minutes=5)
    if len(chunks) == 0:
        return ""
    outfile = "wxox_{0}.hr.mp3".format(hourID)
    concat(chunks, outfile, True)
    return outfile



# getHours gets `n` hours of audio starting with timestamp `utcdt` (timestamp in UTC).
# Returns mp3 filename, or empty string if error.
def getHours(utcdt, n):
    showID = utcdt.strftime("%Y%m%dT%H%M00Z")  
    hours = []
    cur = utcdt
    for i in range(0, n):
        hourfile = getHour(cur)
        if len(hourfile) > 0:
            hours.append(hourfile)
        cur = cur + timedelta(hours=1)
    if len(hours) == 0:
        return ""
    outfile = "wxox_{0}.mp3".format(showID)
    if len(hours) == 1:
        os.rename(hours[0], outfile)
    else:
        concat(hours, outfile, True)
    return outfile




parser = argparse.ArgumentParser()
parser.add_argument('date', metavar='MM/DD/YYYY', help='The show date')
parser.add_argument('time', metavar="HH:MM", help='Starting time')
parser.add_argument('count', type=int, metavar="N", help='Number of hours to retrieve (up to 4)')
args = parser.parse_args()

hours = args.count
timestamp = "{0} {1}".format(args.date, args.time)

localstamp  = datetime.strptime(timestamp, "%m/%d/%Y %H:%M")
tt = localstamp.timetuple()
if not(tt.tm_min == 0 or tt.tm_min == 5):
    print("ERROR: time must be multiple of 5 minutes")
    sys.exit(1)
if hours > 4 or hours < 1:
    print("ERROR: hours must be betwen 1 and 4")
    sys.exit(1)

utcstamp = localstamp.astimezone(timezone.utc)
print("show start is {0}".format(utcstamp.strftime("%Y%m%dT%H%M00Z")))
outfile = getHours(utcstamp, hours)
if outfile == "":
    print("Uh oh, nothing was retrieved!")
    sys.exit(1)
print("downloaded audio to {0}".format(outfile))



