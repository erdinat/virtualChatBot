"""
Öğrenci Profil Sıfırlama — Demo/Sunum Yardımcısı

Belirtilen kullanıcının tüm öğrenme verisini siler:
  1. data/student_logs/<username>.json (mastery, interaction history, diagnostic flag)
  2. data/system_logs/chat_log.jsonl içinden o kullanıcının satırlarını çıkarır
  3. Tarayıcı localStorage temizleme JS snippet'ini ekrana yazar

Önemli: Tarayıcı tarafı silinmedikçe öğrenci "diagnostic yapılmış" sayılır.
JS snippet'ini Chrome DevTools Console'a yapıştırıp ENTER'a basın.

Kullanım:
    python scripts/reset_student.py ayse
    python scripts/reset_student.py ayse --keep-chat-log   (sohbeti koru, sadece state sıfırla)
    python scripts/reset_student.py ayse --dry-run         (silmeden ne olacağını göster)
"""

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

# Proje kökü
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

STUDENT_LOGS = ROOT / "data" / "student_logs"
CHAT_LOG = ROOT / "data" / "system_logs" / "chat_log.jsonl"


def reset_student(username: str, keep_chat_log: bool = False, dry_run: bool = False) -> None:
    print(f"🔄 '{username}' profili sıfırlanıyor (dry-run={dry_run})\n")

    # 1) Öğrenci JSON dosyası
    student_file = STUDENT_LOGS / f"{username}.json"
    if student_file.exists():
        if dry_run:
            print(f"   [silinecek] {student_file}")
        else:
            # Güvenlik için zaman damgalı yedek
            backup = student_file.with_suffix(
                f".bak.{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
            )
            shutil.copy2(student_file, backup)
            student_file.unlink()
            print(f"   ✅ silindi: {student_file.name}  (yedek: {backup.name})")
    else:
        print(f"   ℹ️  {student_file.name} zaten yok — atlanıyor")

    # 2) chat_log.jsonl içinden kullanıcının satırlarını çıkar
    if keep_chat_log:
        print("   ↪️  chat_log.jsonl korunuyor (--keep-chat-log)")
    elif CHAT_LOG.exists():
        kept, removed = [], 0
        for line in CHAT_LOG.read_text(encoding="utf-8").splitlines():
            try:
                e = json.loads(line)
                if e.get("username") == username:
                    removed += 1
                    continue
            except json.JSONDecodeError:
                pass
            kept.append(line)

        if dry_run:
            print(f"   [silinecek] chat_log.jsonl içinden {removed} satır")
        elif removed > 0:
            backup = CHAT_LOG.with_suffix(
                f".bak.{datetime.now().strftime('%Y%m%d-%H%M%S')}.jsonl"
            )
            shutil.copy2(CHAT_LOG, backup)
            CHAT_LOG.write_text("\n".join(kept) + ("\n" if kept else ""), encoding="utf-8")
            print(f"   ✅ chat_log.jsonl: {removed} satır silindi  (yedek: {backup.name})")
        else:
            print(f"   ℹ️  chat_log.jsonl'da '{username}' kaydı yok")
    else:
        print("   ℹ️  chat_log.jsonl yok")

    # 3) Tarayıcı localStorage temizleme komutu
    js_snippet = (
        "(() => {"
        f" const u = '{username}';"
        " const keys = Object.keys(localStorage).filter(k => k.includes('_'+u+'_') || k.endsWith('_'+u));"
        " keys.forEach(k => localStorage.removeItem(k));"
        " console.log('🧹 silindi:', keys);"
        " localStorage.removeItem('access_token');"
        " localStorage.removeItem('sta-auth');"
        " location.reload();"
        " })();"
    )

    print()
    print("─" * 70)
    print("🌐 TARAYICI ADIMI — bunlar olmadan sıfırlama tamamlanmaz:")
    print("─" * 70)
    print()
    print("1. Tarayıcıda http://localhost:5173 sayfasını aç")
    print("2. F12 ile DevTools'u aç, Console sekmesine geç")
    print("3. Aşağıdaki tek satırı yapıştır + ENTER:")
    print()
    print(f"   {js_snippet}")
    print()
    print("Sayfa otomatik yenilenir. Login ekranı görünecek — '{u}/{u}123' ile gir."
          .format(u=username))
    print("İlk ekran: Diagnostic test (sıfırdan başlangıç). ✨")


def main():
    p = argparse.ArgumentParser(description="Demo için öğrenci profil sıfırlayıcı")
    p.add_argument("username", help="Sıfırlanacak kullanıcı adı (örn: ayse)")
    p.add_argument("--keep-chat-log", action="store_true",
                   help="Sohbet kayıtlarını silme (sadece mastery/diagnostic sıfırla)")
    p.add_argument("--dry-run", action="store_true",
                   help="Hiçbir şey silme — sadece ne olacağını göster")
    args = p.parse_args()

    reset_student(args.username, keep_chat_log=args.keep_chat_log, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
