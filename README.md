# Zotero Plugins

Collections of Zotero Plugins

More detail in ...
[Gitee Page](https://zotero-chinese.gitee.io/zotero-plugins/#/)

## 如何提交没有收录的插件信息

[sources.json](https://github.com/l0o0/ZoteroPlugins/blob/main/sources.json) 记录着插件的信息，Github Action 机器人会每天定时读取该文件，下载最新的插件包，同步到仓库中。如果想添加新的插件，可以在`sources.json`添加下面的插件配置

```json
{
  "addon": "zotero-figure",  //插件名称
  "desc": "Zotero 图/表自动抓取插件",  // 插件介绍
  "repourl": "https://github.com/MuiseDestiny/zotero-figure",  // github 仓库地址
  "homepage": "https://github.com/MuiseDestiny/zotero-figure",  // 官网，一般是仓库地址
  "metafile": "package.json"  // addon/menifest.json 注意文件的相对路径
 }
```

其他信息插件版本、日期等，会在自动更新时由机器人自动添加，不必手动添加。
