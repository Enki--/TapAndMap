#!/bin/bash
# get today's date
# OUTPUT="$(date)"
# You must add following two lines before
# outputting data to the web browser from shell
# script
  echo "Content-type: text/html"
  echo ""
#  echo "<html><head><title>Demo</title></head><body>"
#  echo "Today is $OUTPUT <br>"
#cp /var/www/right_template.html /var/www/right.html
cp /var/www/Connections_Seen_Template.json /var/www/Connections_Seen.json
echo '1' > /var/www/JSONChanged.txt
  echo "Your data is cleared from the underlying Map files <p>"
  echo "It is still resident in the logs, and the Tap is still capturing<p>"
  echo "Close this tab and refresh the original tab to start with a blank screen"
#  echo "Current directory is $(pwd) <br>"
# echo "Shell Script name is $0"
# echo "</body></html>"
#/usr/bin/killall TapAndMap_PacketSniffer_to_File.py
#/var/www/TapAndMap_PacketSniffer_to_File.py &

