class EchoPlugin:
    plugin_id = "echo"

    def __init__(self, configuration=None):
        self.configuration = dict(configuration or {})
        self.closed = False

    def health_check(self, context):
        return context.session_id.startswith("RUN-")

    def execute(self, payload, context):
        return {
            "payload": payload,
            "prefix": self.configuration.get("prefix", ""),
            "session_id": context.session_id,
        }

    def close(self):
        self.closed = True


class UnhealthyPlugin:
    plugin_id = "unhealthy"

    def health_check(self, context):
        return False

    def execute(self, payload, context):
        return payload


class WrongIdPlugin:
    plugin_id = "wrong"

    def execute(self, payload, context):
        return payload


class InvalidPlugin:
    plugin_id = "invalid"
