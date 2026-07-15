# 该项目在不考虑异常事件处理的情况下能够稳定正常运行jmcomic库并进行搜索、预览、下载与发送本子(我用18年买的内存只有4个G的树莓派都可以跑)
# 如果你在使用过程中发现问题或有更好的实现方式请随意修改代码 ;)
# 你需要的文档有：https://docs.ncatbot.xyz/ 以及 https://jmcomic.readthedocs.io/zh-cn/latest/
# By: Thsine

import os
from typing import Optional

import jmcomic
from jmcomic import *
from ncatbot.core import registrar
from ncatbot.types import MessageArray
from ncatbot.plugin import NcatBotPlugin
from ncatbot.types.qq import ForwardConstructor
from ncatbot.event.qq import MessageEvent, GroupMessageEvent, PrivateMessageEvent

class JMComicPlugin(NcatBotPlugin):
    async def on_load(self):
        # 回到上级目录用于存放本子
        project_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../")
        )
        # 缓存目录
        self.base_dir = os.path.join(project_root, "image_cache")
        self.base_dir = os.path.join(project_root, "jmcomic_cache")
        # 导入参数配置
        config_path = os.path.join(os.path.dirname(__file__), "option.yml")
        self.jm_option = jmcomic.JmOption.from_file(config_path)

        os.makedirs(self.base_dir, exist_ok=True)
        self.logger.info(f"JMComicPlugin loaded. Base directory: {self.base_dir}")

    async def on_close(self):
        self.logger.info("JMComicPlugin closed.")

    # JMComic客户端实例，使用默认配置创建
    global client
    client = JmOption.default().new_jm_client()

    # 获取本子pdf的路径，用于检查是否已下载过该本子，避免重复下载
    def _pdf_path(self, album_id: str) -> str:
        return os.path.join(self.base_dir, f"{album_id}.pdf")
    
    # 下载本子方法
    async def _download_album(self, event: MessageEvent, album_id: str):
        pdf_path = self._pdf_path(album_id)
        try:
            await event.reply(text = f"开始下载本子 {album_id}")
            await self.jm_option.download_album_async([album_id], extra=Feature.export_pdf(filename_rule= 'Aid'))
            await self._send_file(event, pdf_path)
            
        except Exception as e:
            await event.reply(text = f"下载过程中发生错误: {str(e)}")

    # 发送文件方法
    async def _send_file(self, event: MessageEvent, file_path: str):
        file_name = os.path.basename(file_path)

        try:
            if isinstance(event, PrivateMessageEvent):
                await event.reply(text=f"正在上传: {file_name}")
                await self.api.qq.send_private_file(
                    user_id = event.user_id,
                    file = file_path,
                    name = file_name
                )

            elif isinstance(event, GroupMessageEvent):
                await event.reply(text=f"正在上传: {file_name}")
                await self.api.qq.send_group_file(
                    group_id = event.group_id,
                    file = file_path,
                    name = file_name
                )

        # 上传过程中可能发生错误，例如文件过大、网络问题等
        except Exception as e:
            await event.reply(text = f"文件较大，请稍等")

    # 搜索本子方法
    async def _search_albums(self, event: MessageEvent, keyword: str, _page: int):
        r_keyword = keyword.replace(",", " ")
        try:
            bot_id = str(event.self_id)
            # jmcomic客户端的搜索接口，返回一个分页对象，包含搜索结果和分页信息
            page: JmSearchPage = client.search_site(search_query = r_keyword, page = _page)
            if page.total == 0:
                await event.reply(text = "未找到相关本子")

            else:
                await event.reply(text = f"结果总数: {page.total}, 分页大小: {page.page_size}, 页数: {page.page_count}")
                # 构造内层转发消息，包含搜索结果列表
                inner_fc = ForwardConstructor(user_id = bot_id, nickname = "_")
                for album_id, title in page:
                    inner_fc.attach_text(f"[{album_id}]: {title}")
                inner_forward = inner_fc.build()
                # 构造外层转发消息，包含内层转发消息和一些提示文本
                outer_fc = ForwardConstructor(user_id = bot_id, nickname = "_")
                outer_fc.attach_text(f"关键词 {r_keyword} 第{_page}页")
                outer_fc.attach_text("——————搜索结果如下——————")
                outer_fc.attach_forward(inner_forward)
                # 构造完成后发送转发消息，根据消息类型选择私聊或群聊接口
                forward = outer_fc.build()
                if isinstance(event, PrivateMessageEvent):
                    await self.api.qq.post_private_forward_msg(event.user_id, forward)

                elif isinstance(event, GroupMessageEvent):
                    await self.api.qq.post_group_forward_msg(event.group_id, forward)

        except Exception as e:
            await event.reply(text = f"搜索过程中发生错误: {str(e)}")


    # 预览本子方法，返回本子标题和封面链接，供用户确认是否下载正确的本子
    async def _preview_album(self, event: MessageEvent, album_id: str) -> Optional[str]:
        try:
            page = client.search_site(search_query = album_id)
            album: JmAlbumDetail = page.single_album

            client.download_album_cover(album_id, f'./image_cache/{album_id}.png')

            # 构造外层转发消息，包含内层转发消息和一些提示文本
            outer_fc = ForwardConstructor(user_id = str(event.self_id), nickname = "_")

            # 图文混合接点
            msg = MessageArray()
            msg.add_image(f"./image_cache/{album_id}.png")
            msg.add_text(f"🖼{album.name}\n👍 {album.likes} 点击喜欢\n👀 {album.views} 次观看\n—作者: {album.authors}\n—标签: {album.tags}\n—简介: {album.description}")
            outer_fc.attach_message(msg)

            forward = outer_fc.build()
            if isinstance(event, PrivateMessageEvent):
                await self.api.qq.post_private_forward_msg(event.user_id, forward)

            elif isinstance(event, GroupMessageEvent):
                await self.api.qq.post_group_forward_msg(event.group_id, forward)

        except Exception as e:
            await event.reply(text = f"Error: {str(e)}")
            await event.reply(text = "请重试")


    # 以下为机器人接收命令并调用上述方法的部分
    # 下载命令，接收本子id参数，调用下载方法
    @registrar.qq.on_command("/jm")
    async def jm_download_cmd(self, event: MessageEvent, album_id: str) -> Optional[str]:
        pdf_path = self._pdf_path(album_id)
        # 优先检查本子是否存在
        try:
            album: JmAlbumDetail = client.get_album_detail(album_id) # 这行删掉会出问题

            # 检查本子文件是否存在缓存文件夹里
            if os.path.exists(pdf_path):
                await self._send_file(event, pdf_path)
            else:
                await self._download_album(event, album_id)

        except MissingAlbumPhotoException as e:
            await event.reply(text = f"请求的本子不存在\n原因可能为:\n1. 本子id有误\n2. 该本只对登录用户可见")
        except Exception as e:
            await event.reply(text = f"Error: {str(e)}")
 
    # 搜索命令，接收关键词和页码参数，调用搜索方法
    @registrar.qq.on_command("/jms")
    async def jm_search_cmd(self, event: MessageEvent, keyword: str, _page: Optional[int] = 1):
        await self._search_albums(event, keyword, _page)

    # 预览命令，接收本子id参数，返回本子标题和封面链接
    @registrar.qq.on_command("/jmp")
    async def jm_preview_cmd(self, event: MessageEvent, album_id: str):
        try:
            album: JmAlbumDetail = client.get_album_detail(album_id)
            
            await self._preview_album(event, album_id)

        except MissingAlbumPhotoException as e:
            await event.reply(text = f"请求的本子不存在\n原因可能为:\n1. 本子id有误\n2. 该本只对登录用户可见")
        except Exception as e:
            await event.reply(text = f"Error: {str(e)}")

    # 帮助命令，介绍插件的使用方法
    @registrar.qq.on_command("/jmh")
    async def jm_help_cmd(self, event: MessageEvent):
        help_text = (
            "JMComic 插件使用说明：\n"
            "1. 下载本子：发送命令 /jm 本子ID，例如 /jm 123456\n"
            "2. 搜索本子：发送命令 /jms <关键词> [页码]，例如 /jms 画师A 2\n"
            "-如果有多个关键词请用英文逗号分隔, 例如 /jms <关键词1,关键词2> 页码\n"
            "-搜索逻辑\n"
            "——碧蓝档案,+全彩 仅显示全彩且是碧蓝档案的本\n"
            "——碧蓝档案,-全彩  仅显示非全彩且是碧蓝档案的本\n"
            "——碧蓝档案,全彩   显示结果包含全彩及碧蓝档案的本\n"
            "3. 预览本子：发送命令 /jmp 本子ID，例如 /jmp 123456\n"
            "4. 帮助信息：发送命令 /jmh"
        )
        await event.reply(text = help_text)
