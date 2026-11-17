"""Hand-written HELD-OUT test set (written independently of the training templates).
Limitations: small (n~80), written by the project authors, not collected from real
victims, so reported metrics are optimistic compared with real-world traffic."""
import json, pathlib
OUT = pathlib.Path(__file__).resolve().parents[1] / "datasets" / "test.jsonl"
S, L = 1, 0
T = [
 # ---- scams: English
 ("Dad, I'm at the police station, I got into a fight. Please transfer Rs 40,000 to this account right now, don't call mom.", S, "en"),
 ("This is Mr. Sharma from the Reserve Bank. Your account has suspicious activity. Read out the OTP sent to your phone to secure it.", S, "en"),
 ("You have been selected in the KBC lucky draw, prize Rs 25 lakh. Send Rs 2,500 as tax to claim.", S, "en"),
 ("Hi uncle, this is Arjun, I changed my number. I am stuck at the airport, send 15000 urgently on GPay, I will return tonight.", S, "en"),
 ("Customs has seized a parcel in your name. Pay Rs 30,000 penalty immediately or you will be arrested. Do not tell anyone.", S, "en"),
 ("Your electricity will be disconnected tonight. Call this number and install QuickSupport so our agent can verify your meter.", S, "en"),
 ("Dear user, SBI YONO account is blocked. Update PAN at http://sbi-yono-verify.top/kyc within 1 hour.", S, "en"),
 ("Money request of Rs 49,999 from cashback.reward7788@paytmx. Tap approve to receive your reward.", S, "en"),
 ("Sir by mistake I transferred Rs 12,000 into your account, please send it back to me immediately, I am in hospital.", S, "en"),
 ("Enter your UPI PIN on the next screen to receive Rs 8,000 refund from the shopping site.", S, "en"),
 ("Hello grandma, I am in an accident and the doctor wants payment now. Send Rs 60,000. Please keep this between us.", S, "en"),
 ("Your SIM will be deactivated in 2 hours due to KYC. Share the verification code sent by SMS to continue.", S, "en"),
 ("Cyber crime police: your Aadhaar is linked to a money laundering case. You are under digital arrest, stay on video call and transfer funds for verification.", S, "en"),
 ("Task job: like YouTube videos earn Rs 5000 daily. First deposit Rs 1,000 as security. Join our Telegram now.", S, "en"),
 # ---- scams: Tanglish / Tamil / Hindi
 ("Sir, ungal bank account block aagapovuthu. OTP ippove sollunga, illana avasaram problem aagum.", S, "tanglish"),
 ("Appa naan Vignesh pesuren, vandi accident aayiduchu, hospital-la 30000 panam venum udane anuppunga, amma-kitta sollaatheenga.", S, "tanglish"),
 ("Congrats! Ungalukku 10 lakh lottery vizhundhirukku. Claim panna 5000 rupees anuppunga.", S, "tanglish"),
 ("Refund process panna UPI PIN enter pannunga, udane panam vandhurum.", S, "tanglish"),
 ("உங்கள் வங்கி கணக்கு இன்று நிறுத்தப்படும். உடனே ஓடிபி எண்ணை சொல்லுங்கள்.", S, "ta"),
 ("உங்கள் மகன் கைது செய்யப்பட்டுள்ளார். வழக்கை முடிக்க உடனே 50000 பணம் அனுப்புங்கள். யாரிடமும் சொல்லாதீர்கள்.", S, "ta"),
 ("Papa mera accident ho gaya hai, turant 25000 rupees bhejo, mummy ko mat batana.", S, "hi"),
 ("Aapka bank account band hone wala hai. Abhi OTP batao aur AnyDesk install karo.", S, "hi"),
 ("Aapko lottery lagi hai 5 lakh ki. Paise lene ke liye pehle 2000 rupees bhejo.", S, "hi"),
 # ---- legit: bank/payment messages (hard negatives)
 ("HDFC Bank: Rs 12,500.00 credited to a/c **4821 on 14-11-26 by UPI/Ref 603412345678. Avl bal Rs 58,300.", L, "en"),
 ("Dear customer, never share your OTP, PIN or CVV with anyone, including bank staff. Stay safe from fraud.", L, "en"),
 ("123456 is your OTP for Swiggy login. Do not share it with anyone.", L, "en"),
 ("ICICI Bank: Rs 3,400 debited from a/c XX9087 for Netflix subscription. If not you, call the number on your card.", L, "en"),
 ("SBI Alert: Beware of fraudsters. SBI never asks for OTP or PIN over phone or SMS.", L, "en"),
 ("Your Airtel recharge of Rs 299 is successful. Validity 28 days. Txn ID 88223.", L, "en"),
 ("PhonePe: Rs 450 paid to Zomato. UPI Ref 4433221100. Check balance in your bank app.", L, "en"),
 ("Axis Bank: Your credit card bill of Rs 8,210 is due on 20th Nov. Pay via the Axis Mobile app to avoid late fee.", L, "en"),
 ("Amazon: Your refund of Rs 1,299 has been processed to your original payment method and will reflect in 3-5 days.", L, "en"),
 ("TNEB: Your electricity bill of Rs 1,120 for consumer no 0422 is generated. Last date 25-11-2026.", L, "en"),
 # ---- legit: everyday (some with scam-looking words)
 ("Urgent: please send me the project report before 5 pm, the client is waiting.", L, "en"),
 ("Can you send Rs 500 to Ravi for the cab? I will pay you back tomorrow.", L, "en"),
 ("Mom, I reached the hostel safely. Will call after dinner.", L, "en"),
 ("Dad, my phone battery is dying, I will call from my friend's phone if needed. All good here.", L, "en"),
 ("Hi, the plumber is coming at 4 pm. Please keep Rs 800 ready to pay him.", L, "en"),
 ("Reminder: parent-teacher meeting tomorrow at 10 am. Attendance is important.", L, "en"),
 ("Your OLA ride is arriving in 3 minutes. Share the ride PIN 4821 with the driver to start the trip.", L, "en"),
 ("Happy birthday! Sending you a small gift of Rs 1000 on GPay, treat yourself.", L, "en"),
 ("Our office WiFi password has changed. I will tell you in person tomorrow.", L, "en"),
 ("Doctor appointment confirmed for tomorrow 11 am at City Hospital. Please carry previous reports.", L, "en"),
 ("The bank manager called to say my loan documents are ready. I will collect them on Monday.", L, "en"),
 ("Anna just paid me Rs 2,000 for the tickets, thanks for arranging everything.", L, "en"),
 ("Brother, your friend's marriage is on Sunday. Come early morning, food will be great.", L, "en"),
 ("Please install the Zoom app before tomorrow's class. Link will be shared by the teacher.", L, "en"),
 ("Your Flipkart order is out for delivery today. Keep Rs 499 cash ready if you chose cash on delivery.", L, "en"),
 ("News: RBI warns citizens about digital arrest scams; police say never transfer money to unknown callers.", L, "en"),
 # ---- legit: Tanglish / Tamil / Hindi
 ("Amma naan office-la irundhu 8 manikku varuven, dinner ready pannunga.", L, "tanglish"),
 ("Nalaiku morning 7 manikku temple-kku pogalam, ready-a irunga.", L, "tanglish"),
 ("Ungal account-la Rs 3000 credit aagirukku. Ref 55421. -Indian Bank", L, "tanglish"),
 ("Kadai-la milk vaanginu vaanga, naan seekiram varuven.", L, "tanglish"),
 ("பிறந்தநாள் வாழ்த்துக்கள்! இன்று மாலை வீட்டுக்கு வாங்க.", L, "ta"),
 ("உங்கள் கணக்கில் ரூ 2,000 வரவு வைக்கப்பட்டது. நன்றி.", L, "ta"),
 ("நாளை பள்ளியில் பெற்றோர் கூட்டம் காலை 10 மணிக்கு நடைபெறும்.", L, "ta"),
 ("Kal subah 9 baje meeting hai, documents saath le aana.", L, "hi"),
 ("Aapke account mein Rs 5000 credit hue hain. Ref 99231. -SBI", L, "hi"),
 ("Beta ghar pahunch gaya? Khana bana diya hai, jaldi aa jao.", L, "hi"),
]
OUT.write_text("\n".join(json.dumps({"text": t, "label": y, "lang": l, "source": "handwritten"}, ensure_ascii=False) for t, y, l in T), encoding="utf-8")
print(f"wrote {len(T)} held-out test rows (scam={sum(1 for _,y,_ in T if y)}) -> {OUT}")
