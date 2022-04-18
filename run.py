from base64 import encode
import re
import os
import requests

from datetime import datetime

# Get github token
def getToken():
    token = os.getenv("TOKEN")
    return {
        "authorization": "Bearer %s" % token,
        "content-type": "application/json"
    }

# Read source.txt to a list
def readSource():
    with open("source.txt", encoding='utf-8') as handle:
        plugins = [_i.strip().split("|") for _i in handle.readlines() if not _i.startswith("#")]
    plugins = [_i + [None, None] if len(_i) == 4 else _i for _i in plugins]
    return plugins


# Create plugin dir
def createPluginFolder(plugin_dir):
    if not os.path.isdir(plugin_dir):
        print("Create dir %s" % plugin_dir)
        os.mkdir(plugin_dir)
        return True
    else:
        return False

# Download release file 
def downloadFile(download_url, local_filename):
    print("Downloading %s to %s" % (download_url, local_filename))
    with requests.get(download_url, stream=True, headers=headers) as r:
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024): 
                f.write(chunk)

def getFielName(plugin_dir, download_url, tag_name):
    local_filename = os.path.join(plugin_dir, os.path.basename(download_url))
    if not re.sub("[vV]", '', tag_name) in local_filename:
        local_filename = "%s_%s.xpi" % (local_filename.replace(".xpi", ""), tag_name)
    return local_filename

#####################################################################
# Main code

# Loop all plugins in source.txt
plugins = readSource()
new_plugins_source = []
update_flag = 0
headers = getToken()
for plugin in plugins:
    print(plugin)
    plugin_name = plugin[0].replace(" ", '_').lower()
    desc = plugin[1]
    repo_url = plugin[2]
    home_page = plugin[3]
    last_update_time = None if plugin[4] is None else datetime.strptime(plugin[4], "%Y-%m-%d %H:%M:%S")
    api_url = repo_url.replace("github.com", "api.github.com/repos") + "/releases/latest"  # Latest release
    releases_url = api_url[:-7]  # All releases
    plugin_dir = os.path.join("plugins", plugin_name)
    print("%s starts ..." % (plugin_name))

    # Create folder for added plugin
    is_new = createPluginFolder(plugin_dir)

    # Download all version when plugin is added to source.txt, otherwise download the latest release
    if is_new:
        resp = requests.get(releases_url, headers=headers)
        # resp = requests.get(releases_url)
        json_datas = resp.json()
        print(json_datas)
        for _i, json_data in enumerate(json_datas):
            if _i == 0:
                plugin[5] = os.path.basename(local_filename)

            download_url = json_data['assets'][0]['browser_download_url']
            update_time = datetime.strptime(json_data['assets'][0]['updated_at'], "%Y-%m-%dT%H:%M:%SZ")
            tag_name = json_data['tag_name']

            if last_update_time is None or last_update_time < update_time:
                last_update_time = update_time

            local_filename = getFielName(plugin_dir, download_url, tag_name)
            downloadFile(download_url, local_filename)

        os.system("git add %s" % os.path.join("plugins", plugin_name))
        os.system("git commit -m 'Add %s'" % plugin_name)
       
    else:
        resp = requests.get(api_url, headers=headers)
        # resp = requests.get(api_url)
        json_data = resp.json()
        download_url = json_data['assets'][0]['browser_download_url']
        update_time = datetime.strptime(json_data['assets'][0]['updated_at'], "%Y-%m-%dT%H:%M:%SZ")
        tag_name = json_data['tag_name']

        # Check update time, skip if latest version is downloaded
        if last_update_time >= update_time:
            print("Skip %s %s <= %s" % (plugin_name, update_time, last_update_time))
            new_plugins_source.append(plugin)
            continue

        last_update_time = update_time
        local_filename = getFielName(plugin_dir, download_url, tag_name)
        downloadFile(download_url, local_filename)
        os.system("git add %s" % local_filename)
        os.system("git commit -m 'Add %s'" % local_filename)
        plugin[5] = os.path.basename(local_filename)
    

    # Update flag
    update_flag = 1
    
    plugin[4] = "%s" % last_update_time
    new_plugins_source.append(plugin)

    # Add & commit plugin
    os.system("git add %s" % local_filename)
    os.system("git commit -m 'Add %s'" % local_filename)


# Update source.txt and markdown file
if update_flag == 1:
    source = ["|".join(_i) + '\n' for _i in new_plugins_source]
    with open("source.txt", 'w') as handle:
        handle.writelines(source, encoding='utf-8')

    # Add & commit source.txt
    os.system("git add source.txt")
    os.system("git commit -m 'Update source.txt %s'" % datetime.now())

    markdown = "# Zotero 插件下载\n\n"
    markdown += "自动更新于： `%s`\n\n" % datetime.now()
    markdown += "| 插件名 | 简介 |  最新版下载链接 | 更新时间 | GitHub链接 | 主页 |\n"
    markdown += "| ----- | ----- | ----- | ----- | ----- | ----- |\n"
    
    for plugin in new_plugins_source:
        download_link = "https://cdn.jsdelivr.net/gh/l0o0/ZoteroPlugin@main/plugins/%s/%s" % (plugin[0], plugin[5])
        markdown += "| %s | %s | [🔗](%s) | 📅%s | [💻](%s) | [🏠](%s) |\n" % (plugin[0], plugin[1], download_link, plugin[4], plugin[2], plugin[3])
    with open("readme.md", 'w') as handle:
        handle.write(markdown, encoding='utf-8')
    os.system("git add readme.md")
    os.system("git commit -m 'Update readme.md %s'" % datetime.now())
    os.system("git push origin main")
    