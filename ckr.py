import asyncio
import re
import time
import json
from telethon import TelegramClient, events
from telethon.sessions import StringSession # ১. সেশন ইমপোর্ট


# ================= CONFIG =================
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
SESSION_STRING = os.getenv("SESSION_STRING")
MY_ID = 5162551291


SESSION_STRING ="1BVtsOKQBu2sLHcbFgd4L53AijwcAbY-2zDaAi6Dkb1SsFPK9x91kLRLN9wWwdWk8FKb7erf8fCvXk98iLzqtutlVAVB6d24JpG0DI6BSsGqibofhiIpwx6vcrrOPX7My53vhd01MOGvIHjOrdSgkb2uy5lnCUu8ohH3HqOvOGHvkMAQMRxsdZEGxZsYqU2cg0QBgaOaHAddRjO9ft9g8Exx0GuI1u33PK3AnogkNUnACQ3WAzPOMlHn6Wsd4zlbUb1BQIA5YUSf9LA7v39tlmTSMFNKRWmKAV_vgmmEWsHS-_Dso5FBDb5ZcEdJoosVMpFwtyp1v6hoTlPHjSJsFDDt5B3z6eXg="# ================= CLIENTS =================
client_monitor = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
bot = TelegramClient("SESSION_STRING", API_ID, API_HASH)

# ================= SAFE DATABASE =================
def load_data():
    try:
        with open("users.json", "r") as f:
            data = json.load(f)
    except:
        data = {}

    if "approved" not in data:
        data["approved"] = [MY_ID]
    if "banned" not in data:
        data["banned"] = []
    if "requests" not in data:
        data["requests"] = {}
    return data

def save_data(data):
    with open("users.json", "w") as f:
        json.dump(data, f, indent=2)

data = load_data()

# ================= MEMORY =================
# ================= MEMORY =================
active_users = set()   # Default OFF: /startnotify না দিলে notification যাবে না
user_bins = {}
user_bal_ranges = {}
recent_cards = {}

DEFAULT_BINS = ["4358", "4034", "5113"]
DEFAULT_RANGE = (10.0, 25.0)
REQUEST_COOLDOWN = 600  # 10 minutes

# ================= SAFE SEND FUNCTION =================
async def safe_send(uid, text):
    try:
        await bot.send_message(uid, text)
    except Exception as e:
        err = str(e).lower()
        if "blocked" in err or "deactivated" in err:
            if uid in data["approved"]:
                data["approved"].remove(uid)
            active_users.discard(uid)
            save_data(data)
        print(f"[SEND ERROR] {uid} -> {err}")

# ================= USER HANDLER =================
@bot.on(events.NewMessage)
async def handler(event):
    user_id = event.sender_id
    text = (event.raw_text or "").strip().lower()

    sender = await event.get_sender()
    full_name = f"{sender.first_name or ''} {sender.last_name or ''}".strip()
    username = sender.username or "NoUsername"

    # ================= BAN CHECK =================
    if user_id in data["banned"]:
        await event.respond("🚫 You are banned!")
        return

    # ================= HELP MENU =================
    if text == "/help":
        await event.respond("""🛠 Help Menu

1️⃣ `/setbins 4358,5113,4034` - নির্দিষ্ট BIN ফিল্টার করতে।
2️⃣ `/setrange 10 25` - ব্যালেন্স রেঞ্জ সেট করতে।
3️⃣ `/startnotify` - এলার্ট চালু করতে।
4️⃣ `/stopnotify` - এলার্ট বন্ধ করতে।

⚡ Features:
✔ Smart BIN filter
✔ Balance matching
✔ Instant alerts
""")
        return

    # ================= REQUEST SYSTEM =================
    if text == "/request":
        if user_id in data["approved"]:
            await event.respond("✅ Already approved! 🚀")
            return

        now = time.time()
        last = data["requests"].get(str(user_id))
        if last and (now - last) < REQUEST_COOLDOWN:
            remain = int((REQUEST_COOLDOWN - (now - last)) / 60)
            await event.respond(f"⏳ Pending request!\nTry again after {remain} min")
            return

        data["requests"][str(user_id)] = now
        save_data(data)
        await event.respond("📩 Request sent! Please wait a moment... ⏳")

        await bot.send_message(
            MY_ID,
            f"🔔 NEW REQUEST\n\n👤 Name: {full_name}\n🔗 Username: @{username}\n🆔 ID: `{user_id}`\n\n`/approve {user_id}`"
        )
        return

    # ================= ADMIN COMMANDS (ONLY FOR MY_ID) =================
    if user_id == MY_ID:
        if text == "/admin":
            await event.respond(f"""👑 **ADMIN PANEL**

🆔 Your ID: `{MY_ID}`

━━━━━━━━━━━━━━━━━━━
📌 **USER CONTROL:**
`/approve USER_ID` - ইউজার অ্যাপ্রুভ করুন
`/ban USER_ID` - ইউজার ব্যান করুন

📋 **USER LIST:**
/request_user - পেন্ডিং লিস্ট
/approve_user - অ্যাপ্রুভড লিস্ট
/ban_user - ব্যান লিস্ট

📢 **BROADCAST:**
`/update YOUR_MESSAGE` - সবাইকে মেসেজ দিন
━━━━━━━━━━━━━━━━━━━""")
            return

        # --- LIST REQUEST USERS ---
        if text == "/request_user":
            if not data["requests"]:
                return await event.respond("❌ No pending requests")
            msg = "📩 **Request Users List:**\n\n"
            for uid in data["requests"]:
                try:
                    u = await bot.get_entity(int(uid))
                    name = f"{u.first_name or ''} {u.last_name or ''}".strip()
                    msg += f"👤 {name}\n🆔 `{uid}`\n\n"
                except: msg += f"🆔 `{uid}` | (Unknown)\n\n"
            await event.respond(msg)
            return

        # --- LIST APPROVED USERS ---
        if text == "/approve_user":
            if not data["approved"]:
                return await event.respond("❌ No approved users")
            msg = "✅ **Approved Users List:**\n\n"
            for uid in data["approved"]:
                try:
                    u = await bot.get_entity(int(uid))
                    name = f"{u.first_name or ''} {u.last_name or ''}".strip()
                    msg += f"👤 {name}\n🆔 `{uid}`\n\n"
                except: msg += f"🆔 `{uid}` | (Unknown)\n\n"
            await event.respond(msg)
            return

        # --- LIST BANNED USERS ---
        if text == "/ban_user":
            if not data["banned"]:
                return await event.respond("❌ No banned users")
            msg = "🚫 **Banned Users List:**\n\n"
            for uid in data["banned"]:
                try:
                    u = await bot.get_entity(int(uid))
                    name = f"{u.first_name or ''} {u.last_name or ''}".strip()
                    msg += f"👤 {name}\n🆔 `{uid}`\n\n"
                except: msg += f"🆔 `{uid}` | (Unknown)\n\n"
            await event.respond(msg)
            return

         # --- APPROVE ACTION ---
        if text.startswith("/approve"):
            try:
                uid = int(text.split()[1])

                if uid not in data["approved"]:
                    data["approved"].append(uid)

                if uid in data["banned"]:
                    data["banned"].remove(uid)

                data["requests"].pop(str(uid), None)
                save_data(data)

                # active_users.add(uid) দেওয়া যাবে না
                # approve করলে auto notification চালু হবে না

                await safe_send(
                    uid,
                    "🎉 Approved Successfully!\n\nNotification পেতে /startnotify দিন।"
                )

                await event.respond(f"✅ User `{uid}` approved!")

            except:
                await event.respond("❌ Usage: `/approve user_id`")

            return
        # --- BAN ACTION ---
        if text.startswith("/ban"):
            try:
                uid = int(text.split()[1])
                if uid not in data["banned"]: data["banned"].append(uid)
                if uid in data["approved"]: data["approved"].remove(uid)
                data["requests"].pop(str(uid), None)
                save_data(data)
                active_users.discard(uid)
                await safe_send(uid, "🚫 Account Permanently Banned!")
                await event.respond(f"✅ User `{uid}` banned!")
            except: await event.respond("❌ Usage: `/ban user_id`")
            return

        # --- BROADCAST ---
        if text.startswith("/update"):
            msg_text = event.raw_text.replace("/update", "").strip()
            if not msg_text: return await event.respond("❌ Use: `/update message`")
            sent, failed = 0, 0
            for uid in data["approved"]:
                try:
                    await bot.send_message(uid, f"📢 **UPDATE FROM ADMIN**\n\n{msg_text}")
                    sent += 1
                    await asyncio.sleep(0.3)
                except: failed += 1
            await event.respond(f"✅ Sent: {sent} | ❌ Failed: {failed}")
            return

    # ================= ACCESS BLOCK =================
    if user_id not in data["approved"]:
        await event.respond("🚫 Access Denied! Use /request to apply. 📑")
        return

    # ================= START UI =================
    if text == "/start":
        await event.respond(f"""👋 **Hey, {full_name} Welcome Brother 🚀**

━━━━━━━━━━━━━━━━━━━
💳 **X Stock Filter Bot**

Get **instant alerts** for matching cards — fast, smart, and efficient.

━━━━━━━━━━━━━━━━━━━
⚙️ **Quick Setup (Only 3 Steps)**

🔹 **Step 1:** `/startnotify` 
🔹 **Step 2:** `/setbins 4358,5113,4034`
🔹 **Step 3:** `/setrange 10 25`

━━━━━━━━━━━━━━━━━━━
⏹ **Stop Alerts:** `/stopnotify`
📞 **Need Help?** /help
━━━━━━━━━━━━━━━━━━━""")
        return

    # ================= NOTIFY CONTROLS =================
    if text == "/startnotify":
        active_users.add(user_id)
        user_bins.setdefault(user_id, DEFAULT_BINS)
        user_bal_ranges.setdefault(user_id, DEFAULT_RANGE)
        await event.respond("Your notifications are now successfully active! 🎉")
        return

    if text == "/stopnotify":
        active_users.discard(user_id)
        await event.respond("🔴 Notifications turned off successfully.")
        return

    if text.startswith("/setbins"):
        bins_input = text.replace("/setbins", "").strip()
        if not bins_input:
            return await event.respond("⚠️ Example: `/setbins 4358,5113`")
        user_bins[user_id] = [b.strip() for b in bins_input.split(",")]
        await event.respond(f"✅ BIN লিস্ট সেট হয়েছে: \nYour BINs: {user_bins[user_id]}")
        return

    if text.startswith("/setrange"):
        try:
            parts = text.split()
            mn, mx = parts[1], parts[2]
            user_bal_ranges[user_id] = (float(mn), float(mx))
            await event.respond(f"✅ ব্যালেন্স রেঞ্জ সেট হয়েছে:\nYour Range: {mn} - {mx}")
        except:
            await event.respond("⚠️ Example: `/setrange 10 25`")
        return

# ================= MONITORING LOGIC =================
@client_monitor.on(events.NewMessage)
async def monitor(event):
    try:
        content = event.raw_text or ""
        bin_match = re.search(r"BIN:\s*(\d+)", content)
        bal_match = re.search(r"Balance:\s*USD\s*\$([\d\.,]+)", content)

        if bin_match and bal_match:
            card_bin = bin_match.group(1)
            card_balance = float(bal_match.group(1).replace(",", ""))
            card_id = f"{card_bin}-{card_balance}"

            if card_id in recent_cards and (time.time() - recent_cards[card_id]) < 10:
                return
            recent_cards[card_id] = time.time()

            for user in list(active_users):
                if user in user_bins:
                    if not any(card_bin.startswith(b) for b in user_bins[user]):
                        continue
                if user in user_bal_ranges:
                    mn, mx = user_bal_ranges[user]
                    if not (mn <= card_balance <= mx):
                        continue
                
                await safe_send(user, f"🆕 **Found ${card_balance}**\n\n{content}")
    except Exception as e:
        print(f"MONITOR ERROR: {e}")

# ================= RUN =================
async def main():
    await client_monitor.start()
    await bot.start(bot_token=BOT_TOKEN)
    print("✅ Bot is fully running...")
    await asyncio.gather(client_monitor.run_until_disconnected(), bot.run_until_disconnected())

if __name__ == "__main__":
    asyncio.run(main())