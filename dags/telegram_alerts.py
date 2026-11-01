import urllib.request
import json
import ssl
import os

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

def send_telegram_failure_alert(context):
    dag_id = context.get('task_instance').dag_id
    task_id = context.get('task_instance').task_id
    execution_date = context.get('execution_date').strftime("%Y-%m-%d %H:%M:%S")
    exception = context.get('exception')

    message = (
        f"🚨 <b>Airflow Task Failed!</b>\n\n"
        f"<b>DAG:</b> <code>{dag_id}</code>\n"
        f"<b>Task:</b> <code>{task_id}</code>\n"
        f"<b>Time:</b> {execution_date}\n"
        f"<b>Error:</b> <code>{exception}</code>"
    )

    url = f"https://149.154.167.220/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = json.dumps({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }).encode('utf-8')

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(
        url, 
        data=payload, 
        headers={
            'Content-Type': 'application/json',
            'Host': 'api.telegram.org'
        }
    )
    
    try:
        urllib.request.urlopen(req, context=ctx, timeout=10)
        print("警报已成功发送！")
    except Exception as e:
        print(f"发送 Telegram 提醒时出错： {e}")
