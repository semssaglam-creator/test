"""Tarih bicim donusumleri.

Kullanici arayuzunde ve Excel ciktilarinda Turkce 'GG.AA.YYYY SS:DD' formati
kullanilir; veritabaninda siralama/filtreleme icin ISO 'YYYY-AA-GG SS:DD'
formati saklanir.
"""
from datetime import datetime


def simdi_tr():
    return datetime.now().strftime("%d.%m.%Y %H:%M")


def tr_to_iso(tr_str):
    tr_str = (tr_str or "").strip()
    if not tr_str:
        return ""
    try:
        return datetime.strptime(tr_str, "%d.%m.%Y %H:%M").strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return tr_str


def iso_to_tr(iso_str):
    iso_str = (iso_str or "").strip()
    if not iso_str:
        return ""
    try:
        return datetime.strptime(iso_str, "%Y-%m-%d %H:%M").strftime("%d.%m.%Y %H:%M")
    except ValueError:
        return iso_str


def tr_tarih_to_iso_gun(tr_tarih_str):
    """'GG.AA.YYYY' -> 'YYYY-AA-GG' (sadece tarih, istatistik filtresi icin)."""
    tr_tarih_str = (tr_tarih_str or "").strip()
    if not tr_tarih_str:
        return ""
    try:
        return datetime.strptime(tr_tarih_str, "%d.%m.%Y").strftime("%Y-%m-%d")
    except ValueError:
        return ""
