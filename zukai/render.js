const { chromium } = require('playwright'); const fs = require('fs');
(async () => {
  const lines = JSON.parse(fs.readFileSync('lines.json'));
  let t = 0; const TL = [];
  for (const l of lines) { const start = t, vstart = start + 0.6; const end = vstart + l.dur + (l.key === 's5' ? 3.0 : 1.0); TL.push({ ...l, start, vstart, end }); t = end; }
  fs.writeFileSync('timeline.json', JSON.stringify(TL, null, 1));
  const total = t, fps = 30, n = Math.ceil(total * fps);
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  await p.addInitScript(tl => { window.TIMELINE = tl; }, TL);
  await p.goto('file://' + process.cwd() + '/anim.html'); await p.waitForTimeout(500);
  fs.mkdirSync('frames', { recursive: true });
  for (let i = 0; i < n; i++) {
    await p.evaluate(tt => window.render(tt), i / fps);
    await p.screenshot({ path: `frames/f${String(i).padStart(5, '0')}.jpg`, type: 'jpeg', quality: 92 });
  }
  console.log('frames', n, 'total', total.toFixed(2));
  await b.close();
})();
