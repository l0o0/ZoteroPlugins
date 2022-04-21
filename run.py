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


def getDesc(url):
    try:
        resp = requests.get(url)
        out = re.findall("<em:description>(.*?)</em:description>", resp.text)
        return sorted(out)[-1]
    except:
        return "插件简介获取异常"

#####################################################################
# Main code

# Create plugins folder
if not os.path.isdir("plugins"):
    print("Create plugins folder")
    os.mkdir('plugins')

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

    # tag 
    tag = None

    # Download all version when plugin is added to source.txt, otherwise download the latest release
    if is_new:
        resp = requests.get(releases_url, headers=headers)
        # resp = requests.get(releases_url)
        json_datas = resp.json()
        # print(json_datas)
        for _i, json_data in enumerate(json_datas):
            if _i == 5:
                break
            download_url = json_data['assets'][0]['browser_download_url']
            update_time = datetime.strptime(json_data['assets'][0]['updated_at'], "%Y-%m-%dT%H:%M:%SZ")
            tag_name = json_data['tag_name']

            if last_update_time is None or last_update_time < update_time:
                last_update_time = update_time

            local_filename = getFielName(plugin_dir, download_url, tag_name)
            downloadFile(download_url, local_filename)
            if _i == 0:
                plugin[5] = os.path.basename(local_filename)
                tag = tag_name

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
        tag = tag_name
    

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
    with open("source.txt", 'w', encoding='utf-8') as handle:
        handle.writelines(source)

    # Add & commit source.txt
    os.system("git add source.txt")
    os.system("git commit -m 'Update source.txt %s'" % datetime.now())

    markdown = "# Zotero 插件下载\n\n"
    markdown += "自动更新于： `%s`，国内用户建议使用 Gitee 下载链接。插件间可能存在冲突，强烈建议按需获取安装\n\n" % datetime.now()
    markdown += "| 插件名 | 简介 |  最新版下载链接 | 更新时间 | GitHub链接 | 主页 |\n"
    markdown += "| ----- | ----- | ----- | ----- | ----- | ----- |\n"
    
    for plugin in new_plugins_source:
        if len(plugin[1]) > 20:
            desc = plugin[1]
        else:
            desc = getDesc(plugin[2].replace("github", "raw.githubusercontent")  + "/master/%s" % plugin[1])
        download_link_github = "https://github.com/l0o0/ZoteroPlugins/raw/main/plugins/%s/%s" % (plugin[0].replace(" ", '_').lower(), plugin[5])
        download_link_gitee = "https://gitee.com/zotero-chinese/zotero-plugins/raw/main/plugins/%s/%s" % (plugin[0].replace(" ", '_').lower(), plugin[5])
        markdown += "| %s | %s | %s [Github🔗](%s), [Gitee🔗](%s) | 📅`%s` | [💻](%s) | [🏠](%s) |\n" % (plugin[0], desc, tag, download_link_github, download_link_gitee, plugin[4], plugin[2], plugin[3])
    with open("docs/README.md", 'w', encoding='utf-8') as handle:
        handle.write(markdown)
    os.system("git add docs/README.md")
    os.system("git commit -m 'Update readme.md %s'" % datetime.now())
    os.system("git push origin main")
    
