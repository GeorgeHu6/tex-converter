# tex-converter

## 运行方式

考虑到打包后文件巨大，因此建议以源码方式运行。（既然你都会用Latex了，那一定也会下面这些Python的基本操作了吧🤭）

1. 创建Python虚拟环境，并安装依赖

```bash
D:\your-folder> python -m venv tex_converter
D:\your-folder> .\tex_converter\Script\activate
(tex_converter) D:\your-folder\> pip install -r requirements.txt
```

2. 运行程序

```bash
(tex_converter) D:\your-folder\> python main.py
```

## 使用方式

### 界面介绍

![image](https://github.com/GeorgeHu6/tex-converter/assets/43069137/5465a1ff-9e62-4ba6-8184-8f2f8f81d3ef)

①：选择后台进程使用的浏览器（推荐使用Chrome），可以选择一个你电脑上已经安装过的浏览器

②：后台进程开关，在使用前请先点击打开

③：用于查看后台进程是否意外被终结（检测能力很弱，请不要特别相信这个功能）

④：LaTex公式书写区域

⑤：渲染LaTex公式

⑥：日志输出区域

⑦：LaTex公式显示区域

⑧：在需要复制的公式上右键，选择“复制为SVG”，然后就可以在Word、PPT等地方直接粘贴啦

### 操作步骤

1. 选择后台要使用的浏览器
2. 开启后台进程
3. 输入LaTex公式
4. 点击确认进行渲染
5. 右键复制公式
6. 粘贴到Word、PPT等地方

<small>（注：若公式显示为一个黑方块，说明LaTex写错了，请自行检查）</small>

## 待完善功能

- [ ] 错误提示输出
- [ ] 点击公式查看大图
- [ ] 托盘模式
- [ ] 免切换应用，直接从剪贴板读取LaTex，渲染后重新放到剪贴板
- [ ] 更多功能等你来提，有相关意见或建议可以在issues中提出，合理的会添加到这里

## 参与项目

1. 在issues中提出意见或建议
2. fork后进行开发，向本项目提出request
