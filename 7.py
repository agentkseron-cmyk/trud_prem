import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime

def get_clan_info_and_nicks(first=1, last=500):
    clans = dict()  # clan_id -> {"name":..., "icon":..., "nicks":[nick, ...]}
    nick2clan = dict()  # nick -> clan_id
    for clannum in range(first, last+1):
        url = f'https://www.ereality.ru/clan{clannum}.html'
        print(f'Парсим клан: {url}')
        try:
            r = requests.get(url, timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')

            # Значок клана
            clan_img = soup.find('img', src=lambda x: x and x.startswith('https://img.ereality.ru/clan/'))
            clan_icon_url = clan_img['src'] if clan_img else ''

            # Название клана
            clan_name = ''
            if clan_img:
                b = clan_img.find_next('b')
                if b:
                    clan_name = b.text.strip()

            # Игроки
            imgs = soup.find_all('img', src='https://img.ereality.ru/inf.gif')
            nicks = []
            for img in imgs:
                title = img.get('title', '')
                if 'Информация о персонаже' in title:
                    nick = title.split('Информация о персонаже')[-1].strip()
                    if nick:
                        nicks.append(nick)
                        nick2clan[nick] = clannum

            if nicks:
                clans[clannum] = {
                    "name": clan_name,
                    "icon": clan_icon_url,
                    "nicks": nicks  # сохраняем только реальных игроков
                }
            time.sleep(0.1)
        except Exception as e:
            print(f'Ошибка при обработке клана {clannum}: {str(e)}')
    return clans, nick2clan

def get_awards_for_nick(nick):
    url = f'https://www.ereality.ru/~{nick}'
    try:
        r = requests.get(url, timeout=10)
        count = r.text.count('Трудовая премия')
        start = r.text.find("<title>")
        end = r.text.find("</title>", start)
        nick2 = r.text[start+7:end] if start != -1 and end != -1 else nick
        nick2 = nick2.replace('Информация о', '').strip()
        return nick2, count
    except Exception as e:
        print(f"Ошибка для ника {nick}: {e}")
        return nick, 0

# --- Основная часть ---

first_clan, last_clan = 1, 500
clans, nick2clan = get_clan_info_and_nicks(first_clan, last_clan)

results = []
nick2_awards = {}
for idx, nick in enumerate(nick2clan.keys(), 1):
    nick2, count = get_awards_for_nick(nick)
    print(f"{idx}/{len(nick2clan)} : {nick2} — {count} премий")
    results.append({
        'nick': nick2,
        'raw_nick': nick,
        'count': count,
        'clan_id': nick2clan[nick]
    })
    nick2_awards[nick] = count

results = sorted(results, key=lambda x: x['count'], reverse=True)

# Клановый рейтинг с объединением 1-8 в один клан
superclan_ids = [1,2,3,4,5,6,7,8]
superclan_name = clans[1]["name"] if 1 in clans else "Суперклан"
superclan_icon = clans[1]["icon"] if 1 in clans else ""
superclan_nicks = []
superclan_awards_sum = 0

clan_results = []
for clan_id, data in clans.items():
    if clan_id in superclan_ids:
        superclan_nicks.extend(data["nicks"])
        superclan_awards_sum += sum(nick2_awards.get(nick, 0) for nick in data["nicks"])
    else:
        awards_sum = sum(nick2_awards.get(nick, 0) for nick in data["nicks"])
        num_members = len(data["nicks"])
        clan_results.append({
            'clan_id': clan_id,
            'name': data["name"],
            'icon': data["icon"],
            'count': awards_sum,
            'cnt': num_members
        })

# Добаляем объединенный клан
if superclan_nicks:
    clan_results.append({
        'clan_id': 1,
        'name': superclan_name,
        'icon': superclan_icon,
        'count': superclan_awards_sum,
        'cnt': len(superclan_nicks)
    })

clan_results = sorted(clan_results, key=lambda x: x["count"], reverse=True)

dt_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

html = f"""
<html>
<head>
    <meta charset="utf-8">
    <title>Рейтинг по трудовым премиям</title>
    <style>
        body {{font-family: 'Segoe UI', Arial, sans-serif; background: #f5f7fa; margin: 0; padding: 50px 0;}}
        .container {{width: 95%%; max-width: 950px; margin: auto; background: #fff; border-radius: 18px; box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.12); padding: 30px 36px;}}
        h2 {{text-align: center; color: #224488; margin-bottom: 8px; letter-spacing: 1px;}}
        .date-gen {{text-align:center; color:#666; margin-bottom: 24px; font-size: 0.95em;}}
        .table-wrap {{display: flex; justify-content: center;}}
        table {{border-collapse: collapse; margin-bottom: 24px;}}
        th, td {{border: 1px solid #e3e9f0; padding: 9px 18px; text-align: center; transition: background 0.2s;}}
        th {{background: #f0f6ff; color: #224488; font-size: 1.05em;}}
        tr:nth-child(even) td {{background: #f5faff;}}
        tr:hover td {{background: #e6eeff;}}
        .first {{background: #ffd700 !important; font-weight: bold;}}
        .second {{background: #c0c0c0 !important;}}
        .third {{background: #e0b07d !important;}}
        .clanicon {{vertical-align: middle; margin-right:3px;}}
        .nickcell {{text-align:left;}}
        .tabs {{
           display: flex; border-bottom:1px solid #d7e2f3; margin-bottom:18px;
        }}
        .tab {{
           padding: 9px 24px; border: 1px solid #d7e2f3; border-bottom: none; background:#eff4fb; color: #224488; 
           cursor:pointer; font-weight:500;}}
        .tab.selected {{background: #fff; color: #224488; font-weight:bold;}}
        @media (max-width: 700px) {{
            .container {{padding: 5px 2px;}}
            .table-wrap {{display:block;}}
        }}
    </style>
</head>
<body>
    <div class='container'>
        <h2>ТОП по трудовым премиям</h2>
        <div class='date-gen'>Выгрузка сделана: {dt_str}</div>
        <div class="tabs">
            <div class="tab selected" onclick="showTab(0)">Рейтинг персонажей</div>
            <div class="tab" onclick="showTab(1)">Рейтинг кланов</div>
        </div>
        <div id="tabcontent0">
            <div class="table-wrap">
            <table id="chartable">
                <tr><th>Место</th><th>Ник</th><th>Трудовых премий</th></tr>
"""
for i, x in enumerate(results, 1):
    row_class = ''
    if i == 1:
        row_class = 'first'
    elif i == 2:
        row_class = 'second'
    elif i == 3:
        row_class = 'third'
    clan_icon = clans[x['clan_id']]["icon"] if x['clan_id'] in clans else ""
    icon_html = f"<img src='{clan_icon}' width='15' height='12' class='clanicon'>" if clan_icon else ''
    nick_html = f'<a href="https://www.ereality.ru/~{x["raw_nick"]}" target="_blank">{x["nick"]}</a>'
    html += f"<tr class='{row_class}'><td>{i}</td><td class='nickcell'>{icon_html}{nick_html}</td><td>{x['count']}</td></tr>"

html += """
            </table>
            </div>
        </div>
        <div id="tabcontent1" style="display:none;">
            <div class="table-wrap">
            <table id="clantable">
                <tr><th>Место</th><th>Клан</th><th>Сумма премий</th><th>Кол-во участников</th></tr>
"""
for i, x in enumerate(clan_results, 1):
    row_class = ''
    if i == 1:
        row_class = 'first'
    elif i == 2:
        row_class = 'second'
    elif i == 3:
        row_class = 'third'
    icon_html = f"<img src='{x['icon']}' width='15' height='12' class='clanicon'>" if x["icon"] else ""
    name_html = f"{icon_html}<b>{x['name']}</b>"
    html += f"<tr class='{row_class}'><td>{i}</td><td>{name_html}</td><td>{x['count']}</td><td>{x['cnt']}</td></tr>"

html += """
            </table>
            </div>
        </div>
    </div>
    <script>
        function showTab(n) {
            var tabs = document.getElementsByClassName('tab');
            for (var i = 0; i < tabs.length; i++) tabs[i].classList.remove('selected');
            tabs[n].classList.add('selected');
            document.getElementById('tabcontent0').style.display = n==0?'':'none';
            document.getElementById('tabcontent1').style.display = n==1?'':'none';
        }
    </script>
</body>
</html>
"""

with open("rating_trud_premiya_clans.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Готово! Файл rating_trud_premiya_clans.html сохранён.")
