<h1 align="center">UDIP Service</h1>

**UDIP Service** is `udip.service` and contains `rxt.sh` file, It supports flexible sync scheduling and runs as a background systemd service.

> ⚠️ **UDIP Service only supports Linux and Unix-like systems.**  
> It **won't work on Windows**.

## 🔧 Prerequisites

- Python 3.12+
- Virtual environment setup (recommended)
- Internet access for DNS updates

## Configuration

1. Open the `config.ini` file to configure the application. Here's an example:

   ```ini
   [General]
      queryAPI = "ipify"
      mode = "unixEpoch"
      syncTime = 300

   [Logging]
      enabledFile = True

      consoleIncluded = [normal, debug, error]
      logIncluded = [normal, error]
      splitLog = False

   [LearningBehavior]
      timeShift = [True, 300]

   [CloudFlare]
      enabled = True

      email = "YOUR_EMAIL_OF_CLOUDFLARE"
      password = "YOUR_GLOBAL_OR_LOCAL_API_KEY"

      FQDN = '{"A": ["example.com"], "AAAA": ["v6.example.com"]}'

      cacheTimeout = 172800
      cachePersistent = True
   ```

## 📦 Installation Service

1. Install and checking status

    ```bash
    git clone https://github.com/dotplai/UDIP.git
    cd ./UDIP/
    ./service.installer.sh -y
    sudo systemctl status udip.service
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
