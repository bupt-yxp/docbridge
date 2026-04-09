class DocBridgeError(Exception):
    """库内错误基类。"""


class UnsupportedConversionError(DocBridgeError):
    """请求的源/目标格式组合未注册。"""


class ConversionFailedError(DocBridgeError):
    """转换过程失败。"""
