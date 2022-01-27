#!/usr/bin/env python3

# usage:
#
#  spinget.py 11/20/2021 10:00
#     capture show starting at 10:00pm on November 20, 2021.
#
# Requires python3 and:
#   - requests `pip install requests`
#   - m3u8 `pip instrall m3u8`
#
# version 2, by mathias for WXOX


import argparse
import sys
import os
from datetime import datetime, date, time, timezone, timedelta
import requests
import m3u8


INDEXURL="https://ark2.spinitron.com/ark2/WXOX-{0}/index.m3u8" # pass in UTC timestamp


def segtofile(n, seguri):
    chunkID = seguri.split("/")[-1]
    return "wxox_%0.5d_%s.tmp.mpeg" % (n, chunkID)


def concat(seglist, output, rm):
    print("concatenating %d segments..." % len(seglist))
    with open(output, 'wb') as fdout:
        n = 0
        for seguri in seglist:
            n = n + 1
            fn = segtofile(n, seguri)
            with open(fn, 'rb') as fdin:
                fdout.write(fdin.read())
            if rm:
                os.remove(fn)

# Takes a list of segment URIs and dowloads them one at a time.
def download(seglist):
    n = 0
    for seguri in seglist:
        n = n + 1
        print("fetch seg %d/%d  %s" % (n, len(seglist), seguri))
        r = requests.get(seguri, stream=True)
        if r.status_code != requests.codes.ok:
            print("  * request failed: {0}".format(r.status_code))
            return False
        chunkFile = segtofile(n, seguri)
        # print("  output to: {0}".format(chunkFile))
        with open(chunkFile, 'wb') as fd:
            for chunk in r.iter_content(chunk_size=128):
                fd.write(chunk)
    return True


# Given string format of time from user, convert to a real datetime object in
# UTC zone.
def makets(t):
    localstamp  = datetime.strptime(t, "%m/%d/%Y %H:%M")
    tt = localstamp.timetuple()
    if not(tt.tm_min == 0 or tt.tm_min == 5):
        print("ERROR: time must be multiple of 5 minutes")
        sys.exit(1)
    return localstamp.astimezone(timezone.utc)


# use the indexes to get all segments necessary for the number of hours
# requestd. Returns a list of segment URIs
def loadsegs(stamp, hours):
    curts = stamp
    segs = []
    accum = 0 # seconds
    required = hours * 60 * 60 # seconds

    while accum < required:
        showtime = curts.strftime("%Y%m%dT%H%M00Z")
        print("fetching index for {0}".format(showtime))
        playlist = m3u8.load(INDEXURL.format(showtime))
        if len(playlist.segments) == 0:
            print("no playlist data found")
            return []
        total_secs = 0 # seconds from this playlist
        for seg in playlist.segments:
            # print("    {0}  {1}s  {2}".format(showtime, seg.duration, seg.uri))
            if (total_secs + seg.duration) > (30 * 60): # have we exeecded 30mins?
                break
            segs.append(seg.uri)
            total_secs = total_secs + seg.duration
        if total_secs == 0:
            print("playlist has no content")
            return []
        accum = accum + total_secs
        print(" --> has {0} seconds (need {1})".format(total_secs, required - accum))
        if accum >= required:
            break
        curts = curts + timedelta(minutes=30) # grab index starting at next half hour
    return segs






parser = argparse.ArgumentParser()
parser.add_argument('date', metavar='MM/DD/YYYY', help='The show date')
parser.add_argument('time', metavar="HH:MM", help='Starting time')
parser.add_argument('count', type=int, metavar="N", help="hours")
args = parser.parse_args()

hours = args.count
if hours > 2 or hours < 1:
    print("hours must be 1 or 2")

timestamp = "{0} {1}".format(args.date, args.time)
utcs = makets(timestamp)

showID = utcs.strftime("%Y%m%dT%H%M00Z")
print("show start is {0}".format(showID))

outfile = "wxox_{0}_{1}h.mpeg".format(showID, hours)


seglist = loadsegs(utcs, hours)
if len(seglist) > 0:
    print("downloading {0} segments...".format(len(seglist)))
    if download(seglist):
        concat(seglist, outfile, True) # set False to leave the downloaded files.





