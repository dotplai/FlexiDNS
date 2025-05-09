<h1 align="center">FlexiDNS Service</h1>

**FlexiDNS Service** is `flexidns.service` and contains `rxt.sh` file, It supports flexible sync scheduling and runs as a background systemd service.

> ⚠️ **FlexiDNS Service only supports Linux and Unix-like systems.**  
> It will **not work on Windows**.

## 🔧 Prerequisites

- Python 3.10+
- Virtual environment setup (recommended)
- Internet access for DNS updates

## Configuration

1. Open the `config.ini` file to configure the application. Here's an example:

   ```ini
   [General]
   loopingMethod = "unixEpoch"
   syncTime = 300 # seconds

   [CloudFlare]
   enabled = True
   email = "your-email@example.com"
   password = "your-api-token"
   FQDNv4 = ["example.com", "subdomain.example.com"]
   FQDNv6 = ["example.com", "subdomain.example.com"]
   cacheTimeout = 172800
   cachePersistent = True
   ```

## 📦 Installation Service

1. Install and checking status

    ```bash
    git clone https://github.com/dotplai/FlexiDNS.git
    cd ./FlexiDNS/
    ./install.service.sh
    sudo systemctl status flexidns.service
    ```

## Contributing

> Yeah, You can fork the repository to make it use easier or more useful.

1. Fork the repository.
2. Create a new branch for your feature or bugfix:

   ```bash
   git checkout -b feature-name
   ```

3. Commit your changes:

   ```bash
   git commit -m "Add your commit message here"
   ```

4. Push to your branch:

   ```bash
   git push origin feature-name
   ```

5. Submit a pull request.
