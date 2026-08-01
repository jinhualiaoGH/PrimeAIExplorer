class KernelError(RuntimeError): pass
class ConfigurationError(KernelError): pass
class ValidationError(KernelError): pass
class RunnerError(KernelError): pass
class BenchmarkError(RunnerError): pass
class ConnectorError(RunnerError): pass
