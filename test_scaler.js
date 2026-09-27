const fs = require("fs");
const path = require("path");

const USAGE = `node test_scaler.js [page.html ...]

With no argument, tests every built page that carries a scaler. The scaler's
script tag sits above the ingredient list, so a browser parsing top to bottom
reaches it before those nodes exist; the DOM stub below reproduces that by
scoping querySelectorAll to what has been parsed so far.`;

function domFrom(html) {
  const cut = html.indexOf("</script>");
  const spans = [...html.matchAll(/<span class="q" data-q="([^"]+)">([^<]*)<\/span>/g)]
    .map(m => ({ q: m[1], txt: m[2], parsedBeforeScript: m.index < cut }));
  const fvals = [...html.matchAll(/<button type="button" data-f="([^"]+)"/g)].map(m => m[1]);
  return { spans, fvals };
}

const mk = o => Object.assign({
  classList: {
    cls: new Set(),
    toggle(c, on) { on ? this.cls.add(c) : this.cls.delete(c); },
    has(c) { return this.cls.has(c); },
  },
  _h: {},
  addEventListener(t, fn) { this._h[t] = fn; },
  fire(t) { this._h[t] && this._h[t].call(this); },
}, o);

function mount(html, script) {
  const { spans: raw, fvals } = domFrom(html);
  const spans = raw.map(s =>
    mk({ dataset: { q: s.q }, textContent: s.txt, _pre: s.parsedBeforeScript }));
  const buttons = fvals.map(f => mk({ dataset: { f } }));
  const input = mk({ value: "1" });
  const box = mk({
    querySelectorAll: s => (s === "button" ? buttons : []),
    querySelector: s => (s === "input" ? input : null),
  });
  let ready = "loading";
  const docH = {};
  global.document = {
    get readyState() { return ready; },
    addEventListener: (t, fn) => { docH[t] = fn; },
    querySelector: s => (s === "[data-scaler]" ? box : null),
    querySelectorAll: s =>
      s !== ".q" ? [] : ready === "loading" ? spans.filter(x => x._pre) : spans,
  };
  eval(script);
  ready = "complete";
  if (docH.DOMContentLoaded) docH.DOMContentLoaded();
  return { spans, buttons, input, fvals };
}

const round = v => parseFloat(v.toFixed(v >= 100 ? 0 : v >= 10 ? 1 : 2));
const near = (a, b) => Math.abs(a - b) < 0.011;

function check(file) {
  const html = fs.readFileSync(file, "utf8");
  const m = /<script>([\s\S]*?)<\/script>/.exec(html);
  if (!m) return null;
  const shipped = m[1];
  const problems = [];

  const { spans, buttons, input, fvals } = mount(html, shipped);
  const base = spans.map(s => parseFloat(s.dataset.q));
  const now = () => spans.map(s => parseFloat(s.textContent));
  const at = (label, f, click) => {
    if (click !== undefined) buttons[fvals.indexOf(click)].fire("click");
    else { input.value = String(f); input.fire("input"); }
    const want = base.map(v => round(v * f));
    const got = now();
    if (!(got.length === want.length && got.every((v, i) => near(v, want[i]))))
      problems.push(`${label}: want ${want} got ${got}`);
  };

  if (!spans.length) problems.push("scaler present but no quantity spans found");
  at("1x", 1, "1");
  at("2x", 2, "2");
  at("3x after 2x, must not compound", 3, "3");
  at("0.5x", 0.5, "0.5");
  at("custom 1.5x", 1.5);
  const held = now();
  for (const bad of ["0", "", "-2"]) {
    input.value = bad;
    input.fire("input");
    if (!now().every((v, i) => near(v, held[i])))
      problems.push(`input ${JSON.stringify(bad)} corrupted the quantities`);
  }
  at("back to 1x", 1, "1");
  const on = buttons.filter(b => b.classList.has("on")).map(b => b.dataset.f);
  if (on.length !== 1 || on[0] !== "1") problems.push(`active button = ${on}`);

  const naive = shipped.replace(/if\(document\.readyState[\s\S]*?\{ init\(\); \}/, "init();");
  if (naive !== shipped && spans.length > 1) {
    const old = mount(html, naive);
    old.buttons[old.fvals.indexOf("2")].fire("click");
    const moved = old.spans.filter(
      s => !near(parseFloat(s.textContent), parseFloat(s.dataset.q))).length;
    if (moved >= old.spans.length)
      problems.push("readiness guard absent: the parse-time bug no longer reproduces");
  }
  return { name: path.basename(file), count: spans.length, problems };
}

const args = process.argv.slice(2);
if (args[0] === "-h" || args[0] === "--help") {
  console.log(USAGE);
  process.exit(0);
}
const files = args.length
  ? args
  : fs.readdirSync(path.join(__dirname, "recipes"))
      .filter(f => f.endsWith(".html"))
      .map(f => path.join(__dirname, "recipes", f))
      .filter(f => fs.readFileSync(f, "utf8").includes("data-scaler"));

let bad = 0;
let n = 0;
let scaled = 0;
for (const f of files) {
  const r = check(f);
  if (!r) continue;
  n++;
  scaled += r.count;
  if (r.problems.length) {
    bad++;
    console.log(`FAIL ${r.name}`);
    r.problems.forEach(p => console.log(`       ${p}`));
  }
}
console.log(bad
  ? `\n${bad} of ${n} pages FAILED`
  : `${n} scaler pages pass, ${scaled} quantities scaled`);
process.exit(bad ? 1 : 0);
