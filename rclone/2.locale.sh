#!/bin/bash

if ! dpkg -s locales &> /dev/null; then
    apt update
    apt install -y locales
fi

if ! grep -q '^zh_TW.UTF-8' /etc/locale.gen; then
    sed -i 's/^# zh_TW.UTF-8/zh_TW.UTF-8/' /etc/locale.gen
fi
locale-gen
locale-gen en_US.UTF-8
export LC_ALL=en_US.UTF-8

if ! grep -q 'LANG=en_US.UTF-8' /etc/default/locale; then
    echo "LANG=en_US.UTF-8" > /etc/default/locale
    echo "LC_ALL=en_US.UTF-8" >> /etc/default/locale
fi
