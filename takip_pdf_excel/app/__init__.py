import sys

SURUM = "1.1"


def _modulleri_sil(ad):
    for m in [m for m in sys.modules if m == ad or m.startswith(ad + ".")]:
        del sys.modules[m]


def pypdf_guvenli_yukle():
    """pypdf'i, sistemde kurulu BOZUK bir şifreleme paketine takılmadan yükler.

    pypdf varsa sistemdeki `cryptography`yi (yoksa `Crypto`yu) yükler ve yalnızca
    ImportError'u yakalar. Geliştirme makinesinde (Debian, python3.11) sistem
    `cryptography`si `_cffi_backend` eksik olduğu için Rust panic'i
    (BaseException) fırlattı ve uygulama hiç açılmadı. Bozuksa o paketi
    engelleyip (sys.modules[ad] = None -> ImportError) pypdf'in yerleşik
    yoluna düşürüyoruz. Bedeli: AES ile şifrelenmiş PDF'ler açılamaz.
    """
    son = None
    for engel in (None, "cryptography", "Crypto"):
        if engel:
            _modulleri_sil(engel)
            sys.modules[engel] = None
            print("Uyarı: sistemdeki '{}' paketi yüklenemedi ({}); kullanılmıyor."
                  .format(engel, type(son).__name__), file=sys.stderr)
        try:
            import pypdf  # noqa: F401
            return
        except (KeyboardInterrupt, SystemExit):
            raise
        except BaseException as e:  # panic BaseException'dır, Exception değil
            son = e
            _modulleri_sil("pypdf")
    raise son


pypdf_guvenli_yukle()
