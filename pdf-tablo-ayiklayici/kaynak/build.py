import re
h=open('app.html',encoding='utf-8').read()
def lib(p):
    s=open(p,encoding='utf-8').read()
    return s.replace('</script','<\\/script').replace('<!--','<\\!--').replace('<script','<\\script')
# Her kütüphane, sayfadaki define/module/exports/require'ı göremeyeceği kapalı bir fonksiyonda çalışır
def wrap(src, tail=''):
    return '(function(define,module,exports,require){\n'+src+'\n'+tail+'\n}).call(window);'
rep={'/*__PDFJS__*/':wrap(lib('pdfjs-dist-3.11.174/package/legacy/build/pdf.min.js'),'if(!window.pdfjsLib&&window["pdfjs-dist/build/pdf"])window.pdfjsLib=window["pdfjs-dist/build/pdf"];'),
     '/*__PDFWORKER__*/':wrap(lib('pdfjs-dist-3.11.174/package/legacy/build/pdf.worker.min.js')),
     '/*__XLSX__*/':wrap(lib('xlsx-0.18.5/package/dist/xlsx.full.min.js'),'if(typeof XLSX!=="undefined")window.XLSX=XLSX;'),
     '/*__CORE__*/':open('core.js',encoding='utf-8').read(),
     '/*__SAMPLE__*/':open('ornek.b64').read().strip()}
for k,v in rep.items():
    assert h.count(k)==1,k; h=h.replace(k,lambda m=None,v=v:v) if False else h.replace(k,v)
open('pdf-tablo-ayiklayici.html','w',encoding='utf-8').write(h)
print(len(h.encode())/1e6,'MB')
