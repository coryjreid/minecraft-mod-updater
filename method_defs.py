import requests
import pickle
import json
import os
from constants import HEADERS


def get_modpack_mod_ids(modpack):
    mods = []
    for mod in modpack['mods']:
        if len(mod['dependencies']) > 0:
            for d in mod['dependencies']:
                mods.append(d)

        mods.append(mod['id'])
    return set(mods)


def make_request(url, params):
    r = requests.get(url, headers=HEADERS, params=params)

    return json.loads(r.content)


def get_all_latest(ids):
    results = make_request('https://staging_cursemeta.dries007.net/api/v3/direct/addon', {'id': ids})

    mods = {}
    for mod in results:
        list_of_files = list(filter(lambda x: x['gameVersion'] == '1.12.2', mod['gameVersionLatestFiles']))
        sorted_list_of_files = sorted(list_of_files, key=lambda k: k['projectFileId'], reverse=True)

        mods[mod['id']] = {
            'modName': mod['name'],
            'lastDownloadedFileId': sorted_list_of_files[0]['projectFileId']
        }

    return mods


def get_download_info(modid, fileid):
    results = make_request(
        'https://staging_cursemeta.dries007.net/api/v3/direct/addon/files',
        {'addon': modid, 'file': fileid}
    )

    return {
        'nameOnDisk': results[str(modid)][0]['fileNameOnDisk'],
        'url': results[str(modid)][0]['downloadUrl']
    }


def download_file(url, filepath, filename):
    f = os.path.join(filepath, filename)
    os.makedirs(os.path.dirname(f), exist_ok=True)  # create directories if not exist

    if os.path.isfile(f):
        print("We already have " + f + " downloaded.")
    else:
        print("Downloading " + f + "...", end=" ")
        r = requests.get(url, allow_redirects=True)
        open(f, "wb").write(r.content)
        print("Done!")


def save_data(data, file):
    print("Storing updates to disk...", end=" ")
    pickle.dump(data, open(file, 'wb'))
    print("Done!")
