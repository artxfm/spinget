#!/usr/bin/env python3

# usage:
#
#  spinget.py 11/20/2021 10:00 1
#     capture 1 hour show starting at 10:00pm on November 20, 2021.
#
# Requires python3 and:
#   - requests `pip install requests`
#   - m3u8 `pip instrall m3u8`
#
# Requires ffmpeg
#
# version 2, by mathias for WXOX


import argparse
from datetime import datetime, date, time, timezone, timedelta
import os
import subprocess
import sys

import m3u8
import requests



INDEXURL="https://ark2.spinitron.com/ark2/WXOX-{0}/index.m3u8" # pass in UTC timestamp


# Pass (segment_number, segment_uri), returns a unique filename.
def segtofile(n, seguri):
    chunkID = seguri.split("/")[-1]
    return "wxox_%0.5d_%s.tmp.mpeg" % (n, chunkID)


# Given list of downloaded segments `seglist`, concatenate them into a file
# named `output`. If `rm` is set True then also delete the downloaded segments
# if concatenation succeeds.  Returns True on success.
def concat(seglist, output, rm):
    print("creating index file for %d segments..." % len(seglist))
    # First build an index file
    indexfn = "{0}.index".format(output)
    with open(indexfn, 'w') as fdout:
        n = 0
        for seguri in seglist:
            n = n + 1
            fn = segtofile(n, seguri)
            fdout.write("file {0}\n".format(fn))

    # Then get ffmpeg to do the work:
    print("concatenating with ffmpeg...")
    ffproc = subprocess.run(["ffmpeg", "-f", "concat", "-safe", "0", "-i", "{0}".format(indexfn),  "-c", "copy", output],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if ffproc.returncode != 0:
        print("ffmpeg run failed:")
        print(ffproc.stdout)
        return False
    if rm:
        print("cleaning up")
        n = 0
        for seguri in seglist:
            n = n + 1
            os.remove(segtofile(n, seguri))
        os.remove(indexfn)
    return True


# Takes a list of segment URIs and dowloads them one at a time.
# Return True on success.
def download(seglist):
    n = 0
    for seguri in seglist:
        n = n + 1
        print("fetch seg %d/%d  %s" % (n, len(seglist), seguri))
        chunkFile = segtofile(n, seguri)        
        if os.path.exists(chunkFile):
            print("--> using cached: {0}".format(chunkFile))
            continue
        r = requests.get(seguri, stream=True)
        if r.status_code != requests.codes.ok:
            print("  * request failed: {0}".format(r.status_code))
            return False
        # print("  output to: {0}".format(chunkFile))
        with open(chunkFile, 'wb') as fd:
            for chunk in r.iter_content(chunk_size=128):
                fd.write(chunk)
    return True


# Given string format of time from user, convert to a real datetime object in
# UTC zone and return that.
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
            accum = accum + seg.duration
            if accum >= required:
                # we have enough seconds.
                break
        if total_secs == 0:
            print("playlist has no content")
            return []
        if accum >= required:
            break
        else:
            print(" --> has {0} seconds (need {1} more)".format(total_secs, required - accum))
        curts = curts + timedelta(minutes=30) # grab index starting at next half hour
    return segs


parser = argparse.ArgumentParser()
parser.add_argument('date', metavar='MM/DD/YYYY', help='The show date')
parser.add_argument('time', metavar="HH:MM", help='Starting time')
parser.add_argument('count', type=int, metavar="N", help="hours (1 or 2)")
parser.add_argument('--keep', dest='keep', action='store_const', const=True, help="keep intermediate files around")
args = parser.parse_args()

hours = args.count
if hours > 2 or hours < 1:
    print("hours must be 1 or 2")
    sys.exit(1)

timestamp = "{0} {1}".format(args.date, args.time)
utcs = makets(timestamp)

showID = utcs.strftime("%Y%m%dT%H%M00Z")
print("show start is {0}".format(showID))

outfile = "wxox_{0}_{1}h.mp4".format(showID, hours)

seglist = loadsegs(utcs, hours)
if len(seglist) > 0:
    print("downloading {0} segments...".format(len(seglist)))
    if download(seglist):
        if concat(seglist, outfile, not(args.keep)):
            print("done!")





