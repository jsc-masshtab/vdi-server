#!/bin/bash
sudo timeout 50s perl /usr/lib/cgi-bin/awstats.pl -config=vdi -update -output -staticlinks -month=$1 -year=$2
