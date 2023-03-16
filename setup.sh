#!/bin/bash

# Устанавливаем зависимости
if ! command -v python3 &> /dev/null; then
    sudo apt-get update
    sudo apt-get install -y python3
fi

if ! command -v pip3 &> /dev/null; then
    sudo apt-get install -y python3-pip
fi

if ! pip3 list | grep Flask &> /dev/null; then
    sudo pip3 install Flask
fi

# Скачиваем Python скрипт
sudo curl -o /usr/local/bin/reversetunnel.py https://raw.githubusercontent.com/RockieGear/rt/main/service.py
sudo chmod +x /usr/local/bin/reversetunnel.py

# Создаем пользователя
if [ -z "$1" ]; then
    username="sshtunnel"
else
    username="$1"
fi
sudo adduser --disabled-password --gecos "" $username
password=$(openssl rand -base64 14)
echo "$username:$password" | sudo chpasswd
echo "Username: $username" | sudo tee /root/sshcreds
echo "Password: $password" | sudo tee -a /root/sshcreds

# Настраиваем сервер для реверс туннеля
sudo sed -i 's/#GatewayPorts no/GatewayPorts yes/' /etc/ssh/sshd_config
sudo sed -i 's/#AllowTcpForwarding yes/AllowTcpForwarding yes/' /etc/ssh/sshd_config
sudo sed -i 's/#PermitOpen any/PermitOpen any/' /etc/ssh/sshd_config
sudo systemctl restart ssh

# Создаем и настраиваем сервис
sudo bash -c "cat > /etc/systemd/system/reverse_tunnel.service" << EOL
[Unit]
Description=Reverse Tunnel Service
After=network.target

[Service]
User=root
WorkingDirectory=/usr/local/bin
ExecStart=/usr/bin/python3 /usr/local/bin/reversetunnel.py
Restart=always

[Install]
WantedBy=multi-user.target
EOL

sudo systemctl daemon-reload
sudo systemctl enable reverse_tunnel.service
sudo systemctl start reverse_tunnel.service

# Проверяем статус сервиса
sudo systemctl status reverse_tunnel.service
