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
    fieldNum = 7
    with open("source.txt", encoding='utf-8') as handle:
        plugins = [_i.strip().split("|") for _i in handle.readlines() if not _i.startswith("#") and _i.strip()]
    plugins = [_i + [None] * (fieldNum - len(_i)) if len(_i) != fieldNum else _i for _i in plugins]
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

    # Download all version when plugin is added to source.txt, otherwise download the latest release
    if is_new:
        resp = requests.get(releases_url, headers=headers)
        # resp = requests.get(releases_url)
        json_datas = resp.json()
        # print(json_datas)
        for _i, json_data in enumerate(json_datas):
            if _i == 2:
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
    plugin[6] = tag_name
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
    markdown += "自动更新于： `%s`，国内用户建议使用 国内镜像Gitee 下载链接。插件间可能存在冲突，强烈建议按需获取安装\n\n" % datetime.now()
    markdown += "Zotero Connector 谷歌浏览器插件安装文件[下载地址](https://crxdl-1257117300.file.myqcloud.com/crx0795607d11df537/ekhagklcjbdpajgpjgmbionohlpdbjgc_v5.0.97.zip), 谷歌浏览器插件手动[安装教程](https://zhuanlan.zhihu.com/p/80305764)\n\n"
    markdown += "Android 客户端Zoo for Zotero[下载地址](https://gitee.com/zotero-chinese/zotero-plugins/raw/main/zooforzotero_43_apps.evozi.com.apk)\n\n"
    markdown += "Zotero 中文插件群（1群已满，请加2群)： 1群 913637964， 2群 617148016， 3群 962963257, 4群 893963769。独学而无友，则孤陋而寡闻\n\n"
    markdown += "| 插件名 | 简介 |  最新版下载链接 | 更新时间 | GitHub链接 | 主页 |\n"
    markdown += "| ----- | ----- | ----- | ----- | ----- | ----- |\n"
    
    for plugin in new_plugins_source:
        if len(plugin[1]) > 20:
            desc = plugin[1]
        else:
            desc = getDesc(plugin[2].replace("github", "raw.githubusercontent")  + "/master/%s" % plugin[1])
        download_link_github = "https://github.com/l0o0/ZoteroPlugins/raw/main/plugins/%s/%s" % (plugin[0].replace(" ", '_').lower(), plugin[5])
        download_link_gitee = "https://gitee.com/zotero-chinese/zotero-plugins/raw/main/plugins/%s/%s" % (plugin[0].replace(" ", '_').lower(), plugin[5])
        markdown += "| %s | %s | %s [官方🔗](%s), [国内镜像🔗](%s) | 📅`%s` | [💻](%s) | [🏠](%s) |\n" % (plugin[0], desc, plugin[6], download_link_github, download_link_gitee, plugin[4], plugin[2], plugin[3])
    with open("docs/README.md", 'w', encoding='utf-8') as handle:
        handle.write(markdown)
    os.system("git add docs/README.md")
    os.system("git commit -m 'Update readme.md %s'" % datetime.now())
    os.system("git push origin main")
    
