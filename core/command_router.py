"""
core/command_router.py
根据解析到的意图，路由到对应技能模块执行
"""

import logging
from skills import weather, open_app, search_web, minecraft, unknown_handler

logger = logging.getLogger("kiki.router")

# 意图 → 处理函数映射表
# 新增技能只需在这里注册，无需修改其他代码
INTENT_MAP = {
    "weather":    weather.handle,
    "open_app":   open_app.handle,
    "search_web": search_web.handle,
    "mc_start":   minecraft.handle_start,
    "mc_stop":    minecraft.handle_stop,
    "mc_status":  minecraft.handle_status,
    "mc_cmd":     minecraft.handle_cmd,
    "unknown":    unknown_handler.handle,
}


class CommandRouter:
    def execute(self, intent: dict, original_text: str):
        """
        根据意图字典执行对应技能

        :param intent: {"intent": str, "target": str, "extra": str}
        :param original_text: 原始识别文字（用于 unknown 处理）
        """
        intent_name = intent.get("intent", "unknown")
        handler = INTENT_MAP.get(intent_name, unknown_handler.handle)

        logger.info(f"🔀 路由至: {intent_name}")
        try:
            handler(intent)
        except Exception as e:
            logger.error(f"技能执行失败 [{intent_name}]: {e}", exc_info=True)
