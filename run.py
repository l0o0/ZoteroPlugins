import os
import requests

from datetime import datetime

# Get github token
token = os.getenv("TOKEN")
headers = {
    "authorization": "Bearer %s" % token,
    "content-type": "application/json"
}

# Read source.txt to a list
with open("source.txt") as handle:
    plugins = [_i.strip().split("|") for _i in handle.readlines() if not _i.startswith("#")]

# Loop all plugin in source.txt
new_plugins_source = []
update_flag = 0
for plugin in plugins:
    print(plugin)
    plugin_name = plugin[0].replace(" ", '_').lower()
    desc = plugin[1]
    repo_url = plugin[2]
    home_page = plugin[3]
    last_update_time = None if len(plugin) == 4 else datetime.strptime(plugin[4], "%Y-%m-%d %H:%M:%S")
    api_url = repo_url.replace("github.com", "api.github.com/repos/") + "releases/latest"
    print("%s %s" % (plugin_name, api_url))

    resp = requests.get(api_url, headers=headers)
    json_data = resp.json()
    download_url = json_data['assets'][0]['browser_download_url']
    update_time = datetime.strptime(json_data['assets'][0]['updated_at'], "%Y-%m-%dT%H:%M:%SZ")
    tag_name = json_data['tag_name']

    # Check update time, skip if latest version is downloaded
    if update_time <= last_update_time:
        print("Skip %s %s <= %s" % (plugin_name, update_time, last_update_time))
        new_plugins_source.append(plugin)
        continue

    # Update flag
    update_flag = 1

    # Create plugin dir
    plugin_dir = os.path.join("plugins", plugin_name)
    if not os.path.isdir(plugin_dir):
        print("Create dir %s" % plugin_dir)
        os.mkdir(plugin_dir)

    # Download file
    local_filename = os.path.join(plugin_dir, os.path.basename(download_url))
    if not tag_name in local_filename:
        local_filename = "%s_%s.xpi" % (local_filename.replace(".xpi", ""), tag_name)
    with requests.get(download_url, stream=True) as r:
        print("Downloading %s to %s" % (download_url, local_filename))
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192): 
                # If you have chunk encoded response uncomment if
                # and set chunk_size parameter to None.
                #if chunk: 
                f.write(chunk)
    plugin[4] = "%s" % update_time
    new_plugins_source.append(plugin)

    # Add & commit plugin
    os.system("git add %s")
    os.system("git commit -m 'Add %s'" % local_filename)

# Update source.txt
if update_flag == 1:
    source = ["|".join(_i) + '\n' for _i in new_plugins_source]
    with open("source.txt", 'w') as handle:
        handle.writelines(source)

    # Add & commit source.txt
    os.system("git add source.txt")
    os.system("git commit -m 'Update source.txt %s'" % datetime.now())
    os.system("git push origin main")
