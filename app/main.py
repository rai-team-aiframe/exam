# app/main.py
import os
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

# Import modules
from app.database import init_db, init_db_updates, import_all_questions
from app.routers import home, auth, exam, admin, superuser
from app.admin_db import init_admin_db
from app.superuser_db import init_superuser_db

# Create the FastAPI app
app = FastAPI(title="آزمون آنلاین شخصیت و هوش")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Set up templates
templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(home.router)
app.include_router(auth.router)
app.include_router(exam.router)
app.include_router(admin.router)
app.include_router(superuser.router)

# Root redirect to home
@app.get("/", response_class=HTMLResponse)
async def root():
    return RedirectResponse(url="/home")

# Startup event
@app.on_event("startup")
async def startup_event():
    # Initialize database
    init_db()
    
    # Initialize database updates for new features
    init_db_updates()
    
    # Initialize admin database
    init_admin_db()
    
    # Initialize superuser database
    init_superuser_db()
    
    # Import all questions (both personality and puzzle)
    import_all_questions()
    
    # Import questions from the existing list (for backwards compatibility)
    questions_list = [
        "1- من اصولا شخص نگراني نيستم.",
        "2- دوست دارم هميشه افراد زيادي دور و برم باشند.",
        "3- دوست ندارم وقتم را با خيال پردازي تلف كنم.",
        "4- سعي ميكنم در مقابل همه مودب باشم.",
        "5- وسايل متعلق به خود را تميز و مرتب نگاه مي دارم.",
        "6- اغلب خود را كمتر از ديگران حس مي كنم.",
        "7- زود به خنده مي افتم.",
        "8- هنگامي كه راه درست، كاري را پيدا كنم،آن روش را هميشه در آن مورد تكرار مي كنم.",
        "9- اغلب با فاميل و همكارانم بگو مگو دارم.",
        "10-به خوبي مي توانم كارهايم را طوري تنظيم كنم كه درست سر زمان تعيين شده انجام شوند.",
        "11- هنگامي كه تحت فشارهاي روحي زيادي هستم، گاه احساس مي كنم دارم خرد مي شوم.",
        "12- خودم را فرد خيلي سر حال و سر زنده اي نمي دانم.",
        "13- نقش هاي موجود در پديده هاي هنري و طبيعت مرا مبهوت مي كند.",
        "14- بعضي مردم فكر مي كنند كه من نشخصي خود خواه و خود محورم.",
        "15- فرد خيلي مرتب و منظمي نيستم.",
        "16- به ندرت احساس تنهايي و غم مي كنم.",
        "17- واقعا از صحبت كردن با ديگران لذت مي برم.",
        "18- فكر مي كنم گوش دادن دانشجويان به مطالب متناقض فقط به سردرگمي و گمراهي آن ها منجر خواهد شد.",
        "19- همكاري را بر رقابت با ديگران ترجيح مي دهم.",
        "20- سعي مي كنم همه كارهايم را با احساس مسوليت انجام دهم.",
        "21- اغلب احساس عصبي بودن و تنش مي كنم.",
        "22- هميشه براي كار آماده ام.",
        "23- شعر تقريبا اثري بر من ندارد.",
        "24- نسبت به قصد و نيت ديگران حساس  مشكوك هستم.",
        "25- داراي هدف روشني هستم و براي رسيدن به آن طبق برنامه كار ميكنم.",
        "26- گاهي كاملا احساس بي ارزشي مي كنم.",
        "27- غالباً ترجيح مي دهم كار ها را به تنهايي انجام دهم.",
        "28- اغلب غذاهاي جديد و خارجي را امتحان مي كنم.",
        "29- معتقدم اگر به مردم اجازه  دهيد، اكثر آن ها از شما سوء استفاده مي كنند.",
        "30- قبل از شروع هر كاري وقت زيادي را تلف مي كنم.",
        "31- به ندرت احساس اضطراب يا ترس مي كنم.",
        "32- اغلب احساس مي كنم سرشار از انرژي هستم.",
        "33- به  ندرت به احساسات و عواطفي كه محيط هاي متفاوت به وجود  مي آورند توجه مي كنم .",
        "34- اغلب آشنايانم مرا دوست دارند.",
        "35- براي رسيدن به اهدافم شديداً تلاش مي كنم.",
        "36- اغلب از طرز برخورد ديگران با خودم عصباني مي شوم.",
        "37- فردي خوشحال و بشاش و داراي روحيه خوبي هستم.",
        "38- معتقدم كه هنگام تصميم گيري درباره مسائل اخلاقي بايد از مراجع مذهبي پيروي كنيم.",
        "39- برخي فكر مي كنند كه من فردي سرد و حسابگر هستم.",
        "40- وقتي قول يا تعهدي مي دهم، همواره مي توان براي عمل به آن روي من حساب كرد.",
        "41-  غالبا وقتي كارها پيش نمي روند، دلسرد شده و از كار صرف نظر مي كنم.",
        "42- شخص با نشاط و خوش بيني نيستم.",
        "43- بعضي اوقات وقتي شعري را مي خوانم يا يك كار هنري را تماشا مي كنم، يك احساس لرزش و يك تكان هيجاني را حس مي كنم.",
        "44- در روش هايم سرسخت و بي انعطاف هستم.",
        "45- گاهي آن طور كه بايد و شايد قابل اعتماد و اتكاء نيستم.",
        "46- به ندرت غمگين و افسرده مي شوم .",
        "47- زندگي و رويدادهاي آن برايم  سريع مي گذرند.",
        "48- علاقه اي به تامل و تفكر جدي درباره سرنوشت و ماهيت جهان يا انسان ندارم.",
        "49- عموماً سعي مي كنم شخصي با ملاحظه و منطقي باشم.",
        "50- فرد مولدي هستم كه هميشه كارهايم را به اتمام مي رسانم.",
        "51- اغلب احساس درماندگي مي كنم و دنبال كسي مي گردم كه مشكلاتم را برطرف كند.",
        "52- شخص بسيار فعالي هستم.",
        "53- من كنجكاوي فكري فراواني دارم.",
        "54- اگر كسي را دوست نداشته باشم،مي گذارم متوجه اين احساسم بشود.",
        "55- فكر نمي كنم كه هيچ وقت بتوانم فردي منطقي بشوم.",
        "56- گاهي آنچنان خجالت زده شده ام كه فقط مي خواستم خود را پنهان كنم.",
        "57- ترجيح مي دهم كه براي خودم كار كنم تا راهبر ديگران باشم.",
        "58- اغلب از كلنجار رفتن با نظريه ها يا مفاهيم انتزاعي لذت مي برم.",
        "59- اگر لازم باشد مي توانم براي رسيدن به اهدافم ديگران را به طور ماهرانه اي به كار بگيرم.",
        "60- تلاش مي كنم هر كاري را به نحو ماهرانه اي انجام دهم."
    ]
    
    # Import existing questions using the old function for backwards compatibility
    from app.questions import import_questions_from_list
    import_questions_from_list(questions_list)

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    # Cleanup resources if needed
    pass