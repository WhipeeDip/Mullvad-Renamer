import os
from os import listdir
from os.path import isfile, join
from bs4 import BeautifulSoup
import pycountry

# Configuration here
HTML_PATH = 'Servers _ Mullvad VPN.html' # https://mullvad.net/en/servers/#wireguard
CONFIG_PATH = 'mullvad-wireguard-configs' # path to directory with wireguard configs

def main():
    print('\n********** Make sure you read the README! **********\n')

    print('Parsing Mullvad server file. This can take some time...')
    server_dict = parse_mullvad_servers()

    print('Calculating renames...')
    rename_dict = calculate_renames(server_dict)
    success = rename_dict['success']
    failed = rename_dict['fail']

    print('File rename preview: ')
    print('Will be renamed: ')
    for rename in success:
        old = rename['old']
        new = rename['new']
        print(f'\t{old} => {new}')
    print('Cannot be renamed: ')
    for fail in failed:
        print(f'\t{fail}')
    if not failed:
        print('\tNo failures!')

    while True:
        input_continue = input('Y to continue, N to exit: ').strip().upper()
        if input_continue == 'Y':
            break
        elif input_continue == 'N':
            print('Exiting, no files were renamed.')
            exit()

    print('Renaming...')
    rename_files(success)

    print('\nDone!')

def parse_mullvad_servers():
    soup = BeautifulSoup(open(HTML_PATH, 'r', encoding = 'utf-8'), 'html.parser')
    table = soup.select_one('table.table.is-fullwidth.is-striped')
    tbody = table.find('tbody')
    rows = tbody.findChildren(['tr'])

    server_dict = {}
    for row in rows:
        tds = row.find_all('td')
        name = tds[0].get_text().split('-', 1)[0] # strip everything after first dash
        country = tds[1].get_text()
        city = tds[2].get_text().replace(', ', '')
        city = ''.join(city.split()) # strip all whitespace

        try:
            country_iso2 = pycountry.countries.search_fuzzy(country)[0].alpha_2
        except (IndexError, LookupError):
            print(f'Could not get country abbreviation for: {country}, using full name')
            country_iso2 = country

        server_dict[name] = {'country': country_iso2, 'city': city}

    return server_dict

def calculate_renames(server_dict):
    success = []
    fail = []

    files = [f for f in listdir(CONFIG_PATH) if isfile(join(CONFIG_PATH, f))]
    for file in files:
        try:
            server_name = file.split('mullvad-')[1].split('.conf')[0]
        except IndexError:
            print(f'\t{file} did not follow expected file format; skipping')
            fail.append(file)
            continue

        server_info = server_dict[server_name]
        country = server_info['country']
        city = server_info['city']
        insert_str = (f'-{country}_{city}')

        insert_index = file.find('-')
        if insert_index == -1:
            print(f'\t{file} did not follow expected file format; skipping')
            fail.append(file)
            continue

        new_name = file[:insert_index] + insert_str + file[insert_index:]
        success.append({'old': file, 'new': new_name})

    return {'success': success, 'fail': fail}

def rename_files(rename_dict):
    for rename in rename_dict:
        old = os.path.join(CONFIG_PATH, rename['old'])
        new = os.path.join(CONFIG_PATH, rename['new'])
        print (f'\tRenaming {old} to {new}...')
        os.rename(old, new)

# Check for main function execution
if __name__ == '__main__':
    main()