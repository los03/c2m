#!/usr/bin/env python3
# C2ME - User-Agent rotasyonu + proxy + hız

import asyncio
import aiohttp
import requests
import concurrent.futures
import time, secrets, random, string, sys, json, hashlib, subprocess

ACCOUNTS_FILE = "/data/data/com.termux/files/home/c2m_accounts.txt"
PROXIES_FILE = "/data/data/com.termux/files/home/proxies_all.txt"
PW = "asddsa03"
TOR_PROXY = "127.0.0.1:9052"

# ─── User-Agent havuzu (gerçek cihazlar) ───
UA_POOL = [
    'Connected2/3.394.1822300963 (samsung SM-S931B; Android 17; Scale/2.00)',
    'Connected2/3.394.1822300963 (samsung SM-S928B; Android 14; Scale/2.00)',
    'Connected2/3.394.1822300963 (samsung SM-G991B; Android 13; Scale/2.75)',
    'Connected2/3.394.1822300963 (samsung SM-A546B; Android 14; Scale/2.63)',
    'Connected2/3.394.1822300963 (Xiaomi 2312DRA50G; Android 14; Scale/2.75)',
    'Connected2/3.394.1822300963 (Xiaomi M2101K6G; Android 13; Scale/2.75)',
    'Connected2/3.394.1822300963 (Google Pixel 8; Android 14; Scale/2.63)',
    'Connected2/3.394.1822300963 (Google Pixel 7; Android 13; Scale/2.63)',
    'Connected2/3.394.1822300963 (OnePlus CPH2449; Android 14; Scale/2.75)',
    'Connected2/3.394.1822300963 (HUAWEI ELS-NX9; Android 12; Scale/2.75)',
    'Connected2/3.394.1822300963 (OPPO CPH2451; Android 14; Scale/2.75)',
    'Connected2/3.394.1822300963 (vivo V2225; Android 13; Scale/2.75)',
    'Connected2/3.394.1822300963 (realme RMX3630; Android 13; Scale/2.75)',
    'Connected2/3.394.1822300963 (motorola moto g84 5G; Android 13; Scale/2.75)',
    'Connected2/3.394.1822300963 (samsung SM-F946B; Android 14; Scale/2.50)',
]

class C:
    R = '\033[0;31m'; G = '\033[0;32m'; Y = '\033[1;33m'; B = '\033[0;34m'
    M = '\033[0;35m'; C = '\033[0;36m'; W = '\033[1;37m'; D = '\033[0;90m'
    N = '\033[0m'; BOLD = '\033[1m'

def calc_checksum(s):
    A = 0x1003F; OFF = 0x93; M = (1 << 60) - 1
    sb = '15CSD8J1B15A41MAS7D10UPM3G1T5'
    h = 0x1865
    for ch in (s + sb).encode('utf-8'):
        h = (h * A + ch + OFF) & M
    return str(h)

def gen_o():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=32))

def gen_anon():
    pw = secrets.token_hex(20)
    nick = "anon-" + hashlib.sha256(pw.encode()).hexdigest()[:15]
    return nick, pw

def random_ua():
    return random.choice(UA_POOL)

async def fetch_stories(target):
    anon_nick, anon_pw = gen_anon()
    o = gen_o()
    ck = calc_checksum(f"{anon_nick}|{o}|{anon_pw}|{target}|")
    url = f"https://api.c2me.cc/b/get_user_info?user={target}&nick={anon_nick}&password={anon_pw}&o={o}&checksum={ck}"
    try:
        result = await asyncio.to_thread(subprocess.run, [
            "curl", "-s", "--http2", "--max-time", "10", url,
            "-H", f"User-Agent: {random_ua()}",
            "-H", "Accept-Encoding: gzip", "--compressed"
        ], capture_output=True, text=True, timeout=15)
        data = json.loads(result.stdout)
        return [s.get("story_id") for s in data.get("stories", [])]
    except:
        return []

async def like_with_tor(story_id):
    anon_nick, anon_pw = gen_anon()
    o = gen_o()
    ck = calc_checksum(f"{anon_nick}|{o}|{anon_pw}|{story_id}|")
    url = f"https://api.c2me.cc/b/like_story?story_id={story_id}&nick={anon_nick}&password={anon_pw}&o={o}&checksum={ck}"
    try:
        result = await asyncio.to_thread(subprocess.run, [
            "curl", "-s", "--http2", "--max-time", "15",
            "--socks5", TOR_PROXY, "-X", "POST", url,
            "-H", f"User-Agent: {random_ua()}",
            "-H", "content-length: 0",
            "-H", "Accept-Encoding: gzip", "--compressed"
        ], capture_output=True, text=True, timeout=20)
        return '"status": "OK"' in result.stdout
    except:
        return False

async def try_register(target, proxy):
    TS = int(time.time() * 1000) + random.randint(0, 9999)
    U = f"user{TS}"
    E = f"test{TS}@test.com"
    D = secrets.token_hex(8)
    O = gen_o()
    CK = calc_checksum(f"{D}|{E}|{O}|{PW}|{U}|")
    ua = random_ua()  # ← rastgele UA
    headers = {'User-Agent': ua}

    url = f"https://api.c2me.cc/b/register?password={PW}&device_id={D}&checksum={CK}&email={E}&username={U}&o={O}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, proxy=f"http://{proxy}", timeout=5) as r:
                text = await r.text()
                if '"status": "OK"' not in text:
                    return None

                O2 = gen_o()
                CK2 = calc_checksum(f"{target}|{U}|{O2}|{PW}|")
                f_url = f"https://api.c2me.cc/b/follow?follow_nick={target}&nick={U}&password={PW}&o={O2}&checksum={CK2}"
                follow_ok = False
                try:
                    async with session.get(f_url, headers={'User-Agent': random_ua()}, proxy=f"http://{proxy}", timeout=5) as fr:
                        f_text = await fr.text()
                        follow_ok = ('"status": "OK"' in f_text or 'already_following' in f_text)
                except:
                    pass

                with open(ACCOUNTS_FILE, "a") as f:
                    f.write(f"{U}|{PW}\n")

                return {"user": U, "follow": follow_ok, "ua": ua.split('(')[1].split(';')[0] if '(' in ua else '?'}
    except:
        return None

def check_proxy(proxy):
    try:
        r = requests.get('https://api.ipify.org',
            proxies={'http': f'http://{proxy}', 'https': f'http://{proxy}'},
            timeout=3,
            headers={'User-Agent': random_ua()})
        ip = r.text.strip()
        if ip and len(ip) > 5:
            return (proxy, ip)
    except:
        pass
    return None

async def main():
    if len(sys.argv) < 2:
        print("Kullanım: python3 c2m_ua_rotate.py <hedef1> [hedef2] ...")
        sys.exit(1)

    targets = sys.argv[1:]

    with open(PROXIES_FILE) as f:
        proxies = [l.strip() for l in f if l.strip()]

    print(f"{C.M}{C.BOLD}")
    print("╔══════════════════════════════════════════════════════╗")
    print("║       C2ME UA ROTATE - USER-AGENT DEĞİŞİMİ           ║")
    print("╚══════════════════════════════════════════════════════╝")
    print(f"{C.N}")
    print(f"{C.C}🎯 Hedefler: {C.W}{', '.join(targets)}{C.N}")
    print(f"{C.C}📦 Proxy: {C.W}{len(proxies)}{C.N}")
    print(f"{C.C}📱 UA pool: {C.W}{len(UA_POOL)}{C.N}")
    print(f"{C.C}🔄 Ctrl+C ile durdur{C.N}")
    print("")

    stats = {"follow": 0, "like": 0, "fail": 0, "proxy_tested": 0, "ua_used": set()}
    TARGET_SUCCESS = 3  # Her hedef için kaç başarılı hesap
    start_time = time.time()

    try:
        round_num = 0
        while True:
            round_num += 1
            print(f"\n{C.M}{'═'*58}{C.N}")
            print(f"{C.M}🔁 TUR {round_num}{C.N}")
            print(f"{C.M}{'═'*58}{C.N}")

            # Story'ler
            print(f"\n{C.Y}📸 Story'ler çekiliyor...{C.N}")
            stories_map = {}
            for target in targets:
                stories = await fetch_stories(target)
                stories_map[target] = stories
                icon = "📷" if stories else "  "
                print(f"   {icon} {C.W}{target}{C.N}: {stories and C.G or C.D}{len(stories)} story{C.N}")

            for target_idx, target in enumerate(targets):
                print(f"\n{C.C}[{target_idx+1}/{len(targets)}] 🎯 {C.W}{target}{C.N}")
                stories = stories_map.get(target, [])
                target_success = 0

                print(f"   {C.D}Proxy'ler paralel test ediliyor (UA rotasyon)...{C.N}")
                working = []

                with concurrent.futures.ThreadPoolExecutor(max_workers=50) as ex:
                    futures = {ex.submit(check_proxy, p): p for p in proxies}
                    for future in concurrent.futures.as_completed(futures):
                        stats["proxy_tested"] += 1
                        r = future.result()
                        if r:
                            working.append(r)
                            proxy_addr, ip = r
                            print(f"   {C.G}✅ {proxy_addr}{C.N} {C.D}({ip}){C.N}")

                            result = await try_register(target, proxy_addr)

                            if result:
                                if result.get("follow"):
                                    stats["follow"] += 1
                                    stats["ua_used"].add(result["ua"])
                                    print(f"      {C.G}✅ {result['user']} (follow OK){C.N} {C.D}[UA: {result['ua']}]{C.N}")
                                else:
                                    print(f"      {C.Y}⚠️  {result['user']} (follow FAIL){C.N}")

                                if stories:
                                    for sid in stories:
                                        ok = await like_with_tor(sid)
                                        if ok:
                                            stats["like"] += 1
                                            print(f"         {C.G}❤️  {sid} OK{C.N}")
                                        else:
                                            print(f"         {C.R}❤️  {sid} FAIL{C.N}")
                                        await asyncio.sleep(0.2)

                                # Başarılıysa say
                                if result.get("follow"):
                                    target_success += 1
                                    print(f"      {C.G}🎯 {target} için {target_success}/{TARGET_SUCCESS}{C.N}")
                                    if target_success >= TARGET_SUCCESS:
                                        working = []
                                        break
                            else:
                                stats["fail"] += 1
                                print(f"      {C.R}❌ Register fail{C.N}")

                # Tur özeti
                elapsed = time.time() - start_time
                print(f"\n{C.M}{'─'*58}{C.N}")
                print(f"   {C.G}✅ Follow: {stats['follow']}  ❤️  Like: {stats['like']}  ❌ Fail: {stats['fail']}{C.N}")
                print(f"   {C.C}📦 Proxy: {stats['proxy_tested']}  📱 UA: {len(stats['ua_used'])}  ⏱️  {int(elapsed//60)}m {int(elapsed%60)}s{C.N}")
                print(f"{C.M}{'─'*58}{C.N}")

            await asyncio.sleep(1)

    except KeyboardInterrupt:
        elapsed = time.time() - start_time
        print(f"\n\n{C.M}{'═'*58}{C.N}")
        print(f"{C.M}🛑 DURDURULDU{C.N}")
        print(f"{C.M}{'═'*58}{C.N}")
        print(f"   ✅ Follow: {stats['follow']}")
        print(f"   ❤️  Like: {stats['like']}")
        print(f"   ❌ Fail: {stats['fail']}")
        print(f"   📦 Proxy: {stats['proxy_tested']}")
        print(f"   📱 UA: {len(stats['ua_used'])}")
        print(f"   ⏱️  {int(elapsed//60)}m {int(elapsed%60)}s")
        print(f"{C.M}{'═'*58}{C.N}")

if __name__ == "__main__":
    asyncio.run(main())
