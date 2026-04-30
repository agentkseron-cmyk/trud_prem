import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime

def get_nicks_and_clanicons_from_clans(first=1, last=500):
    res = dict()  # nick: clan_icon_url
    for clannum in range(first, last+1):
        url = f'https://www.ereality.ru/clan{clannum}.html'
        print(f'Парсим клан: {url}')
        try:
            r = requests.get(url, timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')

            # ищем значек клана (берём первый в таблице): <img src="/clan/82.gif" ...>
            clan_img = soup.find('img', src=lambda x: x and x.startswith('https://img.ereality.ru/clan/'))
            clan_icon_url = clan_img['src'] if clan_img else ''

            # игроки — <img ... inf.gif ... title="Информация о персонаже Имя">
            imgs = soup.find_all('img', src='https://img.ereality.ru/inf.gif')
            for img in imgs:
                title = img.get('title', '')
                if 'Информация о персонаже' in title:
                    nick = title.split('Информация о персонаже')[-1].strip()
                    if nick:
                        res[nick] = clan_icon_url
            time.sleep(0.15)
        except Exception as e:
            print(f'Ошибка при обработке клана {clannum}: {str(e)}')
    return res

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

nick_to_clanicon = get_nicks_and_clanicons_from_clans(first_clan, last_clan)
nicks = list(nick_to_clanicon.keys())
print(f"Собрано уникальных ников: {len(nicks)}")
print('Первые 10 ников:', nicks[:10])

results = []
for idx, nick in enumerate(nicks, 1):
    nick2, count = get_awards_for_nick(nick)
    print(f"{idx}/{len(nicks)} : {nick2} — {count} премий")
    clan_icon = nick_to_clanicon[nick]
    results.append({'nick': nick2, 'count': count, 'clan_icon': clan_icon})

results = sorted(results, key=lambda x: x['count'], reverse=True)

dt_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

html = f"""
<html>
<head>
    <meta charset="utf-8">
    <title>Рейтинг по трудовым премиям</title>
    <style>
        body {{font-family: 'Segoe UI', Arial, sans-serif; background: #f5f7fa; margin: 0; padding: 50px 0;}}
        .container {{width: 90%%; max-width: 700px; margin: auto; background: #fff; border-radius: 18px; box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.12); padding: 30px 36px;}}
        h2 {{text-align: center; color: #224488; margin-bottom: 8px; letter-spacing: 1px;}}
        .date-gen {{text-align:center; color:#666; margin-bottom: 24px; font-size: 0.95em;}}
        table {{width: 100%%; border-collapse: collapse;}}
        th, td {{border: 1px solid #e3e9f0; padding: 12px 10px; text-align: center; transition: background 0.2s;}}
        th {{background: #f0f6ff; color: #224488; font-size: 1.05em;}}
        tr:nth-child(even) td {{background: #f5faff;}}
        tr:hover td {{background: #e6eeff;}}
        .first {{background: #ffd700 !important; font-weight: bold;}}
        .second {{background: #c0c0c0 !important;}}
        .third {{background: #e0b07d !important;}}
        .clanicon {{vertical-align: middle; margin-right:3px;}}
        .nickcell {{text-align:left;}}
    </style>
</head>
<body>
    <div class='container'>
        <h2>ТОП по трудовым премиям</h2>
        <div class='date-gen'>Выгрузка сделана: {dt_str}</div>
        <table>
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
    icon_html = f"<img src='{x['clan_icon']}' width='15' height='12' class='clanicon'>" if x['clan_icon'] else ''
    html += f"<tr class='{row_class}'><td>{i}</td><td class='nickcell'>{icon_html}{x['nick']}</td><td>{x['count']}</td></tr>"

html += """
        </table>
    </div>
</body>
</html>
"""

with open("rating_trud_premiya_clans.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Готово! Файл rating_trud_premiya_clans.html сохранён.")