# ncatbot-JMComicPlugins
在NcatBot上运行的JMComic插件

一个比较简单的JMComic插件

### 环境要求

- Python 3.13+

#### 安装依赖

pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple

[你会需要ncatbot的文档](https://docs.ncatbot.xyz/)

## 项目结构
```
ncatbot-JMComicPlugins/
├── config.yaml              # ncatbot init 自动生成的配置文件
├── main.py                  # 启动入口(可选，也可直接用 ncatbot run)
├── plugins/                 # 插件目录
│   ├── hello_world/         # 测试用插件(可卸载)
│   │   ├── manifest.toml
│   │   └── plugin.py
│   └── BilibiliParser/      # JMComic插件
│       ├── manifest.toml
│       ├── option.yml
│       └── plugin.py
└── requirements.txt
```

## 插件可用指令

1. 下载本子：发送命令 /jm 本子ID，例如 /jm 123456
2. 搜索本子：发送命令 /jm_search <关键词> [页码]，例如 /jm_search 画师A 2
3. 预览本子：发送命令 /jm_preview 本子ID，例如 /jm_preview 123456
4. 帮助信息：发送命令 /jm_help

[JmComic详细文档](https://jmcomic.readthedocs.io/zh-cn/latest/)

## 鸣谢
[NcatBot](https://github.com/ncatbot/NcatBot)
[JMComic-Crawler-Python](https://github.com/hect0x7/JMComic-Crawler-Python)
