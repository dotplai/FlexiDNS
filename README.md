<h1 align="center">FlexiDNS</h1>

FlexiDNS is a flexible and dynamic IP resolver and DNS updater designed for seamless network management. The application supports multiple APIs, cache persistence, and future IPv6 compatibility, making it ideal for personal or professional use.

## Features

- **Dynamic DNS Updates:** Automatically updates DNS records for your domains (e.g., Cloudflare).
- **Multi-API Support:** Compatible with services.
- **Cache Persistence:** Keeps cached data even after unexpected program exits.
- **Customizable Interval Timeout:** Set the interval time between each loop for DNS checks.
- **IPv4 and IPv6 Ready:** IPv4/6 is fully supported* (Some APIs only)
- **Error Handling:** Robust logging and error handling with customizable verbosity levels.

## Requirements

- Python 3.8 or higher
- Virtual environment setup (recommended)

### Python Modules

Install the required Python modules by running:

```bash
pip install -r requirements.txt
```

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/dotplai/FlexiDNS.git
   cd FlexiDNS
   ```

2. Set up a virtual environment (optional but recommended):

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. Open the `config.ini` file to configure the application. Here's an example:

   ```ini
   [General]
   intervalTime = 720

   [CloudFlare]
   enabled = True
   email = "your-email@example.com"
   password = "your-api-token"
   FQDN = ["example.com", "subdomain.example.com"]
   cacheTimeout = 172800
   cachePersistent = True
   ```

2. Adjust the `intervalTime`, API credentials, and other parameters according to your needs.

## Usage

1. Start the application:

   ```bash
   ./start.sh
   ```

2. Follow the on-screen instructions for virtual environment setup and requirements installation.

## Logs

Logs are saved in the `logs/` directory:

- `flexidns.log`: Contains general information about DNS updates.
- `flexidns_debug.log`: Detailed debug logs.

## Development Roadmap

- **Version 1.4.0:** Full support for IPv6.
- **Additional APIs:** Support for more DNS providers.
- **Enhanced Logging:** Improved log management and filters.

## Contributing

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
Stay tuned for updates and improvements to make FlexiDNS even more powerful and versatile!
