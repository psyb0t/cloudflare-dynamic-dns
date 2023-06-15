# cloudflare-dynamic-dns

cloudflare-dynamic-dns is a Python script used to automatically update the DNS A record for specified hostnames in Cloudflare with the current public IP of the machine on which the script is running.

This script is very useful when you have a machine with a dynamically allocated public IP address and want to keep your Cloudflare DNS records up to date for that machine.

The script continuously runs in a loop with a specified sleep time between each update.

## Requirements

1. Python 3
2. CloudFlare Python library - Can be installed via pip: `pip install cloudflare`
3. Public Internet connectivity to reach Cloudflare API and get public IP

## Configuration

You will need to specify some configuration settings in a `config.json` file located in the same directory as the script.

The following is a sample `config.json`:

```json
{
  "sleep_time_minutes": 10,
  "child_process_timeout": 5,
  "cf_user_email_address": "your-email@domain.com",
  "cf_api_token": "your-cloudflare-api-token",
  "hostnames": ["example1.com", "example2.com"]
}
```

Where:

- `sleep_time_minutes` is the number of minutes to sleep between each update.
- `child_process_timeout` is the number of minutes to wait for the child process to complete before it is terminated.
- `cf_user_email_address` is your Cloudflare account email address.
- `cf_api_token` is your Cloudflare API token.
- `hostnames` is a list of the hostnames for which the DNS A record needs to be updated.

## Usage

1. Clone this repository or download the Python script.
2. Install the required Python library using pip: `pip install cloudflare`.
3. Create a `config.json` file with your configuration settings in the same directory as the script.
4. Run the script with Python: `python3 cloudflare-dynamic-dns.py`.

The script will now continuously update your Cloudflare DNS A records for the specified hostnames with the current public IP address of the machine on which the script is running.

## Logging

The script logs all its activities to stdout with a timestamp, log level (INFO, ERROR), and the log message. You can redirect these logs to a file if you want to keep a record of them.

## Note

Use this script with caution. Depending on your Cloudflare plan and the number of DNS queries, continuous DNS record updates could potentially lead to rate limiting by Cloudflare.
