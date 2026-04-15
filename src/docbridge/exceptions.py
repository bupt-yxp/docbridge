class DocBridgeError(Exception):
    pass


class UnsupportedConversionError(DocBridgeError):
    pass


class ConversionFailedError(DocBridgeError):
    pass
