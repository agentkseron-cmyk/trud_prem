import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
import json

PREMIUM_TYPES = [
    ("Ксенотеки", "Дар Джека (Ксенотеки)"),
    ("Опыт", "Дар Джека (Опыт)"),
    ("Хаотические бои", "Дар Джека (Хаотические бои)"),
    ("PvP-баллы", "Дар Джека (PvP-баллы)"),
    ("Эктоплазма", "Дар Джека (Эктоплазма)"),
    ("Бои с пиратами", "Дар Джека (Бои с пиратами)"),
]

def get_clan_info_and_nicks(first=1, last=500):
    clans = dict()
    nick2clan = dict()
    for clannum in range(first, last+1):
        url = f'https://www.ereality.ru/clan{clannum}.html'
        print(f'Парсим клан: {url}')
        try:
            r = requests.get(url, timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            clan_img = soup.find('img', src=lambda x: x and x.startswith('https://img.ereality.ru/clan/'))
            clan_icon_url = clan_img['src'] if clan_img else ''
            clan_name = ''
            if clan_img:
                b = clan_img.find_next('b')
                if b:
                    clan_name = b.text.strip()
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
                    "nicks": nicks
                }
            time.sleep(0.1)
        except Exception as e:
            print(f'Ошибка при обработке клана {clannum}: {str(e)}')
    return clans, nick2clan

def get_awards_for_nick(nick):
    url = f'https://www.ereality.ru/~{nick}'
    try:
        r = requests.get(url, timeout=10)
        page = r.text
        start = page.find("<title>")
        end = page.find("</title>", start)
        nick2 = page[start+7:end] if start != -1 and end != -1 else nick
        nick2 = nick2.replace('Информация о', '').strip()
        counts = {}
        total = 0
        for key, label in PREMIUM_TYPES:
            c = page.count(label)
            counts[key] = c
            total += c
        return nick2, counts, total
    except Exception as e:
        print(f"Ошибка для ника {nick}: {e}")
        return nick, {k:0 for k,_ in PREMIUM_TYPES}, 0

# --- Основная часть ---

first_clan, last_clan = 1, 500
clans, nick2clan = get_clan_info_and_nicks(first_clan, last_clan)

results = []
nick2_awards = {}
for idx, nick in enumerate(nick2clan.keys(), 1):
    nick2, counts, total = get_awards_for_nick(nick)
    print(f"{idx}/{len(nick2clan)} : {nick2} — всего {total}")
    rec = {
        'nick': nick2,
        'raw_nick': nick,
        'count_total': total,
        'clan_id': nick2clan[nick],
        'counts': counts
    }
    results.append(rec)
    nick2_awards[nick] = rec

# По умолчанию сортируем по "Всего"
results = sorted(results, key=lambda x: x['count_total'], reverse=True)

# Клановый рейтинг с объединением 1-8 в один клан
superclan_ids = [1,2,3,4,5,6,7,8]
superclan_name = clans[1]["name"] if 1 in clans else "Суперклан"
superclan_icon = clans[1]["icon"] if 1 in clans else ""
superclan_nicks = []
superclan_awards_sum = 0
superclan_class_sums = {k:0 for k,_ in PREMIUM_TYPES}

clan_results = []
for clan_id, data in clans.items():
    if clan_id in superclan_ids:
        for nick in data["nicks"]:
            r = nick2_awards.get(nick, {'count_total':0, 'counts':{}})
            superclan_nicks.append(nick)
            superclan_awards_sum += r['count_total']
            for k in superclan_class_sums.keys():
                superclan_class_sums[k] += r['counts'].get(k,0)
    else:
        awards_sum = 0
        class_sums = {k: 0 for k,_ in PREMIUM_TYPES}
        for nick in data["nicks"]:
            r = nick2_awards.get(nick, {'count_total':0, 'counts':{}})
            awards_sum += r['count_total']
            for k in class_sums.keys():
                class_sums[k] += r['counts'].get(k,0)
        num_members = len(data["nicks"])
        clan_results.append({
            'clan_id': clan_id,
            'name': data["name"],
            'icon': data["icon"],
            'count_total': awards_sum,
            'class_sums': class_sums,
            'cnt': num_members
        })
if superclan_nicks:
    clan_results.append({
        'clan_id': 1,
        'name': superclan_name,
        'icon': superclan_icon,
        'count_total': superclan_awards_sum,
        'class_sums': superclan_class_sums,
        'cnt': len(superclan_nicks)
    })
clan_results = sorted(clan_results, key=lambda x: x["count_total"], reverse=True)

dt_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# HTML с доп. столбцами, НО без "Без категории"
headers_html = "<th data-sortby='total' class='sortable selected'>Место</th><th>Ник</th><th class='sortable selected' data-sortby='Всего'>Всего</th>"
headers_clan_html = "<th data-sortby='total' class='sortable selected'>Место</th><th>Клан</th><th class='sortable selected' data-sortby='Всего'>Всего</th><th>Кол-во участников</th>"
for k, _ in PREMIUM_TYPES:
    headers_html += f"<th class='sortable' data-sortby='{k}'>{k}</th>"
    headers_clan_html += f"<th class='sortable' data-sortby='{k}'>{k}</th>"

# Данные для сортировки в JS
js_players_data = []
for x in results:
    entry = {
        "nick": x["nick"],
        "raw_nick": x["raw_nick"],
        "clan_id": x["clan_id"],
        "total": x["count_total"],
        "counts": x["counts"],
    }
    js_players_data.append(entry)
js_clans_data = []
for x in clan_results:
    entry = {
        "name": x["name"],
        "icon": x["icon"],
        "total": x["count_total"],
        "cnt": x["cnt"],
        "class_sums": x["class_sums"],
    }
    js_clans_data.append(entry)

# Формируем HTML
html = f"""
<html>
<head>
    <meta charset="utf-8">
    <title>Рейтинг по трудовым премиям</title>
    <style>
        body {{font-family: 'Segoe UI', Arial, sans-serif; background: #f5f7fa; margin: 0; padding: 50px 0;}}
        .container {{width: 95%%; max-width: 1200px; margin: auto; background: #fff; border-radius: 18px; box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.12); padding: 30px 16px;}}
        h2 {{text-align: center; color: #224488; margin-bottom: 8px; letter-spacing: 1px;}}
        .date-gen {{text-align:center; color:#666; margin-bottom: 24px; font-size: 0.95em;}}
        .table-wrap {{display: flex; justify-content: center;}}
        table {{border-collapse: collapse; margin-bottom: 24px;}}
        th, td {{border: 1px solid #e3e9f0; padding: 7px 12px; text-align: center; transition: background 0.2s; font-size: 0.97em;}}
        th {{background: #f0f6ff; color: #224488; font-size: 1em; cursor:pointer;}}
        th.selected {{background-color: #e4eaff;}}
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
        @media (max-width: 900px) {{
            .container {{padding: 5px 2px;}}
            .table-wrap {{display:block;}}
            table {{font-size:0.88em;}}
            th, td {{padding: 4px 4px;}}
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
                <tr id='headerPlayers'>{headers_html}</tr>
                <tbody id="players_tbody">
                <!-- JS будет вставлять строки -->
                </tbody>
            </table>
            </div>
        </div>
        <div id="tabcontent1" style="display:none;">
            <div class="table-wrap">
            <table id="clantable">
                <tr id='headerClans'>{headers_clan_html}</tr>
                <tbody id="clans_tbody">
                <!-- JS будет вставлять строки -->
                </tbody>
            </table>
            </div>
        </div>
    </div>
    <script>
        var players_data = {json.dumps(js_players_data, ensure_ascii=False)};
        var clans_data = {json.dumps(js_clans_data, ensure_ascii=False)};
        var clan_icons = {json.dumps({str(cid):clans[cid]["icon"] for cid in clans}, ensure_ascii=False)};
        var used_clan_names = {json.dumps({str(cid):clans[cid]["name"] for cid in clans}, ensure_ascii=False)};

        var reward_types = ["Всего",{",".join([f'"{x[0]}"' for x in PREMIUM_TYPES])}];
        var selectedReward = "Всего";
        function renderPlayers(sortBy) {{
            var data = players_data.slice();
            data.sort(function(a,b){{
                if(sortBy=="Всего") return b.total-a.total;
                return (b.counts[sortBy]||0)-(a.counts[sortBy]||0);
            }});
            var tb = "";
            for(let i=0;i<data.length;i++) {{
                let rowcls = "";
                if(i==0) rowcls='first';
                else if(i==1) rowcls='second';
                else if(i==2) rowcls='third';
                let cicon = clan_icons[data[i].clan_id+""] || "";
                let nhtml = "<a href='https://www.ereality.ru/~"+encodeURIComponent(data[i].raw_nick)+"' target='_blank'>"+data[i].nick+"</a>";
                tb += `<tr class='${{rowcls}}'><td>${{i+1}}</td><td class='nickcell'>${{cicon.length?`<img src='${{cicon}}' width='15' height='12' class='clanicon'>`:""}}${{nhtml}}</td><td>${{data[i].total}}</td>`
                for(let j=0;j<{len(PREMIUM_TYPES)};j++) tb += `<td>${{data[i].counts[reward_types[j+1]]||0}}</td>`;
                tb += "</tr>";
            }}
            document.getElementById("players_tbody").innerHTML = tb;
        }}
        function renderClans(sortBy) {{
            var data = clans_data.slice();
            data.sort(function(a,b){{
                if(sortBy=="Всего") return b.total-a.total;
                return (b.class_sums[sortBy]||0)-(a.class_sums[sortBy]||0);
            }});
            var tb = "";
            for(let i=0;i<data.length;i++) {{
                let rowcls = "";
                if(i==0) rowcls='first';
                else if(i==1) rowcls='second';
                else if(i==2) rowcls='third';
                let cicon = data[i].icon || "";
                let nhtml = "<b>"+data[i].name+"</b>";
                tb += `<tr class='${{rowcls}}'><td>${{i+1}}</td><td>${{cicon.length?`<img src='${{cicon}}' width='15' height='12' class='clanicon'>`:""}}${{nhtml}}</td><td>${{data[i].total}}</td><td>${{data[i].cnt}}</td>`
                for(let j=0;j<{len(PREMIUM_TYPES)};j++) tb += `<td>${{data[i].class_sums[reward_types[j+1]]||0}}</td>`;
                tb += "</tr>";
            }}
            document.getElementById("clans_tbody").innerHTML = tb;
        }}

        function setColHeaderSelected(tblId, headerRowId, colName) {{
            const ths = document.getElementById(headerRowId).getElementsByTagName("th");
            for(let i=0;i<ths.length;i++) ths[i].classList.remove("selected");
            for(let i=0;i<ths.length;i++)
                if(ths[i].getAttribute("data-sortby")==colName) ths[i].classList.add("selected");
        }}

        function showTab(n) {{
            var tabs = document.getElementsByClassName('tab');
            for (var i = 0; i < tabs.length; i++) tabs[i].classList.remove('selected');
            tabs[n].classList.add('selected');
            document.getElementById('tabcontent0').style.display = n==0?'':'none';
            document.getElementById('tabcontent1').style.display = n==1?'':'none';
        }}
        // Сортировка и ререндер при клике на столбец
        document.addEventListener("DOMContentLoaded", function(){{
            renderPlayers("Всего");
            renderClans("Всего");
            // Для персонажей
            document.getElementById("headerPlayers").addEventListener("click", function(e){{
                if(e.target.tagName=="TH" && e.target.classList.contains("sortable")) {{
                    var col = e.target.getAttribute("data-sortby");
                    if(col!=selectedReward) {{
                        selectedReward=col;
                        setColHeaderSelected('chartable','headerPlayers',col);
                        renderPlayers(col);
                    }}
                }}
            }});
            // Для кланов
            document.getElementById("headerClans").addEventListener("click", function(e){{
                if(e.target.tagName=="TH" && e.target.classList.contains("sortable")) {{
                    var col = e.target.getAttribute("data-sortby");
                    setColHeaderSelected('clantable','headerClans',col);
                    renderClans(col);
                }}
            }});
        }});
    </script>
</body>
</html>
"""

with open("rating_trud_premiya_clans.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Готово! Файл rating_trud_premiya_clans.html сохранён.")
