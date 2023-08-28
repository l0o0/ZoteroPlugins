from base64 import encode
import json
import re
import os
import requests
import zipfile

from datetime import datetime, timedelta

# Get github token


def getToken():
    token = os.getenv("TOKEN")
    if token:
        return {
            "authorization": "Bearer %s" % token,
            "content-type": "application/json"
        }
    else:
        return None

# Read sources.json to a list
def readSource():
    with open("sources.json", encoding='utf-8') as handle:
        plugins = json.load(handle)
    return plugins


# Create plugin dir
def createPluginFolder(plugin_dir):
    created = False
    if not os.path.isdir(plugin_dir):
        print("Create dir %s" % plugin_dir)
        os.mkdir(plugin_dir)
        created = True
    if not os.path.isdir(os.path.join(plugin_dir, 'pre')):
        print("Create dir %s" % os.path.join(plugin_dir, 'pre'))
        os.mkdir(os.path.join(plugin_dir, 'pre'))
        created = True
    return created


def getDownloadUrl(asserts):
    if asserts:
        download_url = asserts[0]['browser_download_url']
    else:
        return None
    if asserts[0]['content_type'] == "application/x-xpinstall":
        print("Download url: %s" % download_url)
        return download_url
    else:
        return None

# Download release file


def downloadFile(download_url, local_filename):
    print("Downloading %s to %s" % (download_url, local_filename))
    with requests.get(download_url, stream=True, headers=headers) as r:
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                f.write(chunk)


def getFielName(plugin_dir, download_url, tag_name, pre=False):
    if pre:
        plugin_dir = os.path.join(plugin_dir, 'pre')
    local_filename = os.path.join(plugin_dir, os.path.basename(download_url))
    if not re.sub("[vV]", '', tag_name) in local_filename:
        local_filename = "%s_%s.xpi" % (
            local_filename.replace(".xpi", ""), tag_name)
    return local_filename


def readMetadata(zfile, tags):
    info = {}
    metafile = 'manifest.json' if 'zotero7' in tags else 'install.rdf'
    data = zfile.read(metafile).decode('utf-8')
    if metafile.endswith("rdf"):
        idm1 = re.search('em:id="(.*?)"', data)
        idm2 = re.search("<em:id>(.*?)</em:id>", data)
        if idm1 or idm2:
            info['id'] = idm1.groups()[0] if idm1 else idm2.groups()[0]
        authorm1 = re.search('em:creator="(.*?)"', data)
        authorm2 = re.search("<em:creator>(.*?)</em:creator>", data)
        if authorm1 or authorm2:
            info['author'] = authorm1.groups()[0] if authorm1 else authorm2.groups()[0]
        descm = re.findall("<em:description>(.*?)</em:description>", data)
        descm.sort(reverse=True)
        if descm:
            info['description'] = descm[0]        
    else:
        manifest = json.loads(data)
        info['id'] = manifest['applications']['zotero']['id']
        info['author'] = manifest.get('author', '---')
        info['description'] = manifest.get('description', '---')
    return info

def checkCapVersion(zfile):
    tags = []
    if ('install.rdf') in zfile.namelist():
        tags.append('zotero6')
    if ('manifest.json') in zfile.namelist():
        tags.append('zotero7')
    return tags

#####################################################################
# Main code


# Create plugins folder
if not os.path.isdir("plugins"):
    print("Create plugins folder")
    os.mkdir('plugins')

# Loop all plugins in sources.json
plugins = readSource()
new_plugins_source = []
update_flag = 1
headers = getToken()

for plugin in plugins:
    print("Begin ...")
    print(plugin)
    # 跳过 Z7 插件信息，直接由 Z6 信息生成
    if plugin.get('id') and plugin.get('id').startswith('zotero7'):
        print("Skip {0}, a zotero7 addon".format(plugin['name']))
        continue

    plugin_dir = os.path.join("plugins", re.sub("\s", "_", plugin['name']))
    createPluginFolder(plugin_dir)
    latest_url = plugin['repo'].replace(
        "github.com", "api.github.com/repos") + "/releases/latest"  # Latest release
    all_url = plugin['repo'].replace(
        "github.com", "api.github.com/repos") + "/releases"  # All release
    # Keep the latest verion and remove the old.
    resp = requests.get(latest_url, headers=headers)
    pre_resp = requests.get(all_url, headers=headers)
    total_download = sum([r['assets'][0]['download_count'] for r in pre_resp.json() if r['assets']])
    pre_datas = sorted(filter(
        lambda i: i['prerelease'], pre_resp.json()), key=lambda i: i['created_at'], reverse=True)
    
    latest_data = resp.json()
    pre_data = pre_datas[0] if pre_datas else None  # 可能就没有预览版

    # 最新版下载 版本不一致，开始更新
    # Zotero 6 与 Zotero 7 的插件看成是两个插件，不过要生成配置文件时，目前只需要Zotero6的
    # Zotero 7 的插件主要查看预览版
    download_url = getDownloadUrl(latest_data['assets'])
    if latest_data['tag_name'] != plugin.get("version", None) and download_url:
        print("Zotero 6 start {0}".format(plugin['name']))
        plugin['version'] = latest_data['tag_name']
        plugin['updatedAt'] = latest_data['created_at']
        plugin['xpiDownloadUrl'] = download_url
        local_filename = getFielName(plugin_dir, download_url, plugin['version'])
        plugin['filename'] = local_filename
        downloadFile(download_url, local_filename)
        cmdstr = 'ls {0} | grep -xv "{1}" | xargs -i rm {0}/{{}}'.format(
            plugin_dir, os.path.basename(local_filename))
        os.system(cmdstr)
        plugin['downloadCount'] = total_download
        # Read metadata from zipfile
        zfile = zipfile.ZipFile(local_filename, 'r')
        plugin['tags'] = checkCapVersion(zfile)
        info = readMetadata(zfile, plugin['tags'])
        print("Zotero 6 metadata {0}".format(plugin['name']))
        print(info)
        plugin.update(info)
        # 根据不同的版本适配，为ID 加上前缀
        if plugin['tags'] == ['zotero6']: 
            plugin['id'] = 'zotero6' + plugin['id']
        elif plugin['tags'] == ['zotero7']:
            plugin['id'] = 'zotero7' + plugin['id']
        
        update_flag = 1
        print("Zotero 6 done {0}".format(plugin['name']))
        

    # 预览版如果只适配6，则跳过
    # 
    download_url = getDownloadUrl(pre_data['assets']) if pre_data else None
    print(download_url, plugin['tags'])
    if download_url and 'zotero7' not in plugin['tags']: # 如果正式版已经有Z7，则不需要更新预览版
        local_filename = getFielName(os.path.join(plugin_dir, 'pre'), download_url, pre_data['tag_name'])
        downloadFile(download_url, local_filename)
        cmdstr = 'ls {0} | grep -xv "{1}" | xargs -i rm {0}/{{}}'.format(
            os.path.join(plugin_dir, 'pre'), os.path.basename(local_filename))
        os.system(cmdstr)
        zfile = zipfile.ZipFile(local_filename, 'r')
        tags = checkCapVersion(zfile)
        z7id = 'zotero7' + plugin['id'].replace('zotero6', '')
        z7plugin = [_i for _i in plugins if _i.get('id') == z7id]
        z7ver = z7plugin[0]['version'] if z7plugin else None
        print(tags, z7ver, pre_data['tag_name'])
        if tags == ['zotero7'] and z7ver != pre_data['tag_name']:
            print("Zotero 7 start {0}".format(plugin['name']))
            z7plugin = {"name": plugin["name"]}
            info = readMetadata(zfile, tags)
            print(info)
            z7plugin.update(info)
            z7plugin['id'] = z7id
            z7plugin['version'] = pre_data['tag_name']
            z7plugin['updatedAt'] = pre_data['created_at']
            z7plugin['downloadCount'] = total_download
            z7plugin['tags'] = tags
            z7plugin['xpiDownloadUrl'] = download_url
            z7plugin['filename'] = local_filename
            z7plugin['repo'] = plugin['repo']

            update_flag = 1
            print("Zotero 7 done {0}".format(z7plugin['name']))
    print("Add to new plugins source")
    new_plugins_source.append(plugin)
    # Add & commit plugin
    os.system("git add %s" % plugin_dir)
    os.system("git commit -m 'update %s'" % plugin['name'])

print("All sources, {0}, update status {1}".format(len(new_plugins_source), update_flag))
new_plugins_source.sort(key= lambda p : p['updatedAt'], reverse=True)
print(new_plugins_source)

# testing
# Update sources.json and markdown file
if update_flag == 1:
    delta = timedelta(hours=8)
    markdown = "# Zotero 插件下载\n\n"
    markdown += "# 💥💥 插件后台更新维护中 ....\n"
    markdown += "自动更新于： `%s`，国内用户建议使用 **国内镜像** 下载链接。插件间可能存在冲突，强烈建议按需获取安装\n\n" % (datetime.now() + delta)
    crxurl = "https://crxdl-1257117300.file.myqcloud.com/crx0795607d11df537/ekhagklcjbdpajgpjgmbionohlpdbjgc_v5.0.97.zip"
    crxhelp = "https://zhuanlan.zhihu.com/p/80305764"
    # apkurl = "https://gitee.com/zotero-chinese/zotero-plugins/raw/main/zooforzotero_43_apps.evozi.com.apk"
    apkurl = "https://ftp.linxingzhong.top/zooforzotero_43_apps.evozi.com.apk"
    markdown += "Zotero Connector 谷歌浏览器插件安装文件[下载地址]({0}), 谷歌浏览器插件手动[安装教程]({1})\n\n".format(
        crxurl, crxhelp)
    markdown += "Android 客户端Zoo for Zotero[下载地址]({0})\n\n".format(apkurl)
    markdown += """微信公众号：学术废物收容所 <button onclick="document.getElementById('show_image_popup').style.display='block'">扫码加入</button>
<div id="show_image_popup" style="display: none; position: absolute; top: 10%; left: 50%; z-index: 1000; transform: translate(-50%, -50%);">
  <div class="close-btn-area" style="text-align: right;max-width: 80%;">
    <button id="close-btn" style='color:red;' onclick="document.getElementById('show_image_popup').style.display='none'">X</button> 
  </div>
  <div id="image-show-area" style="max-width: 80%;">
    <img id="large-image" alt="" src="./wechat.jpg">
  </div>
</div>"""
    markdown += "Zotero 中文插件群913637964，617148016，893963769，666489129，145248977，317995116，962963257（加一个群即可）。独学而无友，则孤陋而寡闻\n\n"
    markdown += "| 插件名 | 简介 |  Zotero6 | 更新时间(z6) | Zotero7 | 更新时间(z7) | GitHub链接 |\n"
    markdown += "| ----- | ----- | ----- | ----- | ----- | ----- | ----- |\n"

    github_url = "https://github.com/l0o0/ZoteroPlugins/raw/main/plugins"
    # home_url = "https://gitee.com/zotero-chinese/zotero-plugins/raw/main/plugins"
    home_url = "https://ftp.linxingzhong.top/"
    for _i, plugin in enumerate(new_plugins_source):
        if plugin['id'].startswith("zotero7"):
            continue
        print("Writing md, {0} {1}".format(_i, plugin['name']))
        z7plugin = [_p for _p in new_plugins_source if _p['id'] == ("zotero7" + plugin['id'].replace("zotero6", ''))]
        z7plugin = z7plugin[0] if z7plugin else {}
        print(z7plugin)

        download_link_github = plugin['xpiDownloadUrl']
        download_link_gitee = home_url + plugin['filename']
        z7download_link_github = z7plugin.get("xpiDownloadUrl")
        z7download_link_gitee = home_url + z7plugin.get('filename') if z7plugin.get("filename") else None
        if z7plugin:
            z7str = "%s [官方🔗](%s), [国内镜像🔗](%s)" % (z7plugin.get("version", ""), z7download_link_github, z7download_link_gitee
)
            z7updatet = z7plugin.get('updatedAt')
        elif 'zotero7' in plugin['tags'] :  # 6，7兼容就使用lastest 版本
             z7str = "%s [官方🔗](%s), [国内镜像🔗](%s)" % (plugin.get("version", ""), download_link_github, download_link_gitee)
             z7updatet = plugin.get('updatedAt')
        else:
            z7str = "---"
        print(z7plugin.get("name", None), z7str)
        markdown += "| %s | %s | %s [官方🔗](%s), [国内镜像🔗](%s) | `%s` | %s | `%s` | [🏠](%s) |\n" %\
            (plugin['name'], \
                plugin.get('description', '---'), \
                plugin.get('version', '---'), \
                download_link_github, \
                download_link_gitee, \
                plugin.get('updatedAt', '---'), \
                z7str, \
                '---' if z7str == '---' else z7updatet, \
                plugin['repo'])
    
    with open("docs/README.md", 'w', encoding='utf-8') as handle:
        handle.write(markdown)
    os.system("git add docs/README.md")
    os.system("git commit -m 'Update readme.md %s'" % datetime.now())

    with open("sources.json", 'w', encoding='utf-8') as handle:
        json.dump(new_plugins_source, handle, ensure_ascii=False, indent=True)
    # Add & commit sources.json
    os.system("git add sources.json")
    os.system("git commit -m 'Update sources.json %s'" % datetime.now())

    # 将以上更新结果推送到库里
    os.system("git push origin main")

