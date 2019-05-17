import requests_cache
import copy
from constants import DATA_FILE, CHANGELOG_FILE, DOWNLOAD_FOLDER, NOW
from method_defs import *

# cache our request for 12 hours to keep from spamming the API
requests_cache.install_cache('request-cache', backend='sqlite', expire_after=43200)

if os.path.isfile(DATA_FILE):
    print("Script previously run! Loading data from disk...", end=" ")
    data = pickle.load(open(DATA_FILE, 'rb'))
    print("Done!")

    print("Querying data from API...", end=" ")
    latestMods = get_all_latest()
    print("Done!")

    # some useful variables
    latestVersion = max(data.keys(), key=(lambda k: k))
    previousMods = data[latestVersion]['mods']
    nextVersion = latestVersion + 0.1
    modsPendingUpdate = {}

    # identify any mods which have updates
    for modId, mod in previousMods.items():
        if latestMods[modId]['lastDownloadedFileId'] > previousMods[modId]['lastDownloadedFileId']:
            print("Update necessary for " + previousMods[modId]['modName'])
            modsPendingUpdate[modId] = latestMods[modId]

    # update mods with pending updates
    if len(modsPendingUpdate) > 0:
        data[nextVersion] = {
            'date': str(NOW),
            'mods': copy.deepcopy(data[latestVersion]['mods'])
        }

        # download mods
        for modId, mod in modsPendingUpdate.items():
            data[nextVersion]['mods'][modId]['lastDownloadedFileId'] = mod['lastDownloadedFileId']

            print("Getting download info for " + mod['modName'] + "...", end=" ")
            info = get_download_info(modId, mod['lastDownloadedFileId'])
            print("Done!")

            download_file(info['url'], DOWNLOAD_FOLDER + '\\'+str(nextVersion), info['nameOnDisk'])

        # save data file
        save_data(data, DATA_FILE)

        # update changelog
        f = open(CHANGELOG_FILE, "a+")
        f.write(str(nextVersion) + ':\n')

        for modId, mod in modsPendingUpdate.items():
            f.write('    ' + mod['modName'] + ' updated\n')

        f.write('\n\n')
        f.close()

        print(str(len(modsPendingUpdate)) + " mods updated.")
    else:
        print("No mods need updating.")
else:
    print("First run! Querying data from API...", end=" ")
    all_mods = get_all_latest()
    data = {
        1.0: {
            'date': str(NOW),
            'mods': all_mods
        }
    }
    print("Done!")

    save_data(data, DATA_FILE)

    # create changelog file
    f = open(CHANGELOG_FILE, "a+")
    f.write('1.0:\n')

    print("Downloading latest version of all mods...")
    for modId, mod in all_mods.items():
        # add changelog entries
        f.write('    ' + mod['modName'] + ' updated\n')

        # download the file
        print("Getting download info for " + all_mods[modId]['modName'] + "...", end=" ")
        info = get_download_info(modId, mod['lastDownloadedFileId'])
        print("Done!")

        download_file(info['url'], DOWNLOAD_FOLDER + '\\1.0', info['nameOnDisk'])

    # close the changelog
    f.write('\n\n')
    f.close()

print("Success!")
