from ncatbot.plugin import NcatBotPlugin
from ncatbot.core import registrar
from ncatbot.event.qq import GroupMessageEvent
from ncatbot.utils import get_log

LOG = get_log("HelloWorld")

class HelloWorldPlugin(NcatBotPlugin):
    name = "hello_world"
    version = "1.0.0"

    async def on_load(self):
        LOG.info("HelloWorld 插件已加载！")

    async def on_close(self):
        LOG.info("HelloWorld 插件已卸载。")

    @registrar.on_group_command("hello", ignore_case=True)
    async def on_group_hello(self, event: GroupMessageEvent):
        await event.reply(text="Hello from plugin!")