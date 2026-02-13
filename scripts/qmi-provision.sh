#!/bin/sh
AID="A0:00:00:00:87:10:02:FF:49:94:20:89:03:10:00:00"

# wait for qrtr
sleep 5

qmicli -d qrtr://0 --device-open-proxy \
  --uim-change-provisioning-session="session-type=primary-gw-provisioning,activate=yes,slot=1,aid=$AID"
