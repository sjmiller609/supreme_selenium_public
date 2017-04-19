#!/bin/bash
echo "-----------------------------"
sudo -u ubuntu /usr/bin/python3 /home/ubuntu/supreme_selenium/buy_stuff.py
cat /var/log/cloud-init-output.log > /home/ubuntu/supreme_selenium/results/output

