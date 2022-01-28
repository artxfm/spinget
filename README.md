# spinget

Download show audio from WXOX spinitron.


## How to run

1. Make sure you have ffmpeg installed.


2. Install python pre-requisites:
    
     pip3 install requests
     pip3 install m3u8
    
3. Get show audio, eg:

    ./spinget.py 11/04/2021 00:00 1

The above invocation gets `1` hour of audio starting at midnight (`00:00`) on
November 4th, 2021 (`11/04/2021`).


## Issues

- This probably will not work properly across a date boundry.
- Audio is only available for two weeks from air date.


## Contribute

Improvements and patches welcome.

