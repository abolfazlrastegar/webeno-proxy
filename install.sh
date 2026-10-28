#!/bin/bash
set -euo pipefail
[[ $(id -u) -eq 0 ]] || { echo 'Run using sudo'; exit 1; }
command -v sing-box >/dev/null || { echo 'Install sing-box first'; exit 1; }
[[ -x /usr/bin/sing-box ]] || { echo 'Expected sing-box at /usr/bin/sing-box'; exit 1; }
install -d -m 700 /etc/smartproxy
install -D -m 755 smartproxy-ctl /usr/local/libexec/smartproxy-ctl
install -m 644 smartproxy.service /etc/systemd/system/smartproxy.service
systemctl daemon-reload
printf 'Service installed, disabled until you run smartproxy start.\n'
