import re
h=open('app.html',encoding='utf-8').read()
def lib(p):
    s=open(p,encoding='utf-8').read()
    return s.replace('</script','<\\/script').replace('<!--','<\\!--').replace('<script','<\\script')
import base64
def b64(p): return base64.b64encode(open(p,'rb').read()).decode()
rep={'/*__B64PDF__*/':b64('pdfjs-dist-3.11.174/package/legacy/build/pdf.min.js'),
     '/*__B64WORKER__*/':b64('pdfjs-dist-3.11.174/package/legacy/build/pdf.worker.min.js'),
     '/*__B64XLSX__*/':b64('xlsx-0.18.5/package/dist/xlsx.full.min.js'),
     '/*__CORE__*/':open('core.js',encoding='utf-8').read(),
     '/*__SAMPLE__*/':open('ornek.b64').read().strip()}
for k,v in rep.items():
    assert h.count(k)==1,k; h=h.replace(k,lambda m=None,v=v:v) if False else h.replace(k,v)
open('pdf-tablo-ayiklayici.html','w',encoding='utf-8').write(h)
print(len(h.encode())/1e6,'MB')
