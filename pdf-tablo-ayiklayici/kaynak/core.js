// ---- Çekirdek: PDF metin öğelerinden satır/sütun çıkarma (DOM bağımsız) ----
var Core = (function () {
  // İşlem listesinden (operator list) her kelimenin gerçek konumunu hesapla.
  // pdf.js'in getTextContent'i yakın duran hücreleri tek öğede birleştirebildiği için
  // dar sütun aralıklarında bu yöntem şart.
  async function extractWords(page, viewport, lib) {
    var OPS = lib.OPS, U = lib.Util;
    var ol = await page.getOperatorList();
    var fns = ol.fnArray, args = ol.argsArray;
    var ID = [1, 0, 0, 1, 0, 0];
    var st = { ctm: ID.slice(), fs: 0, fm: 0.001, tc: 0, tw: 0, th: 1, tl: 0, rise: 0, tm: ID.slice(), tlm: ID.slice() };
    var stack = [], words = [];
    function clone(o) { return { ctm: o.ctm.slice(), fs: o.fs, fm: o.fm, tc: o.tc, tw: o.tw, th: o.th, tl: o.tl, rise: o.rise, tm: o.tm.slice(), tlm: o.tlm.slice() }; }
    function td(x, y) { st.tlm = U.transform(st.tlm, [1, 0, 0, 1, x, y]); st.tm = st.tlm.slice(); }
    function apply(m, x, y) { return [m[0] * x + m[2] * y + m[4], m[1] * x + m[3] * y + m[5]]; }
    for (var i = 0; i < fns.length; i++) {
      var f = fns[i], a = args[i];
      switch (f) {
        case OPS.save: stack.push(clone(st)); break;
        case OPS.restore: if (stack.length) st = stack.pop(); break;
        case OPS.transform: st.ctm = U.transform(st.ctm, a); break;
        case OPS.paintFormXObjectBegin: stack.push(clone(st)); if (a[0]) st.ctm = U.transform(st.ctm, a[0]); break;
        case OPS.paintFormXObjectEnd: if (stack.length) st = stack.pop(); break;
        case OPS.beginText: st.tm = ID.slice(); st.tlm = ID.slice(); break;
        case OPS.setFont:
          st.fs = a[1]; st.fm = 0.001;
          try { var fo = page.commonObjs.get(a[0]); if (fo && fo.fontMatrix) st.fm = fo.fontMatrix[0]; } catch (e) {}
          break;
        case OPS.setCharSpacing: st.tc = a[0]; break;
        case OPS.setWordSpacing: st.tw = a[0]; break;
        case OPS.setHScale: st.th = a[0] / 100; break;
        case OPS.setLeading: st.tl = a[0]; break;
        case OPS.setTextRise: st.rise = a[0]; break;
        case OPS.moveText: td(a[0], a[1]); break;
        case OPS.setLeadingMoveText: st.tl = -a[1]; td(a[0], a[1]); break;
        case OPS.nextLine: td(0, -st.tl); break;
        case OPS.setTextMatrix: st.tm = a.slice(0, 6); st.tlm = a.slice(0, 6); break;
        case OPS.showText: {
          var M = U.transform(viewport.transform, U.transform(st.ctm, st.tm));
          var dfs = Math.abs(st.fs) * Math.hypot(M[2], M[3]) || 1;
          var x = 0, cur = null, lastEnd = 0;
          var flush = function () {
            if (cur && cur.s.trim()) {
              var p0 = apply(M, cur.xs, st.rise), p1 = apply(M, cur.xe, st.rise);
              words.push({ x: Math.min(p0[0], p1[0]), w: Math.abs(p1[0] - p0[0]), y: p0[1], fs: dfs, s: cur.s });
            }
            cur = null;
          };
          var g = a[0];
          for (var k = 0; k < g.length; k++) {
            var gl = g[k];
            if (typeof gl === "number") { x -= gl * st.fs / 1000 * st.th; continue; }
            if (!gl) continue;
            var sp = gl.isSpace || gl.unicode === " " || gl.unicode === " ";
            var adv = ((gl.width || 0) * st.fs * st.fm + st.tc + (gl.isSpace ? st.tw : 0)) * st.th;
            if (sp) { flush(); }
            else {
              if (cur && x - lastEnd > 0.15 * Math.abs(st.fs)) flush();
              if (!cur) cur = { xs: x, xe: x, s: "" };
              cur.s += gl.unicode || "";
              cur.xe = x + adv - st.tc * st.th;
              lastEnd = cur.xe;
            }
            x += adv;
          }
          flush();
          st.tm = U.transform(st.tm, [1, 0, 0, 1, x, 0]);
          break;
        }
      }
    }
    return words;
  }

  // Yedek yol: getTextContent öğeleri (işlem listesi boş dönerse)
  function itemsFromText(textContent, viewport, Util) {
    var out = [];
    textContent.items.forEach(function (it) {
      if (!it.str || !it.str.trim()) return;
      var tx = Util.transform(viewport.transform, it.transform);
      var fs = Math.hypot(tx[2], tx[3]) || 8;
      var w = it.width * viewport.scale; if (!(w > 0)) w = it.str.length * fs * 0.5;
      var cw = w / Math.max(1, it.str.length), re = /\S+/g, m;
      while ((m = re.exec(it.str))) out.push({ x: tx[4] + m.index * cw, w: m[0].length * cw, y: tx[5], fs: fs, s: m[0] });
    });
    return out;
  }

  // Öğeleri satırlara, satır içinde yakın öğeleri hücre parçalarına (segment) birleştir
  function buildLines(items, opt) {
    var tol = opt.rowTol, gapEm = opt.wordGap;
    var sorted = items.slice().sort(function (a, b) { return a.y - b.y || a.x - b.x; });
    var lines = [];
    sorted.forEach(function (it) {
      var L = lines.length ? lines[lines.length - 1] : null;
      if (L && Math.abs(it.y - L.y) <= tol) { L.items.push(it); L.y = (L.y * (L.items.length - 1) + it.y) / L.items.length; }
      else lines.push({ y: it.y, items: [it] });
    });
    lines.forEach(function (L) {
      L.items.sort(function (a, b) { return a.x - b.x; });
      var segs = [], cur = null;
      L.items.forEach(function (it) {
        if (cur) {
          var gap = it.x - (cur.x + cur.w);
          if (gap < gapEm * Math.max(cur.fs, it.fs)) {
            cur.s += (gap > 0.12 * it.fs ? " " : "") + it.s;
            cur.w = Math.max(cur.x + cur.w, it.x + it.w) - cur.x;
            cur.fs = Math.max(cur.fs, it.fs);
            return;
          }
        }
        cur = { x: it.x, w: it.w, fs: it.fs, s: it.s, y: L.y };
        segs.push(cur);
      });
      L.segs = segs;
    });
    return lines;
  }

  // Tüm satırlarda x kapsama histogramı; boş kalan dikey koridorların ortası = sütun ayracı.
  // opt.target > 0 ise: kelime düzeyinde en geniş (target-1) koridor seçilir (dar aralıklar için).
  function detectDividers(lineSets, pageWidth, opt) {
    var W = Math.ceil(pageWidth) + 2, cov = new Int32Array(W), n = 0, lo = W, hi = 0;
    var useItems = opt.target > 1;
    lineSets.forEach(function (lines) {
      lines.forEach(function (L) {
        var parts = useItems ? L.items : L.segs;
        if (!parts.length) return;
        n++;
        parts.forEach(function (s) {
          var a = Math.max(0, Math.round(s.x)), b = Math.min(W - 1, Math.round(s.x + s.w) - 1);
          for (var i = a; i <= b; i++) cov[i]++;
          lo = Math.min(lo, a); hi = Math.max(hi, b);
        });
      });
    });
    if (!n) return [];
    var allow = Math.max(1, Math.round(n * opt.noise));
    var runs = [], start = -1;
    for (var i = lo; i <= hi + 1; i++) {
      var empty = i <= hi && cov[i] <= allow;
      if (empty && start < 0) start = i;
      if (!empty && start >= 0) { runs.push({ a: start, b: i, w: i - start }); start = -1; }
    }
    var divs;
    if (useItems) {
      // En geniş koridordan başla; içi boş kalacak sütun üreten adayı atla
      var cands = runs.filter(function (r) { return r.w >= 1; }).sort(function (p, q) { return q.w - p.w; });
      var xs = [];
      lineSets.forEach(function (lines) { lines.forEach(function (L) { L.items.forEach(function (it) { xs.push(it.x + it.w / 2); }); }); });
      divs = [];
      for (var c = 0; c < cands.length && divs.length < opt.target - 1; c++) {
        var d = (cands[c].a + cands[c].b) / 2, trial = divs.concat([d]).sort(function (p, q) { return p - q; });
        var cnt = new Array(trial.length + 1).fill(0);
        xs.forEach(function (x) { cnt[colOf(x, trial)]++; });
        if (cnt.every(function (v) { return v > allow; })) divs = trial;
      }
    } else {
      divs = runs.filter(function (r) { return r.w >= opt.minGap; }).map(function (r) { return (r.a + r.b) / 2; });
      // İçi neredeyse hep boş kalan sütunları komşusuyla birleştir
      for (var guard = 0; guard < 50 && divs.length; guard++) {
        var cnt = new Array(divs.length + 1).fill(0);
        lineSets.forEach(function (lines) { lines.forEach(function (L) { L.segs.forEach(function (s) {
          cnt[colOf(s.x + s.w / 2, divs)]++; }); }); });
        var worst = -1;
        for (var j = 0; j < cnt.length; j++) if (cnt[j] <= allow && (worst < 0 || cnt[j] < cnt[worst])) worst = j;
        if (worst < 0) break;
        divs.splice(worst === 0 ? 0 : worst - 1, 1);
      }
    }
    return divs.sort(function (p, q) { return p - q; }).map(function (v) { return Math.round(v * 10) / 10; });
  }
  function colOf(x, divs) { var k = 0; while (k < divs.length && x > divs[k]) k++; return k; }

  var NUM_TR = /^[-−(]?\d{1,3}(\.\d{3})*(,\d+)?\)?$|^[-−(]?\d+,\d+\)?$/;
  function toNumber(s) {
    var t = s.replace(/\s/g, "");
    var neg = /^[-−(]/.test(t) || /\)$/.test(t);
    var core = t.replace(/^[-−(]|\)$/g, "");
    if (!NUM_TR.test(t)) {
      // düz tamsayı (ör. 2026, 1043); baştaki sıfır ve 10+ hane (VKN/TCKN) metin kalır
      if (/^-?\d+$/.test(t) && !/^-?0\d/.test(t) && t.replace("-", "").length < 10) return parseInt(t, 10);
      return null;
    }
    if (/^0\d/.test(core) && core.indexOf(",") < 0) return null;
    var v = parseFloat(core.replace(/\./g, "").replace(",", "."));
    return isNaN(v) ? null : (neg ? -v : v);
  }

  // Alta kayan kod/dönem parçaları boşluksuz birleşir:
  // 2026010166Evn + 0000001, 01/2025- + 12/2025
  function glue(a, b) {
    if (/[-\/]$/.test(a)) return true;
    return !/\s/.test(a) && !/\s/.test(b) && a.length >= 8 && (a.match(/\d/g) || []).length >= 4 && /^[0-9A-Za-z]+$/.test(b);
  }

  // Satırları ayraçlara göre hücrelere böl
  function toRows(lines, divs, opt) {
    var nc = divs.length + 1, rows = [];
    lines.forEach(function (L) {
      var cells = new Array(nc).fill(""), last = new Array(nc).fill(null);
      L.items.forEach(function (it) {
        var k = colOf(it.x + it.w / 2, divs), p = last[k];
        if (!cells[k]) cells[k] = it.s;
        else cells[k] += ((it.x - (p.x + p.w)) > 0.12 * it.fs ? " " : "") + it.s;
        last[k] = it;
      });
      if (opt.dropEmpty && cells.every(function (v) { return !v; })) return;
      rows.push(cells);
    });
    if (opt.mergeWrap) {
      // Anahtar sütunu boş olan satır = üstteki kaydın alta kaymış devamı
      var key = Math.min(opt.keyCol || 0, nc - 1), out = [];
      rows.forEach(function (r) {
        var prev = out[out.length - 1];
        var hasNum = opt.wrapNoNumbers && r.some(function (v) { return v && /,\d+\)?$/.test(v) && toNumber(v) !== null; });
        if (prev && !r[key] && !hasNum && r.some(function (v) { return v; })) {
          r.forEach(function (v, i) { if (v) prev[i] = prev[i] ? prev[i] + (glue(prev[i], v) ? "" : " ") + v : v; });
        } else out.push(r);
      });
      rows = out;
    }
    if (opt.fillCols && opt.fillCols.length) {
      var k2 = Math.min(opt.keyCol || 0, nc - 1);
      for (var r2 = 1; r2 < rows.length; r2++) {
        if (rows[r2][k2]) continue;
        opt.fillCols.forEach(function (c2) { if (c2 < nc && !rows[r2][c2]) rows[r2][c2] = rows[r2 - 1][c2]; });
      }
    }
    return rows;
  }

  function dedupeRepeats(pagesRows) {
    // Birden fazla sayfada aynen tekrar eden satırları (sayfa/sütun başlıkları) ilk görülme dışında at
    var seen = {}, count = {};
    pagesRows.forEach(function (rows, p) {
      var local = {};
      rows.forEach(function (r) { var k = r.join("\u0001"); if (!local[k]) { local[k] = 1; count[k] = (count[k] || 0) + 1; } });
    });
    return pagesRows.map(function (rows) {
      return rows.filter(function (r) {
        var k = r.join("\u0001");
        if (count[k] > 1) { if (seen[k]) return false; seen[k] = 1; }
        return true;
      });
    });
  }

  return { extractWords: extractWords, itemsFromText: itemsFromText, buildLines: buildLines, detectDividers: detectDividers, toRows: toRows, toNumber: toNumber, glue: glue, dedupeRepeats: dedupeRepeats };
})();
if (typeof module !== "undefined") module.exports = Core;
