# -*- coding: utf-8 -*-

import datetime
import time
from datetime import timezone

import pytz
import whois

import yaml
from jinja2 import Environment, FileSystemLoader
from publicsuffix import PublicSuffixList


# whois参照
def get_whois(host):
    time.sleep(2)
    return whois.whois(host)


# YamlをOpen
f = open("./chk_hosts.yml",encoding='utf-8')
chk_hosts = yaml.load(f)
chk_hosts = chk_hosts['chk_host_list']
#print (chk_hosts)

domain_list = []

# サブドメインや日本語ドメインを正規化する
for chk in chk_hosts:
    hostname = chk['uri']
    if hostname is None:
        next
    normalize_hostname = hostname.encode('idna').decode('utf-8')
    psl = PublicSuffixList()
    domain_list.append(psl.get_public_suffix(normalize_hostname))
#print (domain_list)
uniq_domain_list = list(set(domain_list))
list = []
# 重複を除去し、Whoisを引く
for domain in uniq_domain_list:
    registrar = "　"
    update_date = "　"
    expires_date = "　"
    limit_day = "　"
    try:
        whois_ans = get_whois(domain)
        registrar = whois_ans.registrar
   #     print(domain)
   #     print(whois_ans)
   #     print(type(whois_ans.updated_date))
        if isinstance(whois_ans.updated_date, type(list)):
            whois_update_date = whois_ans.updated_date[0]
        else:
            whois_update_date = whois_ans.updated_date

        if isinstance(whois_ans.expiration_date, type(list)):
            whois_expiration_date = whois_ans.expiration_date[0]
        else:
            whois_expiration_date = whois_ans.expiration_date

    except whois.parser.PywhoisError as e:
        print("Whoisに見つからない")
        continue
    print(domain)
  #  print(whois_ans)
    if whois_update_date is None:
        print("Whois情報取得に失敗")
        continue

    # そのまま処理するとJSTと認識されて時刻がずれるので、不細工だけど時間をずらす
    update_date = whois_update_date - datetime.timedelta(hours=9)
    expires_date = whois_expiration_date - datetime.timedelta(hours=9)
    jp = pytz.timezone('Asia/Tokyo')
   # print(update_date.astimezone(jp))

    diff = (expires_date.astimezone(jp) - datetime.datetime.now(jp)
            ) // datetime.timedelta(days=1)
   # print(update_date)
   # print(expires_date)
   # print(diff)
    whois_propaty = {"domain": domain, "registrar": registrar,
                     "update_date": update_date, "expires_date": expires_date, "limit_day": diff}
    list.append(whois_propaty)

# 残り日数とホスト名でソート
list = sorted(list, key=lambda x: (x["limit_day"], x["domain"]))

# HTML作成
env = Environment(loader=FileSystemLoader('./', encoding='utf8'))
templete = env.get_template('./domain_limit.html.j2')
data = {"list": list}
output = templete.render(data)

# Windows環境だとエンコード指定しないと出力がSJISになる。
with open('domain_limit.html', 'w', encoding='utf-8') as f:
    f.write(output)


print("完了!")
