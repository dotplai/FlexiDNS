<h1 align="center">Universal Dynamic Internet Protocol</h1>

UDIP is a flexible and dynamic IP resolver and DNS updater designed for seamless network management. The application supports multiple APIs, cache persistence, and future IPv6 compatibility, making it ideal for personal or professional use.

> This version contains [services file](/services/readme.md).

## Features

- **Dynamic DNS Updates:** Automatically updates DNS records for your domains (e.g., Cloudflare).
- **Multi-API Support:** Compatible with services.
- **Cache Persistence:** Keeps cached data even after unexpected program exits.
- **Customizable Interval Timeout:** Set the interval time between each loop for DNS checks.
- **IPv4 and IPv6 Ready:** IPv4/6 is [<span title="Only some APIs supported now.">fully supported*</span>](#Features)
- **Error Handling:** Robust logging and error handling with customizable verbosity levels.

## Requirements

- Python 3.8 or higher
- Virtual environment setup (recommended)
- Internet access for DNS updates

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/dotplai/UDIP.git
   cd UDIP
   ```

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

## Usage

1. Start the application:

   ```bash
   ./activate.sh
   ```

2. Follow the on-screen instructions for virtual environment setup and requirements installation.

## Logs

Logs are saved in the `logs/` directory:

- `udip.log`: Contains general information about DNS updates.
- `udip.debug.log`: Detailed debug logs.
- `udip.error.log`: Detailed error logs.

## Development Roadmap

- **Additional APIs:** Support for more DNS providers.
- **Enhanced Logging:** Improved log management and filters.
- **Additional Looping Method:** Support for more Looping Method.

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

## License

This project is released into the public domain under the Unlicense. See the [`LICENSE`](./LICENSE) file for details.

## Support

If you encounter any issues, please open an issue in the GitHub repository or contact the maintainer directly.

---
Stay tuned for updates and improvements to make UDIP even more powerful and versatile!
