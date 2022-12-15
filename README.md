# Zotero Plugins

Collections of Zotero Plugins

More detail in ...
[Gitee Page](https://zotero-chinese.gitee.io/zotero-plugins/#/)

## 如何提交没有收录的插件信息

[source.txt](https://github.com/l0o0/ZoteroPlugins/blob/main/source.txt) 记录着插件的信息，Github Action 机器人会每天定时读取该文件，下载最新的插件包，同步到仓库中。如果想添加新的插件，可以在`source.txt`中新建一行，各列以`|`分隔，需要补充的信息如下

`插件名称|插件介绍（如果有install.rdf请写明该文件在仓库中的相对路径）|项目github地址|项目主页地址（没有就填github地址）`

示例  
`zotero-reference|Zotero 参考文献自动抓取插件|https://github.com/MuiseDestiny/zotero-reference|https://github.com/MuiseDestiny/zotero-reference`

其他信息插件版本、日期等，会在自动更新时由机器人自动添加，不必手动添加。
