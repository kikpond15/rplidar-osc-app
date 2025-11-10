// file: RPLidarOscViewer.pde
// 依存: oscP5（Processing Contributions Managerで導入）

import oscP5.*;
import netP5.*;

OscP5 osc;
float[] scan = new float[360]; // mm
boolean hasFrame = false;

float pxPerMeter = 120;  // スケール（環境で調整）
float minDist = 100;     // mm 未満はノイズとして捨てる
float maxDist = 6000;    // mm 以上は描かない（A1の実用域に合わせて）

PFont font;
int lastFrameCount = 0;
int lastMillis = 0;
float fps = 0;

void setup() {
  size(900, 900);
  surface.setTitle("RPLIDAR OSC Viewer");
  background(0);
  osc = new OscP5(this, 8000); // 受信ポート
  font = createFont("Menlo", 14);
  textFont(font);
}

void draw() {
  background(0);
  translate(width/2, height/2);

  // ガイド円（1m, 2m, 3m）
  stroke(60);
  noFill();
  for (int m=1; m<=3; m++) {
    circle(0, 0, 2 * m * pxPerMeter);
  }

  if (hasFrame) {
    stroke(255);
    for (int a=0; a<360; a++) {
      float d = scan[a]; // mm
      if (d < minDist || d > maxDist) continue;
      float r = (d/1000.0) * pxPerMeter; // mm→m→px
      float rad = radians(a);
      float x = r * cos(rad);
      float y = r * sin(rad);
      point(x, y);
    }
  }

  // HUD
  resetMatrix();
  fill(255);
  text("pxPerMeter: " + nf(pxPerMeter, 0, 1) + "  |  min: " + int(minDist) + "mm  max: " + int(maxDist) + "mm", 12, 22);
  text("FPS(recv): " + nf(fps, 0, 1), 12, 42);
  text("Keys: [ / ] scale, { / } maxDist, < / > minDist", 12, 62);

  // 簡易FPS（受信タイミング）
  if (millis() - lastMillis >= 500) {
    fps = (frameCount - lastFrameCount) * 2.0;
    lastFrameCount = frameCount;
    lastMillis = millis();
  }
}

void oscEvent(OscMessage m) {
  try {
    if (!m.checkAddrPattern("/rplidar/scan")) return;

    int argc = (m.arguments() != null) ? m.arguments().length : 0;

    // 旧仕様：360本一括
    if (argc == 360) {
      for (int i = 0; i < 360; i++) {
        scan[i] = getAsFloat(m, i);
      }
      hasFrame = true;
      return;
    }

    // 新仕様： [start, d0..d119]
    if (argc >= 2) {
      int start = (int)getAsFloat(m, 0);
      start = constrain(start, 0, 359);

      int count = min(120, argc - 1);
      for (int i = 0; i < count; i++) {
        int idx = start + i;
        if (idx >= 360) break;
        scan[idx] = getAsFloat(m, i + 1);
      }
      // ざっくり：最後のセグメントが来たら描画OK
      if (start >= 240) hasFrame = true;
      return;
    }

    println("[OSC] unexpected message: typetag=", m.typetag(), "argc=", argc);

  } catch (Exception e) {
    println("[OSC] oscEvent error:", e);
  }
}


// 任意型 → float に吸収するヘルパ
float getAsFloat(OscMessage m, int idx) {
  String tt = m.typetag();
  // typetagが無い場合の保険
  if (tt == null || tt.length() <= idx) {
    // 例外避け：とりあえず floatValue を試す→ダメなら intValue
    try { return m.get(idx).floatValue(); } 
    catch (Exception e) { 
      try { return (float)m.get(idx).intValue(); } 
      catch (Exception e2) { return 0; }
    }
  }
  char t = tt.charAt(idx);
  switch (t) {
    case 'f': return m.get(idx).floatValue();
    case 'i': return (float)m.get(idx).intValue();
    case 'h': return (float)m.get(idx).longValue();  // 来ることは稀ですが一応
    default:
      try { return m.get(idx).floatValue(); } 
      catch (Exception e) { 
        try { return (float)m.get(idx).intValue(); } 
        catch (Exception e2) { return 0; }
      }
  }
}



// 簡易操作
void keyPressed() {
  if (key == '[') pxPerMeter = max(10, pxPerMeter - 10);
  if (key == ']') pxPerMeter = min(1000, pxPerMeter + 10);
  if (key == '{') maxDist = max(500, maxDist - 100);
  if (key == '}') maxDist = min(10000, maxDist + 100);
  if (key == '<') minDist = max(0, minDist - 50);
  if (key == '>') minDist = min(3000, minDist + 50);
}
