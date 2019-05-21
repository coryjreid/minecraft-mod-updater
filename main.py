import requests_cache
import copy
from constants import MODPACK_FILE, DATA_FILE, CHANGELOG_FILE, DOWNLOAD_FOLDER, NOW
from method_defs import *

# cache our request for 12 hours to keep from spamming the API
requests_cache.install_cache('request-cache', backend='sqlite', expire_after=43200)

if os.path.isfile(MODPACK_FILE):
    with open(MODPACK_FILE, 'r') as f:
        modpack = json.load(f)
else:
    print("ERROR: Cannot find " + MODPACK_FILE + ".")
    exit(1)

if os.path.isfile(DATA_FILE):
    print("Script previously run! Loading data from disk...", end=" ")
    data = pickle.load(open(DATA_FILE, 'rb'))
    print("Done!")

    print("Querying data from API...", end=" ")
    ids = get_modpack_mod_ids(modpack)
    latestMods = get_all_latest(ids)
    print("Done!")

    # some useful variables
    updatesMade = False
    latestVersion = max(data.keys(), key=(lambda k: k))
    previousMods = data[latestVersion]['mods']
    nextVersion = latestVersion + 1
    modsPendingUpdate = {}
    modsPendingRemoval = {}

    # identify any mods which need to be removed
    for modId, mod in previousMods.items():
        if modId not in latestMods:
            print(previousMods[modId]['modName'] + " has been removed.")
            modsPendingRemoval[modId] = copy.deepcopy(mod)

    # identify any mods which have updates
    for modId, mod in latestMods.items():
        if (modId not in previousMods) or (latestMods[modId]['lastDownloadedFileId'] > previousMods[modId]['lastDownloadedFileId']):
            print("Update necessary for " + latestMods[modId]['modName'])
            modsPendingUpdate[modId] = latestMods[modId]

    # update mods pending removal
    if len(modsPendingRemoval) > 0:
        updatesMade = True
        for modId, mod in modsPendingRemoval.items():
            del previousMods[modId]

    # update mods pending updates
    if len(modsPendingUpdate) > 0:
        updatesMade = True
        data[nextVersion] = {
            'date': str(NOW),
            'mods': copy.deepcopy(data[latestVersion]['mods'])
        }

        # download mods
        for modId, mod in modsPendingUpdate.items():
            if modId not in previousMods:
                data[nextVersion]['mods'][modId] = mod

            data[nextVersion]['mods'][modId]['lastDownloadedFileId'] = mod['lastDownloadedFileId']

            print("Getting download info for " + mod['modName'] + "...", end=" ")
            info = get_download_info(modId, mod['lastDownloadedFileId'])
            print("Done!")

            download_file(info['url'], DOWNLOAD_FOLDER + '\\'+str(nextVersion), info['nameOnDisk'])

    # finish up
    if updatesMade:
        # save data file
        save_data(data, DATA_FILE)

        print("Writing CHANGELOG...", end=" ")

        # write version header
        with open(CHANGELOG_FILE, "a+") as f:
            f.write('VERSION ' + str(nextVersion) + ':\n')

            # write entries for deleted mods
            for modId, mod in modsPendingRemoval.items():
                f.write('    REMOVED: ' + mod['modName'] + '\n')

            # write separator
            if len(modsPendingRemoval) > 0:
                f.write('    ----\n')

            # write entries for updated mods
            for modId, mod in modsPendingUpdate.items():
                f.write('    UPDATED: ' + mod['modName'] + '\n')

            # write separator for next time and close
            f.write('\n\n')

        print("Done!")

        print(str(len(modsPendingUpdate)) + " mods updated and " + str(len(modsPendingRemoval)) + " mods removed.")
    else:
        print("No updates were necessary.")
else:
    print("First run! Querying data from API...", end=" ")
    ids = get_modpack_mod_ids(modpack)
    all_mods = get_all_latest(ids)
    data = {
        1: {
            'date': str(NOW),
            'mods': all_mods
        }
    }
    print("Done!")

    save_data(data, DATA_FILE)

    # create changelog file
    with open(CHANGELOG_FILE, "a+") as f:
        f.write('VERSION 1:\n')

        print("Downloading latest version of all mods...")
        for modId, mod in all_mods.items():
            # add changelog entries
            f.write('    ADDED: ' + mod['modName'] + '\n')

            # download the file
            print("Getting download info for " + all_mods[modId]['modName'] + "...", end=" ")
            info = get_download_info(modId, mod['lastDownloadedFileId'])
            print("Done!")

            download_file(info['url'], DOWNLOAD_FOLDER + '\\v1', info['nameOnDisk'])

        # close the changelog
        f.write('\n\n')

print("Success!")
