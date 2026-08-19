#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Add Pi-hole section (9) to hermes-gfw-guide, all 4 languages."""
import re, json, os, time, urllib.parse, urllib.request

BASE = "/tmp/gfw"
Z = open("/tmp/gfw/index.html", encoding="utf-8").read()
EN = open("/tmp/gfw/en/index.html", encoding="utf-8").read()
CN = open("/tmp/gfw/zh-CN/index.html", encoding="utf-8").read()
AR = open("/tmp/gfw/ar/index.html", encoding="utf-8").read()

ZH_SECTION = '''  <!-- 9 Pi-hole -->
  <div class="section" id="pihole">
    <h2 class="section-title"><span class="num">9</span> Pi-hole 私人 DNS（全機擋廣告）</h2>
    <p class="section-desc">承接返前面嘅 VM，喺同一部機行 Pi-hole + DNS-over-TLS（DoT），手機、電腦、平板全部經你嘅私人 DNS 出街 — 廣告喺 DNS 層直接擋走，唔使喺每部機裝 blocker，亦都唔使開住任何 VPN App 先有擋廣告。</p>
    <div class="step-list" style="counter-reset:step 0">
      <div class="step-item">
        <h3>VM 起 Pi-hole（Docker）</h3>
        <p>預設 admin 密碼會印喺 container log（<code>WEBPASSWORD</code>），網頁後台：<code>http://&lt;VM_IP&gt;:8080/admin</code>。DNS 只 bind 喺本機 5353，留返畀下一步嘅 DoT 前端轉發。</p>
        <div class="cmd">docker run -d --name pihole --restart unless-stopped \\
  -e TZ=Asia/Hong_Kong \\
  -p 127.0.0.1:5353:53/tcp -p 127.0.0.1:5353:53/udp \\
  -p 8080:80/tcp pihole/pihole:latest
docker logs pihole 2&gt;&amp;1 | grep -i password</div>
      </div>
      <div class="step-item">
        <h3>一定要更新 blocklist（新高裝係 0 條規則）</h3>
        <p>親測：新裝 Pi-hole <strong>一個廣告都唔會擋</strong>，因為 gravity 係空嘅。要手動跑一次先載入官方默認列表；之後可以喺 Web UI → Adlists 加自己鍾意嘅 list（例如 oisd / hagezi）。</p>
        <div class="cmd">docker exec pihole pihole -g</div>
        <div class="tip red"><strong>⚠️ 唔好漏咗呢步：</strong><code>pihole -g</code> 唔跑，裝完會以為部機「壞咗」——實際只係列表未載入。之後 blocklist 更新可以經 Web UI 或 cron 定時跑。</div>
      </div>
      <div class="step-item">
        <h3>攞真 SSL cert（DoT 驗證要用）</h3>
        <p>用 acme.sh + DNS-01（Cloudflare token），唔使開 80 port，cert 自動續期。</p>
        <div class="cmd">export CF_Token="&lt;你的CF_API_Token&gt;" CF_Zone_ID="&lt;你的Zone_ID&gt;"
~/.acme.sh/acme.sh --issue --dns dns_cf -d dns.你的域名.com \\
  --server letsencrypt --keylength ec-256
~/.acme.sh/acme.sh --install-cert -d dns.你的域名.com --ecc \\
  --key-file /etc/dnsproxy/key.pem --fullchain-file /etc/dnsproxy/fullchain.pem \\
  --reloadcmd "sudo systemctl restart dnsproxy"</div>
      </div>
      <div class="step-item">
        <h3>dnsproxy 起 DoT（853）</h3>
        <p>用 AdGuard 嘅 <code>dnsproxy</code>（單一 binary），聽 853，上游指返 Pi-hole。systemd unit：</p>
        <div class="cmd">[Unit]
Description=DoT -&gt; Pi-hole
After=docker.service
[Service]
ExecStart=/usr/local/bin/dnsproxy --listen=0.0.0.0 --port=0 --tls-port=853 \\
  --tls-crt=/etc/dnsproxy/fullchain.pem --tls-key=/etc/dnsproxy/key.pem \\
  --upstream=127.0.0.1:5353 --cache --cache-size=65536
Restart=always
[Install]
WantedBy=multi-user.target</div>
        <p><code>--port=0</code> 好重要：唔係嘅話 dnsproxy 會連 plain DNS 53 一齊開，同 VM 上其他嘢爭 port。</p>
      </div>
      <div class="step-item">
        <h3>OCI Security List 開 853</h3>
        <p>Oracle 有兩層防火牆（同 §7 講嘅一樣）：OCI Console → Networking → Security Lists → Add Ingress Rule：<code>TCP 853</code>。</p>
      </div>
      <div class="step-item">
        <h3>DNS record（灰雲 A record）</h3>
        <p>CF Dashboard → DNS → 加一條：<code>dns.你的域名.com</code> → A record → <code>&lt;VM_IP&gt;</code>，<strong>一定要灰雲</strong>（Proxy off）— DoT 係直接 TCP 到 VM，行唔到 CF proxy。</p>
      </div>
      <div class="step-item">
        <h3>手機 / 電腦設定</h3>
        <ul>
          <li><strong>Android（原生）：</strong>設定 → 私人 DNS → 主機名稱填 <code>dns.你的域名.com</code>（系統 DoT，唔使裝 App）</li>
          <li><strong>iPhone / iPad：</strong>用 DNS configuration profile（.mobileconfig，DoT），Safari 開 → 設定 → 一般 → VPN 與裝置管理 → 安裝 + 信任。可以叫 AI 幫手生成個 profile</li>
          <li><strong>Windows 11：</strong>設定 → 網路和網際網路 → DNS → 手動 → DoT 填 <code>dns.你的域名.com</code></li>
        </ul>
      </div>
    </div>
    <div class="tip green" style="margin-top:12px"><strong>驗證：</strong><code>dig +tls @dns.你的域名.com google.com</code> 出到 IP 即係通；再 <code>dig +tls @dns.你的域名.com doubleclick.net</code> 應該出 <code>0.0.0.0</code>（blocked）。</div>
    <div class="tip red" style="margin-top:8px"><strong>⚠️ 注意事項：</strong>
      <ul style="margin:4px 0 0 18px">
        <li>部分網絡（公司 Wi-Fi / 某啲 ISP）會封 853 port → 呢個情況會靜靜雞跌落未加密 DNS。需要嘅話加個 DoH（443）前端做後備，但 Android 私人 DNS 只食 DoT。</li>
        <li>唔好將你個 DNS 地址貼去公開地方——任何人攞到都可以借用你個 resolver（開放 DNS 濫用 + 食你 VM 流量）。</li>
        <li>blocklist 通常唔會 cover 晒所有 apex domain（例如 <code>googleadservices.com</code> 本身唔喺 list）——正常，實際廣告流量都係行子域（<code>ad.xxx.com</code>），嗰啲先係重點。</li>
      </ul>
    </div>
  </div>'''

EN_SECTION = '''<!-- 9 Pi-hole -->
<div class="section" id="pihole">
  <h2 class="section-title"><span class="num">9</span> Pi-hole Private DNS (whole-device ad blocking)</h2>
  <p class="section-desc">Building on the VM from the previous sections: run Pi-hole + DNS-over-TLS (DoT) on the same machine so phones, laptops and tablets all resolve through your private DNS — ads get blocked at the DNS layer, no per-device blocker apps, no VPN app required.</p>
  <div class="step-list" style="counter-reset:step 0">
    <div class="step-item">
      <h3>Run Pi-hole on the VM (Docker)</h3>
      <p>The default admin password is printed in the container log (<code>WEBPASSWORD</code>); web UI: <code>http://&lt;VM_IP&gt;:8080/admin</code>. DNS binds to localhost:5353 only, left for the DoT front-end from the next steps.</p>
      <div class="cmd">docker run -d --name pihole --restart unless-stopped \\
  -e TZ=Asia/Hong_Kong \\
  -p 127.0.0.1:5353:53/tcp -p 127.0.0.1:5353:53/udp \\
  -p 8080:80/tcp pihole/pihole:latest
docker logs pihole 2&gt;&amp;1 | grep -i password</div>
    </div>
    <div class="step-item">
      <h3>Update blocklists first (a fresh install blocks NOTHING)</h3>
      <p>Tested: a brand-new Pi-hole blocks zero ads because gravity is empty. Run it once to load the default lists; afterwards add your own lists in Web UI → Adlists (e.g. oisd / hagezi).</p>
      <div class="cmd">docker exec pihole pihole -g</div>
      <div class="tip red"><strong>⚠️ Do not skip this:</strong> without <code>pihole -g</code> the install looks "broken" — it just never loaded any lists. Keep lists fresh via the Web UI or a cron job.</div>
    </div>
    <div class="step-item">
      <h3>Get a real SSL cert (DoT validation requires it)</h3>
      <p>Use acme.sh + DNS-01 (Cloudflare token) — no port 80 needed, cert renews automatically.</p>
      <div class="cmd">export CF_Token="&lt;YOUR_CF_API_TOKEN&gt;" CF_Zone_ID="&lt;YOUR_ZONE_ID&gt;"
~/.acme.sh/acme.sh --issue --dns dns_cf -d dns.your-domain.com \\
  --server letsencrypt --keylength ec-256
~/.acme.sh/acme.sh --install-cert -d dns.your-domain.com --ecc \\
  --key-file /etc/dnsproxy/key.pem --fullchain-file /etc/dnsproxy/fullchain.pem \\
  --reloadcmd "sudo systemctl restart dnsproxy"</div>
    </div>
    <div class="step-item">
      <h3>DNS-over-TLS with dnsproxy (port 853)</h3>
      <p>Use AdGuard's <code>dnsproxy</code> (single binary) listening on 853, upstream = Pi-hole. systemd unit:</p>
      <div class="cmd">[Unit]
Description=DoT -&gt; Pi-hole
After=docker.service
[Service]
ExecStart=/usr/local/bin/dnsproxy --listen=0.0.0.0 --port=0 --tls-port=853 \\
  --tls-crt=/etc/dnsproxy/fullchain.pem --tls-key=/etc/dnsproxy/key.pem \\
  --upstream=127.0.0.1:5353 --cache --cache-size=65536
Restart=always
[Install]
WantedBy=multi-user.target</div>
      <p><code>--port=0</code> matters: without it dnsproxy also opens plain DNS on 53 and collides with whatever else runs on the VM.</p>
    </div>
    <div class="step-item">
      <h3>Open 853 in the OCI Security List</h3>
      <p>Oracle has two firewall layers (same as §7): OCI Console → Networking → Security Lists → Add Ingress Rule: <code>TCP 853</code>.</p>
    </div>
    <div class="step-item">
      <h3>DNS record (grey-cloud A record)</h3>
      <p>CF Dashboard → DNS → add: <code>dns.your-domain.com</code> → A record → <code>&lt;VM_IP&gt;</code>, <strong>grey cloud mandatory</strong> (Proxy off) — DoT connects straight to the VM over TCP, it cannot go through the CF proxy.</p>
    </div>
    <div class="step-item">
      <h3>Device setup</h3>
      <ul>
        <li><strong>Android (native):</strong> Settings → Private DNS → hostname <code>dns.your-domain.com</code> (system DoT, no app needed)</li>
        <li><strong>iPhone / iPad:</strong> install a DNS configuration profile (.mobileconfig, DoT) — open in Safari → Settings → General → VPN &amp; Device Management → install + trust. An AI assistant can generate the profile</li>
        <li><strong>Windows 11:</strong> Settings → Network &amp; Internet → DNS → Manual → DoT, set <code>dns.your-domain.com</code></li>
      </ul>
    </div>
  </div>
  <div class="tip green" style="margin-top:12px"><strong>Verify:</strong> <code>dig +tls @dns.your-domain.com google.com</code> returns an IP; then <code>dig +tls @dns.your-domain.com doubleclick.net</code> should return <code>0.0.0.0</code> (blocked).</div>
  <div class="tip red" style="margin-top:8px"><strong>⚠️ Notes:</strong>
    <ul style="margin:4px 0 0 18px">
      <li>Some networks (corporate Wi-Fi / certain ISPs) block port 853 — DNS silently falls back to unencrypted. If needed, add a DoH (443) front-end as backup, but Android Private DNS only supports DoT.</li>
      <li>Never post your DNS address publicly — anyone who grabs it can use your resolver (open-resolver abuse + it burns your VM bandwidth).</li>
      <li>Blocklists usually don't cover every apex domain (e.g. <code>googleadservices.com</code> itself is not listed) — that's normal; real ad traffic runs on subdomains (<code>ad.xxx.com</code>) and those are covered.</li>
    </ul>
  </div>
</div>'''

def gtx(text, target):
    url = ("https://translate.googleapis.com/translate_a/single?client=gtx&sl=zh-TW&tl="
           + target + "&dt=t&q=" + urllib.parse.quote(text))
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    data = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())
    return "".join(seg[0] for seg in data[0])

def split_text_nodes(html):
    """Return list of (is_tag, token) preserving tags; translate only bare text."""
    return re.split(r"(<[^>]+>)", html)

def translate_html(html, target):
    out = []
    for tok in split_text_nodes(html):
        if tok.startswith("<") or not tok.strip():
            out.append(tok)
            continue
        t = tok.strip("\n")
        if t:
            out.append(gtx(t, target))
        else:
            out.append(tok)
    return "".join(out)

SWEEPS = {  # zh-CN residual Cantonese cleanup
    "嘅": "的", "喺": "在", "唔": "不", "咗": "了", "佢": "它", "冇": "没有",
    "嚟": "来", "攞": "拿", "畀": "给", "哋": "们", "啲": "些", "睇": "看",
}
def sweep_cn(t):
    for a, b in SWEEPS.items():
        t = t.replace(a, b)
    return t

def insert(path, section, toc_new, secure_line):
    html = open(path, encoding="utf-8").read()
    assert html.count(secure_line) == 1, f"toc anchor not unique in {path}"
    html = html.replace(secure_line, secure_line + "\n" + toc_new)
    anchor = '<div class="link-block" style="margin-top:16px">'
    assert html.count(anchor) == 1, f"link-block not unique in {path}"
    html = html.replace(anchor, section + "\n\n" + anchor)
    open(path, "w", encoding="utf-8").write(html)
    print("inserted", path)

# root (zh-HK)
insert(BASE + "/index.html", ZH_SECTION,
       '    <a href="#pihole">9 Pi-hole</a>',
       '    <a href="#secure">8 安全</a>')

# en
insert(BASE + "/en/index.html", EN_SECTION,
       '<a href="#pihole">9 Pi-hole</a>',
       '<a href="#secure">8 safety</a>')

# zh-CN: translate zh-HK section (dedent to file's 0-indent style)
cn_sec = translate_html(ZH_SECTION, "zh-CN")
cn_sec = sweep_cn(cn_sec)
cn_sec = "\n".join(l[2:] if l.startswith("  ") else l for l in cn_sec.split("\n"))  # root uses 2-space indent, translated files 0
insert(BASE + "/zh-CN/index.html", cn_sec,
       '<a href="#pihole">9 Pi-hole</a>',
       '<a href="#secure">8 安全</a>')

# ar
ar_sec = translate_html(ZH_SECTION, "ar")
ar_sec = "\n".join(l[2:] if l.startswith("  ") else l for l in ar_sec.split("\n"))
insert(BASE + "/ar/index.html", ar_sec,
       '<a href="#pihole">9 Pi-hole</a>',
       '<a href="#secure">8 السلامة</a>')
print("DONE")