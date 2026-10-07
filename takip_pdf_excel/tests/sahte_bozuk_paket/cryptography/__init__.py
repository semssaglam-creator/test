# Sahada görülen arızanın taklidi: sistemdeki cryptography yüklenirken
# ImportError DEĞİL, BaseException (pyo3 PanicException) fırlatıyor.
class PanicException(BaseException):
    pass


raise PanicException("Python API call failed (sahte)")
