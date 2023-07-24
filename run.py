from base64 import encode
import json
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

# Read sources.json to a list
def readSource():
    with open("sources.json", encoding='utf-8') as handle:
        plugins = json.load(handle)
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
        if url.endswith("rdf"):
            out = re.findall("<em:description>(.*?)</em:description>", resp.text)
            return sorted(out)[-1]
        elif url.endswith("json"):
            package = json.loads(resp.text)
            return package.description
    except:
        return "----"

#####################################################################
# Main code

# Create plugins folder
if not os.path.isdir("plugins"):
    print("Create plugins folder")
    os.mkdir('plugins')

# Loop all plugins in sources.json
plugins = readSource()
new_plugins_source = []
update_flag = 0
headers = getToken()
for plugin in plugins:
    print(plugin)
    if len(plugin.get('desc', "")) == 0:
        desc = getDesc(plugin['repourl'].replace("github", "raw.githubusercontent")  + "/master/%s" % plugin['metafile'])
        plugin['desc'] = desc
    plugin_name = plugin['addon'].replace(" ", '_').lower()
    repo_url = plugin['repourl']
    home_page = plugin['homepage']
    last_update_time = None if plugin.get('updatetime') is None else datetime.strptime(plugin.get('updatetime'), "%Y-%m-%d %H:%M:%S")
    api_url = repo_url.replace("github.com", "api.github.com/repos") + "/releases/latest"  # Latest release
    # releases_url = api_url[:-7]  # All releases
    plugin_dir = os.path.join("plugins", plugin_name)
    print("%s starts ..." % (plugin_name))

    # Create folder for added plugin
    is_new = createPluginFolder(plugin_dir)

    # Keep the latest verion and remove the old.
    resp = requests.get(api_url, headers=headers)
    # resp = requests.get(api_url)
    json_data = resp.json()
    for asset in json_data['assets']:
        if asset['content_type'] == 'application/x-xpinstall':
            download_url = asset['browser_download_url']
            break
    update_time = datetime.strptime(json_data['assets'][0]['updated_at'], "%Y-%m-%dT%H:%M:%SZ")
    tag_name = json_data['tag_name']

    # Check update time, skip if latest version is downloaded
    if last_update_time != None and last_update_time >= update_time:
        print("Skip %s %s <= %s" % (plugin_name, update_time, last_update_time))
        new_plugins_source.append(plugin)
        continue

    last_update_time = update_time
    local_filename = getFielName(plugin_dir, download_url, tag_name)
    downloadFile(download_url, local_filename)
    # Remove old file 
    cmdstr = 'ls {0} | grep -xv "{1}" | xargs -i rm {0}/{{}}'.format(plugin_dir, os.path.basename(local_filename))
    os.system(cmdstr)
    os.system("git add %s" % local_filename)
    os.system("git commit -m 'Add %s'" % local_filename)
    plugin['filename'] = os.path.basename(local_filename)

    # Update flag
    update_flag = 1
    
    plugin['updatetime'] = "%s" % last_update_time
    plugin['version'] = tag_name
    print(plugin)
    new_plugins_source.append(plugin)

    # Add & commit plugin
    os.system("git add %s" % local_filename)
    os.system("git commit -m 'Add %s'" % local_filename)

print(new_plugins_source)
# Update sources.json and markdown file
if update_flag == 1:

    markdown = "# Zotero 插件下载\n\n"
    markdown += "自动更新于： `%s`，国内用户建议使用 **国内镜像** 下载链接。插件间可能存在冲突，强烈建议按需获取安装\n\n" % datetime.now()
    crxurl = "https://crxdl-1257117300.file.myqcloud.com/crx0795607d11df537/ekhagklcjbdpajgpjgmbionohlpdbjgc_v5.0.97.zip"
    crxhelp = "https://zhuanlan.zhihu.com/p/80305764"
    # apkurl = "https://gitee.com/zotero-chinese/zotero-plugins/raw/main/zooforzotero_43_apps.evozi.com.apk"
    apkurl = "http://95.169.23.195:18909/zooforzotero_43_apps.evozi.com.apk"
    markdown += "Zotero Connector 谷歌浏览器插件安装文件[下载地址]({0}), 谷歌浏览器插件手动[安装教程]({1})\n\n".format(crxurl, crxhelp)
    markdown += "Android 客户端Zoo for Zotero[下载地址]({0})\n\n".format(apkurl)
    markdown += "Zotero 中文插件群913637964，617148016，893963769，666489129，145248977，962963257（加一个群即可）。独学而无友，则孤陋而寡闻\n\n"
    markdown += "| 插件名 | 简介 |  最新版下载链接 | 更新时间 | GitHub链接 | 主页 |\n"
    markdown += "| ----- | ----- | ----- | ----- | ----- | ----- |\n"
    
    github_url = "https://github.com/l0o0/ZoteroPlugins/raw/main/plugins"
    # home_url = "https://gitee.com/zotero-chinese/zotero-plugins/raw/main/plugins"
    home_url = "http://95.169.23.195:18909/plugins"
    for _i, plugin in enumerate(new_plugins_source):
        new_plugins_source[_i]['desc'] = desc
        download_link_github = github_url + "/%s/%s" % (plugin['addon'].replace(" ", '_').lower(), plugin['filename'])
        download_link_gitee = home_url + "/%s/%s" % (plugin['addon'].replace(" ", '_').lower(), plugin['filename'])
        markdown += "| %s | %s | %s [官方🔗](%s), [国内镜像🔗](%s) | 📅`%s` | [💻](%s) | [🏠](%s) |\n" \
            % (plugin['addon'], desc, plugin['version'], download_link_github, download_link_gitee, plugin['updatetime'], plugin['repourl'], plugin['homepage'])
    with open("docs/README.md", 'w', encoding='utf-8') as handle:
        handle.write(markdown)
    os.system("git add docs/README.md")
    os.system("git commit -m 'Update readme.md %s'" % datetime.now())
    os.system("git push origin main")

    with open("sources.json", 'w', encoding='utf-8') as handle:
        json.dump(new_plugins_source, handle, ensure_ascii=False, indent=True)
    # Add & commit sources.json
    os.system("git add sources.json")
    os.system("git commit -m 'Update sources.json %s'" % datetime.now())
    
