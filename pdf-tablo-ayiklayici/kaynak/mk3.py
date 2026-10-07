from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import simpleSplit
import random
random.seed(11)
pdfmetrics.registerFont(TTFont('D','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DB','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
def tr(v): s=f"{v:,.2f}"; return s.replace(',','X').replace('.',',').replace('X','.')
cols=[("Sıra No",22,'l'),("Vergi No",44,'l'),("TC Kimlik No",48,'l'),("Plaka No",36,'l'),("Adı Soyadı / Ünvanı",88,'l'),("Adres",96,'l'),
("Vergi Dönemi",42,'l'),("Ana Vergi Kodu",30,'l'),("Vergi Kodu",26,'l'),("Ana Takip Dosya No",54,'l'),("Takip Dosya No",54,'l'),
("Vergi Aslı Borcu Toplamı",56,'r'),("KGZ Toplamı",48,'r'),("Ceza Tutarı",48,'r'),("Toplam Borç",56,'r')]
GAP=5; X0=24; FS=6.5; LH=8
xs=[];x=X0
for n,w,a in cols: xs.append(x); x+=w+GAP
print("genişlik",x)
adlar=["Örnek Gıda San. ve Tic. Ltd. Şti.","Kurgu İnşaat Taahhüt A.Ş.","Ahmet DENEME","Ayşe ÖRNEKOĞLU","Mükellef-A Tekstil Sanayi ve Ticaret Limited Şirketi","Test Nakliyat"]
adres=["Atatürk Mah. Örnek Cad. No:12 D:3 Antakya/HATAY","Cumhuriyet Mah. Deneme Sok. No:5 İskenderun/HATAY","Organize Sanayi Bölgesi 3. Cadde No:41 Merkez/HATAY","Yeni Mah. 1001 Sok. No:8 Defne/HATAY"]
kod={"9047":"MTV","0015":"KDV","0003":"Gelir (Stopaj)","1048":"5035 Damga","0010":"Kurumlar"}
c=canvas.Canvas('ornek.pdf',pagesize=(842,595))
sira=0
def cell(t,i,y,font='D'):
    n,w,a=cols[i]; lines=[l for part in t.split('\n') for l in simpleSplit(part,font,FS,w)] if t else []; c.setFont(font,FS)
    for k,l in enumerate(lines):
        (c.drawRightString(xs[i]+w,y-k*LH,l) if a=='r' else c.drawString(xs[i],y-k*LH,l))
    return max(1,len(lines))
for p in range(3):
    c.setFont('DB',10); c.drawString(X0,565,"AMME ALACAKLARI BORÇ LİSTESİ (ÖRNEK VERİ — GERÇEK MÜKELLEF DEĞİLDİR)")
    c.setFont('D',7); c.drawRightString(818,565,f"Sayfa {p+1}/3")
    y=540; h=max(cell(n,i,y,'DB') for i,(n,w,a) in enumerate(cols)); y-=h*LH+6
    while y>70:
        sira+=1; tuzel=random.random()<.5
        ident=[str(sira), str(random.randint(10**9,10**10-1)) if tuzel else "", "" if tuzel else str(random.randint(10**10,10**11-1)),"",random.choice(adlar),random.choice(adres)]
        for j in range(random.choice([1,1,2,3])):
            ak=random.choice(list(kod)); pl=f"31 {random.choice(['ABC','KR','D'])} {random.randint(10,999)}" if ak=="9047" else ""; asl=random.randint(500,90000)+random.randint(0,99)/100; kgz=asl*random.uniform(.05,.6); cz=random.choice([0,asl*0.1,asl])
            vals=(ident if j==0 else [""]*6)+[];vals[3]=pl;vals+=[(lambda a:f"{a:02d}/2025-\n{min(12,a+random.randint(0,11)):02d}/2025")(random.randint(1,12)),ak,ak,f"20260101{random.randint(10,99)}Evn\n{random.randint(1,9999):07d}",f"20260101{random.randint(10,99)}Eux\n{random.randint(1,9999):07d}",tr(asl),tr(kgz),tr(cz) if cz else "0,00",tr(asl+kgz+cz)]
            h=max(cell(v,i,y) for i,v in enumerate(vals)); y-=h*LH+4
    c.showPage()
c.save()
