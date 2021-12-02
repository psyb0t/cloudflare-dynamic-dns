#!/usr/bin/env python3
import sys
import requests
import logging
import CloudFlare
import re
import time
import json
import os

logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

CONFIG_FILE = './config.json'

CONFIG = {
    'sleep_time_minutes': 0,
    'cf_user_email_address': '',
    'cf_api_token': '',
    'hostnames': [],
}


def read_config():
    global CONFIG

    with open(CONFIG_FILE, 'r') as f:
        config_data = json.load(f)

    CONFIG['sleep_time_minutes'] = config_data['sleep_time_minutes']
    CONFIG['child_process_timeout'] = config_data['child_process_timeout']
    CONFIG['cf_user_email_address'] = config_data['cf_user_email_address']
    CONFIG['cf_api_token'] = config_data['cf_api_token']
    CONFIG['hostnames'] = config_data['hostnames']


def get_public_ip():
    url = 'http://icanhazip.com'
    response = requests.get(url)

    if response.status_code != 200:
        return (None, 'could not get public ip [status code: %d]' % response.status_code)

    public_ip = response.text.strip()

    return public_ip, None


def get_domain_from_hostname(hostname):
    match = re.search(r'(?:(?:\.|)(?:[^\.]+)){2}$', hostname)
    if not match:
        return None, 'could not get domain from hostname %s' % hostname

    domain = match[0].lstrip('.').lower()

    return domain, None


def perform_job():
    cloudflare = CloudFlare.CloudFlare(
        email=CONFIG['cf_user_email_address'], token=CONFIG['cf_api_token'])

    logging.info('getting public ip...')

    public_ip, err = get_public_ip()
    if err is not None:
        logging.error(err)

        return

    logging.info('got public ip %s' % public_ip)

    for hostname in CONFIG['hostnames']:
        logging.info('processing hostname %s' % hostname)

        cf_dns_record_data = {
            'name': hostname,
            'type': 'A',
            'content': public_ip,
            'proxied': True
        }

        domain, err = get_domain_from_hostname(hostname)
        if err is not None:
            logging.error(err)

            continue

        logging.info('getting zone for domain %s' % domain)

        try:
            zones = cloudflare.zones.get(params={'name': domain})
        except Exception as e:
            logging.error(
                'exception on getting zones for domain %s - %s' % (domain, e.message))

            continue

        if not zones:
            logging.error(
                'no zone data for domain %s(hostname %s)' % (domain, hostname))

            continue

        zone = zones[0]

        try:
            zone_dns_a_records = cloudflare.zones.dns_records.get(
                zone['id'], params={'name': hostname, 'type': 'A'})
        except:
            logging.error(
                'exception on getting zone dns A records for domain %s - %s' % (domain, e.message))

            continue

        if zone_dns_a_records:
            zone_dns_a_record = zone_dns_a_records[0]

            if zone_dns_a_record['content'] == public_ip:
                logging.info(
                    'hostname %s already has the current public ip set' % hostname)

                continue

            logging.info(
                'updating existing dns A record for %s' % hostname)

            cf_dns_record_data['proxied'] = zone_dns_a_record['proxied']

            try:
                result = cloudflare.zones.dns_records.put(
                    zone['id'], zone_dns_a_record['id'], data=cf_dns_record_data)

                if not result:
                    logging.error(
                        'could not update existing dns A record for %s' % hostname)
            except Exception as e:
                logging.error(
                    'exception on updating existing dns A record for %s - %s' % (hostname, e.message))

            continue

        logging.info('inserting new dns A record for %s' % hostname)

        try:
            result = cloudflare.zones.dns_records.post(
                zone['id'], data=cf_dns_record_data)

            if not result:
                logging.error(
                    'could not insert dns A record for %s' % hostname)
        except Exception as e:
            logging.error(
                'exception on inserting dns A record for %s - %s' % (hostname, e.message))

        continue


def main():
    while True:
        logging.info('reading config file...')

        read_config()

        pid = os.fork()
        if pid == 0:
            logging.info('child process start')

            perform_job()

            logging.info('child process end')

            os._exit(0)
        else:
            logging.info('created child process %d' % pid)

            logging.info('allowing child to run for max %d minutes' %
                         CONFIG['child_process_timeout'])

            wait_time = 0
            while True:
                if wait_time >= 60 * CONFIG['child_process_timeout']:
                    logging.info(
                        'killing child process %d due to timeout' % pid)

                    os.kill(pid, 9)

                    os.waitpid(pid, 0)

                    break

                wpid, wsts = os.waitpid(pid, os.WNOHANG)
                if wpid != 0:
                    break

                wait_time += 1
                time.sleep(1)

        logging.info('sleeping for %d minutes' % CONFIG['sleep_time_minutes'])

        time.sleep(60 * CONFIG['sleep_time_minutes'])


main()
