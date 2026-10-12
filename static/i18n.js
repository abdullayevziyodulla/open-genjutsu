/* UI-only localization. Never translate form values, request payloads, files or provider errors. */
(() => {
  'use strict';
  const storageKey = 'open-genjutsu-language';
  const supported = value => value === 'uz' ? 'uz' : 'en';
  let language = 'en';
  try { language = supported(localStorage.getItem(storageKey)); } catch (_) { /* Private browser: session only. */ }

  // English source messages are the stable keys; unknown messages keep their original text.
  const uz = {
    'Open Genjutsu · Video character studio': 'Open Genjutsu · Video personaj studiyasi',
    'Open Genjutsu · Quick start': 'Open Genjutsu · Boshlash qo‘llanmasi',
    'Open Genjutsu home': 'Open Genjutsu bosh sahifasi',
    'OPEN SOURCE': 'OCHIQ KODLI',
    'Motion transfer': 'Harakatni ko‘chirish',
    'Motion transfer studio': 'Harakatni ko‘chirish studiyasi',
    'Original audio': 'Asl audio',
    'ORIGINAL AUDIO': 'ASL AUDIO',
    '＋ New video': '＋ Yangi video',
    'Settings': 'Sozlamalar',
    'API settings': 'API sozlamalari',
    'Connect APIs': 'API hisoblarini ulash',
    'Close settings': 'Sozlamalarni yopish',
    'Language': 'Til',
    'English is the default. Your choice is saved in this browser.': 'Standart til — inglizcha. Tanlovingiz shu brauzerda saqlanadi.',
    'Reference video': 'Namuna video',
    'Add a reference video': 'Namuna video qo‘shing',
    'to extract motion': 'harakatni ajratib olish uchun',
    'Video duration: 4 to 30 seconds': 'Video davomiyligi: 4–30 soniya',
    'Original video': 'Asl video',
    'Remove selected video': 'Tanlangan videoni olib tashlash',
    'Advanced preparation': 'Qo‘shimcha tayyorlash sozlamalari',
    'Preparation method': 'Tayyorlash usuli',
    'Depth + subject mask': 'Chuqurlik + obyekt niqobi',
    'Face mesh · experimental': 'Yuz to‘ri · tajriba',
    'Depth + face mesh · experimental': 'Chuqurlik + yuz to‘ri · tajriba',
    'Subject to replace': 'Almashtiriladigan obyekt',
    'Depth model': 'Chuqurlik modeli',
    'Alternate depth model': 'Muqobil chuqurlik modeli',
    'Mesh modes work best with one centered speaker and need the optional worker. Preparation uses Replicate credits for vocals, depth and masks.': 'Yuz to‘ri rejimlari kadr markazidagi bitta odam bilan yaxshiroq ishlaydi va qo‘shimcha worker talab qiladi. Ovoz, chuqurlik va niqoblarni tayyorlash Replicate kreditlarini sarflaydi.',
    'Preparation uses Replicate credits.': 'Tayyorlash Replicate kreditlarini sarflaydi.',
    'Prepare motion →': 'Harakatni tayyorlash →',
    'Character & generation': 'Personaj va video yaratish',
    'Character reference': 'Personaj namunasi',
    'Add your characters': 'Personajlaringizni qo‘shing',
    'Photo or identity video · up to 2 characters': 'Surat yoki shaxs videosi · 2 tagacha personaj',
    'One clear character photo': 'Personajning bitta aniq surati',
    'Your characters': 'Personajlaringiz',
    'Manage ↗': 'Boshqarish ↗',
    'One reference per character.': 'Har bir personaj uchun bitta namuna.',
    'Add your character': 'Personajingizni qo‘shing',
    'Photo or identity reference': 'Surat yoki shaxs namunasi',
    'Add a second character · optional': 'Ikkinchi personajni qo‘shish · ixtiyoriy',
    'Second character': 'Ikkinchi personaj',
    'Optional · a different person': 'Ixtiyoriy · boshqa odam',
    'Custom prompt': 'Maxsus ko‘rsatma',
    'Describe the replacement': 'Almashtirishni tasvirlang',
    'Generation engine': 'Video yaratish modeli',
    'Model': 'Model',
    'Quality': 'Sifat',
    'Wan uses the original motion and one photo. It does not use a custom prompt or the depth composite.': 'Wan asl harakat va bitta suratdan foydalanadi. Maxsus ko‘rsatma yoki chuqurlik kompoziti ishlatilmaydi.',
    'Provider & billing details': 'Provayder va to‘lov tafsilotlari',
    'Connect provider': 'Provayderni ulash',
    'Provider error details': 'Provayder xatosi tafsilotlari',
    'Confirm your request': 'So‘rovingizni tasdiqlang',
    'Exact prompt sent to the model': 'Modelga yuboriladigan aniq ko‘rsatma',
    'Prepare your video, then review the motion guidance in Motion preview.': 'Videoni tayyorlang, keyin Harakat ko‘rinishi bo‘limida natijani tekshiring.',
    'Review draft request →': 'Sinov so‘rovini tekshirish →',
    'Review 480p draft request →': '480p sinov so‘rovini tekshirish →',
    'Review 720p request →': '720p so‘rovini tekshirish →',
    'Generate 720p video (billed) →': '720p video yaratish (pulli) →',
    'Retry draft (billed)': 'Sinovni qayta yaratish (pulli)',
    'Generate reviewed draft': 'Tekshirilgan sinovni yaratish',
    'Workspace views': 'Ish maydoni bo‘limlari',
    '▱ History': '▱ Tarix',
    '◉ Motion preview': '◉ Harakat ko‘rinishi',
    '▶ Results': '▶ Natijalar',
    'ⓘ How it works': 'ⓘ Qanday ishlaydi',
    'Add a reference video and your character to begin.': 'Boshlash uchun namuna video va personajingizni qo‘shing.',
    'Your videos': 'Videolaringiz',
    'Saved locally. Pick a video to continue.': 'Kompyuteringizda saqlangan. Davom etish uchun videoni tanlang.',
    'Loading saved videos…': 'Saqlangan videolar yuklanmoqda…',
    'One video. A new character.': 'Bitta video. Yangi personaj.',
    'Add the source motion and your character on the left.': 'Chap tomonda asl video va personajingizni qo‘shing.',
    'Prepare, review, then generate with your own API keys.': 'Tayyorlang, tekshiring, keyin o‘z API kalitlaringiz bilan yarating.',
    'Motion preserved': 'Harakat saqlanadi',
    'Original soundtrack': 'Asl ovoz yo‘lagi',
    'Preview selection': 'Ko‘rinishni tanlash',
    'Download input ↓': 'Kirish videosini yuklab olish ↓',
    'What should I check?': 'Nimani tekshirish kerak?',
    "Watch the whole clip. Check the subject's hair, hands and clothing, missing mask areas, background spill and flicker. For mesh modes, inspect the face tracking. Listen to the embedded pitched vocals. Fix problems before generating.": 'Videoni to‘liq ko‘ring. Soch, qo‘l va kiyimlar, niqobdagi bo‘shliqlar, fonning niqobga kirishi va miltillashni tekshiring. Yuz to‘ri rejimida yuz kuzatuvini tekshiring. Qo‘shilgan balandlatilgan ovozni tinglang. Video yaratishdan oldin xatolarni tuzating.',
    'Input review required.': 'Kirish videosini tekshirish kerak.',
    'I watched the entire prepared clip; the mask or tracking is aligned throughout.': 'Tayyorlangan videoni to‘liq ko‘rdim; niqob yoki kuzatuv butun video davomida mos.',
    'Approve input': 'Kirish videosini tasdiqlash',
    'Needs fixing': 'Tuzatish kerak',
    'Audio stems': 'Ajratilgan audio yo‘laklari',
    'Your result': 'Natijangiz',
    'Your generated video will appear here.': 'Yaratilgan videongiz shu yerda paydo bo‘ladi.',
    'Review the request before any billed generation.': 'Pulli video yaratishdan oldin so‘rovni tekshiring.',
    '480P DRAFT': '480P SINOV',
    'Download video ↓': 'Videoni yuklab olish ↓',
    'Ready for higher resolution?': 'Yuqoriroq aniqlikka tayyormisiz?',
    'HD is a separate billed render.': 'HD alohida pulli yaratish bosqichidir.',
    'Approve HD render': 'HD yaratishni tasdiqlash',
    'Submitted prompt & task ID': 'Yuborilgan ko‘rsatma va vazifa ID raqami',
    'Download raw generated result': 'Dastlabki yaratilgan natijani yuklab olish',
    'Import an externally generated video': 'Boshqa joyda yaratilgan videoni import qilish',
    'Upload generated result': 'Yaratilgan natijani yuklash',
    "Restore your source's original audio": 'Asl videoning audiosini tiklash',
    'Generated result': 'Yaratilgan natija',
    'Restore original audio': 'Asl audioni tiklash',
    'How it works': 'Qanday ishlaydi',
    'Add your video & character': 'Video va personajingizni qo‘shing',
    'The source video supplies motion. Your reference supplies the replacement identity.': 'Asl video harakatni beradi. Namuna esa yangi personajning qiyofasini beradi.',
    'Prepare & review': 'Tayyorlang va tekshiring',
    'Preparation uses Replicate credits. Watch the complete motion guidance and approve its mask or tracking before generation.': 'Tayyorlash Replicate kreditlarini sarflaydi. Yaratishdan oldin harakat videosini to‘liq ko‘rib, niqob yoki kuzatuvni tasdiqlang.',
    'Generate & download': 'Yarating va yuklab oling',
    'Review the exact request and estimated price. The downloaded result restores the complete original soundtrack.': 'Aniq so‘rov va taxminiy narxni tekshiring. Yuklab olingan natijada to‘liq asl ovoz yo‘lagi tiklanadi.',
    'Setup guide ↗': 'Sozlash qo‘llanmasi ↗',
    'MIT licensed. Your own API accounts pay for inference. No subscription to this project.': 'MIT litsenziyali. Model xarajatlari o‘z API hisoblaringiz orqali to‘lanadi. Bu loyiha uchun obuna talab qilinmaydi.',
    'Open Genjutsu · MIT licensed · Local workspace · Bring your own API keys.': 'Open Genjutsu · MIT litsenziyasi · Mahalliy ish maydoni · O‘z API kalitlaringizdan foydalaning.',
    "Saved in this project's local .env. Keys are never displayed back. Saving settings does not run a model or check your balance.": 'API sozlamalari loyihaning mahalliy .env faylida saqlanadi. Kalitlar qayta ko‘rsatilmaydi. Saqlash modelni ishga tushirmaydi yoki balansni tekshirmaydi.',
    'Video generation provider': 'Video yaratish provayderi',
    'Replicate token': 'Replicate tokeni',
    'For video preparation. Leave blank to keep the saved token.': 'Videoni tayyorlash uchun. Saqlangan tokenni qoldirish uchun bo‘sh qoldiring.',
    'Paste your own token': 'O‘z tokeningizni kiriting',
    'Private Oxen repository': 'Shaxsiy yopiq Oxen repozitoriysi',
    'Create a private repository in your Oxen account for generation inputs.': 'Kirish fayllari uchun Oxen hisobingizda yopiq repozitoriy yarating.',
    'Save settings': 'Sozlamalarni saqlash',
    'Oxen generation key': 'Oxen video yaratish kaliti',
    'Oxen API key': 'Oxen API kaliti',
    'Paste your own Oxen key': 'O‘z Oxen kalitingizni kiriting',
    'Save Oxen key': 'Oxen kalitini saqlash',
    'Lec generation key': 'Lec video yaratish kaliti',
    'Lec API key': 'Lec API kaliti',
    'Paste your own Lec key': 'O‘z Lec kalitingizni kiriting',
    'Save Lec key': 'Lec kalitini saqlash',
    'Uploads': 'Yuklash',
    'Saved characters': 'Saqlangan personajlar',
    'Close character picker': 'Personaj tanlash oynasini yopish',
    'Character slot': 'Personaj o‘rni',
    'optional': 'ixtiyoriy',
    'Use a clear portrait or identity video for this character.': 'Bu personaj uchun aniq portret yoki shaxs videosidan foydalaning.',
    'Use a clear portrait or identity video for Character 1.': '1-personaj uchun aniq portret yoki shaxs videosidan foydalaning.',
    'Use one clear portrait photo. Wan does not accept identity videos.': 'Bitta aniq portret suratidan foydalaning. Wan shaxs videosini qabul qilmaydi.',
    'Choose a photo of a second, different person. This is not another angle of Character 1.': 'Ikkinchi, boshqa odamning suratini tanlang. Bu 1-personajning boshqa rakursi emas.',
    'Upload media': 'Fayl yuklash',
    'Choose a file or drop it here': 'Faylni tanlang yoki shu yerga tashlang',
    'Files stay in your local workspace until you explicitly prepare or generate.': 'Tayyorlash yoki yaratishni boshlamaguningizcha fayllar mahalliy ish maydonida qoladi.',
    'Each slot represents a different person.': 'Har bir o‘rin boshqa odam uchun.',
    'Done': 'Tayyor',
    'Choose a model': 'Modelni tanlang',
    'Close model picker': 'Model tanlash oynasini yopish',
    'Search models or providers': 'Model yoki provayderni qidiring',
    'Search models': 'Modellarni qidirish',
    'AVAILABLE IN OPEN GENJUTSU': 'OPEN GENJUTSU’DA MAVJUD',
    'Choosing a model never submits a generation. Connect your own provider account in API settings.': 'Model tanlash video yaratishni boshlamaydi. API sozlamalarida o‘z provayder hisobingizni ulang.',
    'Prepared video + character identity': 'Tayyorlangan video + personaj qiyofasi',
    'Image identity + prepared motion guidance': 'Suratdagi qiyofa + tayyorlangan harakat',
    'Single-photo replacement with original motion': 'Asl harakat bilan bitta surat orqali almashtirish',
    'Prepared-video reference editing': 'Tayyorlangan video namunasi orqali tahrirlash',
    '480p draft · 1080p final': '480p sinov · 1080p yakuniy',
    '480p preview · new 720p render': '480p sinov · yangi 720p video',
    '720p generation': '720p video yaratish',
    'No matching models.': 'Mos model topilmadi.',
    'Selecting model…': 'Model tanlanmoqda…',
    'This saved job keeps its provider. Start a new video to use another provider.': 'Bu saqlangan vazifa o‘z provayderini saqlaydi. Boshqa provayder uchun yangi video boshlang.',
    'Output quality': 'Natija sifati',
    'Close quality picker': 'Sifat tanlash oynasini yopish',
    'Separate billed render after your draft is ready': 'Sinov tayyor bo‘lgach, alohida pulli video yaratish',
    '720p · current output': '720p · joriy natija',
    '720p · new generation': '720p · yangi video',
    '1080p · final render': '1080p · yakuniy video',
    'Loading local characters…': 'Mahalliy personajlar yuklanmoqda…',
    'Only your local job references appear here.': 'Bu yerda faqat mahalliy vazifalaringizdagi namunalar ko‘rsatiladi.',
    'No saved characters yet. Upload a reference; it is saved when you prepare or generate.': 'Hali saqlangan personaj yo‘q. Namuna yuklang; tayyorlash yoki yaratishda saqlanadi.',
    'Add another character': 'Yana bir personaj qo‘shish',
    'Choose a supported character photo.': 'Qo‘llab-quvvatlanadigan personaj suratini tanlang.',
    'Choose a supported photo or identity video.': 'Qo‘llab-quvvatlanadigan surat yoki shaxs videosini tanlang.',
    'Choose a video file.': 'Video faylini tanlang.',
    'Key saved. Access and current pricing are checked before submission; keep enough credit for this draft.': 'Kalit saqlandi. Yuborishdan oldin kirish va joriy narx tekshiriladi; sinov uchun yetarli kredit saqlang.',
    'Add your Oxen API key. Generation has not started; you can review the request below.': 'Oxen API kalitingizni kiriting. Video yaratish boshlanmagan; quyida so‘rovni tekshirishingiz mumkin.',
    'Key saved. Check your Lec account has enough balance before generating.': 'Kalit saqlandi. Yaratishdan oldin Lec hisobingizda yetarli mablag‘ borligini tekshiring.',
    'Add your key to enable generation. You can review the request first.': 'Yaratishni yoqish uchun kalitingizni kiriting. Avval so‘rovni tekshirishingiz mumkin.',
    'Approve a new billed 720p generation. It may differ from this preview.': 'Yangi pulli 720p yaratishni tasdiqlang. U bu sinovdan farq qilishi mumkin.',
    'Render this same draft at 1080p using its saved draft task ID. This is a separate billed render; Oxen drafts expire after seven days.': 'Saqlangan sinov vazifasi ID raqami bilan shu videoni 1080p yarating. Bu alohida pulli bosqich; Oxen sinovlari yetti kundan so‘ng tugaydi.',
    'Approve & generate new 720p →': 'Tasdiqlash va yangi 720p yaratish →',
    'Approve & render 1080p final →': 'Tasdiqlash va 1080p yakuniy yaratish →',
    'Wan 2.2 · Character replacement': 'Wan 2.2 · Personajni almashtirish',
    'Seedance 2.5 · Prepared-video reference': 'Seedance 2.5 · Tayyorlangan video namunasi',
    'Seedance 2.5 · Image identity': 'Seedance 2.5 · Suratdagi qiyofa',
    'Preview playback failed. Download the saved MP4 to inspect it.': 'Videoni ko‘rsatib bo‘lmadi. Tekshirish uchun saqlangan MP4 faylini yuklab oling.',
    'Prepared input': 'Tayyorlangan kirish',
    'Original': 'Asl video',
    'Depth': 'Chuqurlik',
    'Mask': 'Niqob',
    'Prepared video + isolated vocals pitched +3': 'Tayyorlangan video + 3 yarim tonga balandlatilgan ajratilgan ovoz',
    'Saved depth composite + isolated vocals pitched +3': 'Saqlangan chuqurlik kompoziti + 3 yarim tonga balandlatilgan ajratilgan ovoz',
    'Exact depth colors from the model': 'Modeldan olingan asl chuqurlik ranglari',
    'Full subject mask': 'Obyektning to‘liq niqobi',
    'Isolated vocals ↓': 'Ajratilgan ovoz ↓',
    'Vocals +3 ↓': 'Ovoz +3 ↓',
    'Music stem ↓': 'Musiqa yo‘lagi ↓',
    'Saved reference · click to replace': 'Saqlangan namuna · almashtirish uchun bosing',
    'View prediction on Replicate ↗': 'Replicate’da vazifani ko‘rish ↗',
    'Open retry →': 'Qayta urinishni ochish →',
    'Open revised input →': 'Tuzatilgan kirishni ochish →',
    'Change reference or prompt →': 'Namuna yoki ko‘rsatmani o‘zgartirish →',
    'Verifying and uploading the saved media. Generation starts once Oxen accepts the request; its task ID will appear here.': 'Saqlangan fayllar tekshirilmoqda va yuklanmoqda. Oxen so‘rovni qabul qilgach, yaratish boshlanadi va vazifa ID raqami shu yerda ko‘rinadi.',
    'Generation is running remotely. This page shows the task ID and progress. Your video will appear below after download and original-audio restoration.': 'Video masofada yaratilmoqda. Bu sahifada vazifa ID raqami va holati ko‘rinadi. Yuklash va asl audioni tiklashdan so‘ng video quyida paydo bo‘ladi.',
    'No generation was submitted. The repaired upload path can reuse your reviewed video, portrait, and prompt.': 'Yaratish so‘rovi yuborilmadi. Tuzatilgan yuklash yo‘li tekshirilgan video, portret va ko‘rsatmadan qayta foydalanishi mumkin.',
    'Your video is ready in Results.': 'Videongiz Natijalar bo‘limida tayyor.',
    'Replicate blocked this request. Your source and approved preparation are saved. Open an editable copy to change the inputs.': 'Replicate bu so‘rovni blokladi. Asl video va tasdiqlangan tayyorlash saqlangan. Kirishni o‘zgartirish uchun tahrirlanadigan nusxani oching.',
    'The saved request will not be retried automatically. Check the provider task and any charges before starting another attempt.': 'Saqlangan so‘rov avtomatik takrorlanmaydi. Yangi urinishdan oldin provayderdagi vazifa va to‘lovlarni tekshiring.',
    'Upload failed · not generating': 'Yuklash muvaffaqiyatsiz · video yaratilmayapti',
    'Blocked by Replicate': 'Replicate blokladi',
    'Generation failed': 'Video yaratish muvaffaqiyatsiz',
    'Generation canceled': 'Video yaratish bekor qilindi',
    'Request saved': 'So‘rov saqlandi',
    'Cannot refresh generation status. The remote request may still be running.': 'Yaratish holatini yangilab bo‘lmadi. Masofadagi so‘rov hali ishlayotgan bo‘lishi mumkin.',
    'Review and approve the input first.': 'Avval kirish videosini tekshiring va tasdiqlang.',
    'Request ready. Review it below, then click Generate.': 'So‘rov tayyor. Quyida tekshiring, keyin yaratish tugmasini bosing.',
    'Submitting…': 'Yuborilmoqda…',
    'Oxen key saved. Review the prepared input and exact request before generating.': 'Oxen kaliti saqlandi. Yaratishdan oldin tayyorlangan kirish va aniq so‘rovni tekshiring.',
    'Lec key saved. Review your request before generating.': 'Lec kaliti saqlandi. Yaratishdan oldin so‘rovni tekshiring.',
    'Preparing retry…': 'Qayta urinish tayyorlanmoqda…',
    'Uploading and preparing your video…': 'Videongiz yuklanmoqda va tayyorlanmoqda…',
    'Prepare your original video first.': 'Avval asl videongizni tayyorlang.',
    'Restoring your entire original audio…': 'To‘liq asl audio tiklanmoqda…',
    'Video ready with original audio.': 'Video asl audio bilan tayyor.',
    'Creating a new billed 720p generation from the reviewed input…': 'Tekshirilgan kirishdan yangi pulli 720p video yaratilmoqda…',
    'Rendering the approved draft at 1080p…': 'Tasdiqlangan sinov 1080p formatda yaratilmoqda…',
    'Prepared input approved after full-clip visual review.': 'Tayyorlangan kirish to‘liq ko‘rib chiqilgach tasdiqlandi.',
    'Input needs correction. Submission is blocked.': 'Kirishni tuzatish kerak. Yuborish bloklangan.',
    'Open API settings to add your Replicate token for preparation.': 'Tayyorlash uchun Replicate tokenini kiritish maqsadida API sozlamalarini oching.',
    'Generation is running. Your result downloads automatically.': 'Video yaratilmoqda. Natija avtomatik yuklab olinadi.',
    'This request is saved. See its status above.': 'Bu so‘rov saqlangan. Holati yuqorida ko‘rsatilgan.',
    'Preparing motion guidance. Keep this workspace open.': 'Harakat videosi tayyorlanmoqda. Ish maydonini ochiq qoldiring.',
    '1. Prepare your source video to start.': '1. Boshlash uchun asl videoni tayyorlang.',
    '2. Watch and approve the prepared input in Motion preview.': '2. Harakat ko‘rinishi bo‘limida tayyorlangan kirishni ko‘rib, tasdiqlang.',
    '3. Confirm the cost and generate your reviewed request.': '3. Narxni tasdiqlang va tekshirilgan so‘rovni yarating.',
    '3. Add a character reference and review your draft request.': '3. Personaj namunasini qo‘shing va sinov so‘rovini tekshiring.',
    'Settings saved locally. No inference was submitted.': 'Sozlamalar mahalliy saqlandi. Model so‘rovi yuborilmadi.',
    'Selected original · not prepared': 'Asl video tanlangan · hali tayyorlanmagan',
    'Selected locally. Prepare uploads this video to your preparation provider.': 'Mahalliy tanlangan. Tayyorlash bu videoni tayyorlash provayderingizga yuklaydi.',
    'Result ready': 'Natija tayyor',
    'Needs attention': 'Tekshirish kerak',
    'Processing': 'Ishlanmoqda',
    'Input saved': 'Kirish saqlangan',
    'Your saved videos will appear here.': 'Saqlangan videolaringiz shu yerda paydo bo‘ladi.',
    'Saved videos unavailable.': 'Saqlangan videolarni ochib bo‘lmadi.',
    'Back to studio': 'Studiyaga qaytish',
    'QUICK START': 'BOSHLASH QO‘LLANMASI',
    'A new character. The same performance.': 'Yangi personaj. O‘sha ijro.',
    'Open Genjutsu runs on your computer. Hosted inference is paid through your own API accounts.': 'Open Genjutsu kompyuteringizda ishlaydi. Masofadagi model xarajatlari o‘z API hisoblaringiz orqali to‘lanadi.',
    '1. Connect your accounts': '1. Hisoblaringizni ulang',
    'Open API settings. Add Replicate for video preparation, then choose a generation provider. Oxen also needs its key and an existing private namespace/repository for inputs. Saving keys does not check your balance or submit a model call.': 'API sozlamalarini oching. Tayyorlash uchun Replicate’ni ulang, keyin video yaratish provayderini tanlang. Oxen uchun kalit va kirish fayllariga mavjud yopiq namespace/repozitoriy ham kerak. Kalit saqlash balansni tekshirmaydi yoki model so‘rovini yubormaydi.',
    '2. Prepare and review': '2. Tayyorlang va tekshiring',
    'Upload a 4–30 second video. Prepare creates motion guidance and may use Replicate credits. Watch the entire prepared clip before approving. Check the mask, hands, hair, clothing and cuts. Use advanced settings only when needed.': '4–30 soniyali video yuklang. Tayyorlash harakat videosini yaratadi va Replicate kreditlarini sarflashi mumkin. Tasdiqlashdan oldin butun videoni ko‘ring. Niqob, qo‘l, soch, kiyim va kadr almashishini tekshiring. Qo‘shimcha sozlamalarni faqat kerak bo‘lganda ishlating.',
    '3. Replace and generate': '3. Almashtiring va yarating',
    "Add a character reference and describe the replacement. The optional second character is a different person. Review the exact request and estimate, then generate. The model's quality and billing rules still apply.": 'Personaj namunasini qo‘shing va almashtirishni tasvirlang. Ixtiyoriy ikkinchi personaj boshqa odamdir. Aniq so‘rov va taxminiy narxni tekshiring, keyin yarating. Modelning sifat va to‘lov qoidalari amal qiladi.',
    '4. Download your result': '4. Natijangizni yuklab oling',
    'The result keeps the full original soundtrack. You can return to saved jobs from the library. HD is a separate billed action. Failed or uncertain requests are never silently retried.': 'Natijada to‘liq asl ovoz yo‘lagi saqlanadi. Saqlangan vazifalarga tarixdan qaytishingiz mumkin. HD alohida pulli amal. Muvaffaqiyatsiz yoki holati noaniq so‘rovlar yashirincha takrorlanmaydi.',
    'MIT licensed. No bundled model weights, subscription or commercial companion app.': 'MIT litsenziyali. Model vaznlari, obuna yoki tijoriy yordamchi ilova qo‘shilmagan.',
    'Oxen bills per output second: $0.111 at 480p. Reviewed media uploads to your private Oxen storage and uses verified expiring download links; no preparation is rerun.': 'Oxen har bir yaratilgan soniya uchun to‘lov oladi: 480p uchun $0.111. Tekshirilgan fayllar yopiq Oxen xotirangizga yuklanadi va tasdiqlangan vaqtinchalik havolalardan foydalaniladi; tayyorlash takrorlanmaydi.',
    'Lec lists ¥4.50 per generation, plus private uploads: $0.05/video and $0.01/image. Review the exact request first.': 'Lec’da har bir yaratish ¥4.50, qo‘shimcha yopiq yuklashlar: video uchun $0.05 va surat uchun $0.01. Avval aniq so‘rovni tekshiring.',
    'Review your prepared input and references, then create a 480p preview.': 'Tayyorlangan kirish va namunalarni tekshiring, keyin 480p sinov yarating.',
    'Prepared clip retained. Change the reference or prompt before creating a new preview.': 'Tayyorlangan video saqlangan. Yangi sinovdan oldin namuna yoki ko‘rsatmani o‘zgartiring.',
    'Previous attempt blocked by Replicate (E005). Change the reference or prompt; your prepared clip is retained.': 'Oldingi urinishni Replicate blokladi (E005). Namuna yoki ko‘rsatmani o‘zgartiring; tayyorlangan video saqlangan.',
    'Wan 2.2 is ready to replace the character using your original video and saved photo.': 'Wan 2.2 asl video va saqlangan surat orqali personajni almashtirishga tayyor.',
    'Generation failed: Replicate rejected the input (E006).': 'Video yaratish muvaffaqiyatsiz: Replicate kirishni rad etdi (E006).',
    'Generation failed. No preview was produced.': 'Video yaratish muvaffaqiyatsiz. Sinov yaratilmagan.',
    'Generation canceled. No preview was produced.': 'Video yaratish bekor qilindi. Sinov yaratilmagan.',
    'Replicate blocked the input or output as sensitive (E005). No preview was produced.': 'Replicate kirish yoki natijani cheklangan deb blokladi (E005). Sinov yaratilmagan.',
    'Preview ready with the original source audio restored.': 'Sinov asl video audiosi tiklangan holda tayyor.',
    'Result collection needs attention. The saved prediction will not be resubmitted.': 'Natijani olishni tekshirish kerak. Saqlangan so‘rov qayta yuborilmaydi.',
    'Generation finished. Downloading the video and restoring original audio…': 'Video yaratish tugadi. Video yuklab olinmoqda va asl audio tiklanmoqda…',
    'The provider reports an unknown task state. Inspect the saved task; do not submit another request blindly.': 'Provayder vazifa holatini noma’lum deb ko‘rsatmoqda. Saqlangan vazifani tekshiring; holatni bilmay yangi so‘rov yubormang.',
    'Uploading references and submitting the preview…': 'Namunalar yuklanmoqda va sinov so‘rovi yuborilmoqda…',
    'Submission was attempted, but its outcome is uncertain. Check the provider before retrying.': 'Yuborishga urinish bo‘lgan, lekin natijasi noaniq. Takrorlashdan oldin provayderni tekshiring.',
    'Lec Seedance 2.5 · review your prepared input and request to generate 720p.': 'Lec Seedance 2.5 · 720p yaratish uchun tayyorlangan kirish va so‘rovni tekshiring.',
    'Oxen Seedance 2.5 · reviewed depth/SAM input ready for a 480p draft.': 'Oxen Seedance 2.5 · tekshirilgan depth/SAM kirishi 480p sinovga tayyor.'
  };
  const templates = [
    [/^Character ([12])$/, n => `${n}-personaj`],
    [/^Character ([12]) reference$/, n => `${n}-personaj namunasi`],
    [/^Replace character ([12])$/, n => `${n}-personajni almashtirish`],
    [/^Remove character ([12])$/, n => `${n}-personajni olib tashlash`],
    [/^Video ([a-f0-9]{6})$/, id => `Video ${id}`],
    [/^(\d+p) draft(  ✓)?$/, (q, mark = '') => `${q} sinov${mark}`],
    [/^(\d+p) generation(  ✓)?$/, (q, mark = '') => `${q} video yaratish${mark}`],
    [/^Quality · (\d+p)( preview)?$/, (q, preview) => `Sifat · ${q}${preview ? ' sinov' : ''}`],
    [/^Create (\d+p) preview →$/, q => `${q} sinov yaratish →`],
    [/^Generate 480p draft \(~\$(\d+\.\d+)\) →$/, cost => `480p sinov yaratish (~$${cost}) →`],
    [/^Generate reviewed 480p draft( \(~\$\d+\.\d+\))? →$/, (cost = '') => `Tekshirilgan 480p sinovni yaratish${cost} →`],
    [/^Download (\d+p) video ↓$/, q => `${q} videoni yuklab olish ↓`],
    [/^(\d+P) · ORIGINAL AUDIO$/, q => `${q} · ASL AUDIO`],
    [/^Your (\d+p) video will appear here when generation finishes\.$/, q => `Yaratish tugagach, ${q} videongiz shu yerda paydo bo‘ladi.`],
    [/^Retry (\d+p) preview \(billed\) →$/, q => `${q} sinovni qayta yaratish (pulli) →`],
    [/^Uploading to (Oxen|Replicate|Lec)…$/, p => `${p}’ga yuklanmoqda…`],
    [/^Generating (\d+p) video…$/, q => `${q} video yaratilmoqda…`],
    [/^(\d+p) video ready$/, q => `${q} video tayyor`],
    [/^(Elapsed: |Request duration: )(\d+)m (\d+)s$/, (kind, m, s) => `${kind === 'Elapsed: ' ? 'O‘tgan vaqt' : 'So‘rov davomiyligi'}: ${m} daq ${s} son`],
    [/^· (Oxen|Replicate|Lec) task (.+)$/, (p, id) => `· ${p} vazifasi ${id}`],
    [/^Upload failed before generation\. No request was sent to (Oxen|Replicate|Lec)\.$/, p => `Yaratishdan oldin yuklash muvaffaqiyatsiz. ${p}’ga so‘rov yuborilmadi.`],
    [/^Generating video on (Oxen|Replicate|Lec)… This page checks for updates automatically\.$/, p => `${p}’da video yaratilmoqda… Bu sahifa yangilanishlarni avtomatik tekshiradi.`],
    [/^Request accepted\. Waiting for (Oxen|Replicate|Lec) to start generation…$/, p => `So‘rov qabul qilindi. ${p} yaratishni boshlashi kutilmoqda…`],
    [/^(\d+(?:\.\d+)?) seconds of source · 480p draft · estimated \$(\d+\.\d+) at \$(\d+(?:\.\d+)?)\/output second\. Final billing follows generated duration\. Motion and pitched vocals come from the prepared video; your portrait supplies identity\.( Seedance output audio is OFF\. The export restores the complete original soundtrack\.)?$/, (duration, cost, rate, audio) => `${duration} soniyali asl video · 480p sinov · taxminan $${cost}, har bir yaratilgan soniya $${rate}. Yakuniy to‘lov yaratilgan davomiylikka bog‘liq. Harakat va balandlatilgan ovoz tayyorlangan videodan, qiyofa esa portretingizdan olinadi.${audio ? ' Seedance natija audiosi O‘CHIRILGAN. Eksportda to‘liq asl ovoz yo‘lagi tiklanadi.' : ''}`],
    [/^(\d+(?:\.\d+)?) seconds · (\d+p) · ([\w:]+) · ¥(\d+\.\d+) generation \+ \$(\d+\.\d+) private uploads\. Any fractional extra generated tail is trimmed; source music and timing stay intact\.$/, (duration, q, ratio, cost, upload) => `${duration} soniya · ${q} · ${ratio} · yaratish ¥${cost} + yopiq yuklashlar $${upload}. Qo‘shimcha yaratilgan kasr soniyalar kesiladi; asl musiqa va vaqt saqlanadi.`],
    [/^(.+) via (OXEN|REPLICATE|LEC) selected\. No generation was submitted\.$/, (model, p) => `${model} (${p}) tanlandi. Video yaratish boshlanmadi.`],
    [/^This adapter starts at (\d+p)\. (.+)$/, (q, tail) => `Bu adapter ${q} dan boshlaydi. ${tail === 'Lec has no separate HD step.' ? 'Lec’da alohida HD bosqichi yo‘q.' : 'Avval sinovni yaratib, tekshiring. Natijalar bo‘limida yuqoriroq aniqlikdagi alohida pulli video yaratish mavjud.'}`],
    [/^Preparation and preview use (Oxen|Replicate|Lec|Legacy provider) credits\. Review the prompt before submitting\.$/, p => `Tayyorlash va sinov ${p} kreditlarini sarflaydi. Yuborishdan oldin ko‘rsatmani tekshiring.`],
    [/^Preparing your exact (Oxen|Lec) request\. No provider uploads or charges\.$/, p => `Aniq ${p} so‘rovi tayyorlanmoqda. Provayderga fayl yuklanmaydi yoki pul sarflanmaydi.`],
    [/^Request ready\. Add your (Oxen|Lec) key above to enable generation\.$/, p => `So‘rov tayyor. Yaratish uchun yuqorida ${p} kalitingizni kiriting.`],
    [/^Uploading references and submitting to (Oxen|Replicate|Lec)…$/, p => `Namunalar yuklanmoqda va ${p}’ga yuborilmoqda…`],
    [/^Submitting your reviewed (\d+p) request to (Oxen|Replicate|Lec)…$/, (q, p) => `Tekshirilgan ${q} so‘rovingiz ${p}’ga yuborilmoqda…`]
  ];
  function translate(source, locale = language) {
    if (locale !== 'uz') return source;
    const match = source.match(/^(\s*)(.*?)(\s*)$/s);
    const key = match[2];
    if (Object.hasOwn(uz, key)) return match[1] + uz[key] + match[3];
    for (const [pattern, render] of templates) {
      const parts = key.match(pattern);
      if (parts) return match[1] + render(...parts.slice(1)) + match[3];
    }
    return source;
  }

  // Keep each text node's English source so switching back never uses reverse translation.
  // Observe only UI copy. Requests, inputs, filenames and raw error/prompt blocks are excluded.
  const texts = new WeakMap(), attributes = new WeakMap();
  const excluded = 'script,style,textarea,pre,code,[data-no-i18n],#generation-id,#provider-label,#selected-model,#model-options strong,#saved-reference-grid';
  function updateText(node) {
    if (node.parentElement?.closest(excluded)) return;
    const previous = texts.get(node);
    const source = previous && node.data === previous.rendered ? previous.source : node.data;
    // A filename is opaque data. Only these explicit empty-upload hints are UI messages.
    if (node.parentElement?.closest('[data-filename]') && !['Video duration: 4 to 30 seconds', 'Photo or identity reference', 'Optional · a different person', "Restore your source's original audio", 'Saved reference · click to replace'].includes(source.trim())) return;
    const rendered = translate(source);
    if (rendered !== node.data) node.data = rendered;
    texts.set(node, { source, rendered });
  }
  function updateAttributes(element) {
    if (element.closest('[data-no-i18n],#saved-reference-grid')) return;
    let originals = attributes.get(element);
    if (!originals) { originals = {}; attributes.set(element, originals); }
    for (const name of ['aria-label', 'placeholder', 'alt']) {
      if (!element.hasAttribute(name)) continue;
      const current = element.getAttribute(name), previous = originals[name];
      const source = previous && current === previous.rendered ? previous.source : current;
      const rendered = translate(source);
      if (rendered !== current) element.setAttribute(name, rendered);
      originals[name] = { source, rendered };
    }
  }
  let observer;
  function scan(root) {
    if (root.nodeType === Node.TEXT_NODE) { updateText(root); return; }
    if (root.nodeType !== Node.ELEMENT_NODE) return;
    updateAttributes(root);
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT);
    for (let node = walker.nextNode(); node; node = walker.nextNode()) {
      if (node.nodeType === Node.TEXT_NODE) updateText(node); else updateAttributes(node);
    }
  }
  const observe = () => observer.observe(document.body, { subtree: true, childList: true, characterData: true, attributes: true, attributeFilter: ['aria-label', 'placeholder', 'alt'] });
  function apply() {
    observer?.disconnect();
    document.documentElement.lang = language;
    // Title is deliberately outside the observed body.
    const title = document.querySelector('title');
    if (title) updateText(title.firstChild);
    scan(document.body);
    for (const select of document.querySelectorAll('[data-language-select]')) select.value = language;
    if (observer) observe();
  }
  function setLanguage(value) {
    language = supported(value);
    try { localStorage.setItem(storageKey, language); } catch (_) { /* Session choice still works. */ }
    apply();
  }
  window.I18n = Object.freeze({ translate, setLanguage, get language() { return language; } });
  document.documentElement.lang = language;
  window.addEventListener('DOMContentLoaded', () => {
    observer = new MutationObserver(records => {
      observer.disconnect();
      for (const record of records) {
        if (record.type === 'childList') record.addedNodes.forEach(scan);
        else if (record.type === 'characterData') updateText(record.target);
        else updateAttributes(record.target);
      }
      observe();
    });
    for (const select of document.querySelectorAll('[data-language-select]')) select.addEventListener('change', () => setLanguage(select.value));
    apply();
  }, { once: true });
  window.addEventListener('storage', event => { if (event.key === storageKey || event.key === null) { language = supported(event.newValue); if (document.body) apply(); } });
})();
