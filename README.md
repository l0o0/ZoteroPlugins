# Zotero Plugins

Collections of Zotero Plugins

More detail in ...
[Zotero中文社区插件汇总](https://zoteroplugins.netlify.app/#/)

## 如何提交没有收录的插件信息

[sources.json](https://github.com/l0o0/ZoteroPlugins/blob/main/sources.json) 记录着插件的信息，Github Action 机器人会每天定时读取该文件，下载最新的插件包，同步到仓库中。如果想添加新的插件，可以在`sources.json`添加下面的插件配置，只需要添加`name`和`repo`信息

```json
{
  "name": "zotero-figure",  //插件名称
  "repo": "https://github.com/MuiseDestiny/zotero-figure"  // github 仓库地址
 }
```

其他信息插件版本、日期等，会在自动更新时由机器人自动添加，不必手动添加。
