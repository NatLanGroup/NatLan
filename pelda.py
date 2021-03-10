

# ez az osztály az ételekkel kapcsolatos adatokat és műveleteket tudja.
class etel:           
  
    def __init__(self):        # ez mindig lefut ha egy példányt létrehozunk az osztályból
                                # a "self" az adott pédányt jelenti amelyikkel meghivjuk
        self.etelek = ["paprikas csirke","porkolt","toltott kaposzta","palocleves","bableves"]    # legyen egy listánk ez ételekről
        self.neve = ""               # az adott étel neve
        self.ara = 0                 # az adott étel ára
      
# ez az osztály az éttermeket ragadja meg: 
     
class etterem:

    def __init__(self,nev=""):
        self.neve = nev          # ez lesz az étterem neve
        self.menu=[]            # ebben a listában lesz az étterem választéka
        self.napi_ajanlat={}    # ez egy dictionary - egy olyan lista aminek az indexe nemcsak egész szám lehet
        
    def menu_nyom (self):      # ez a függvény nyomtatja az étterem teljes menüjét
        print ("MENÜ:")
        for etel in self.menu:   # a menu lista értékeit veszi fel az etel változó
            print (etel.neve)
    
        
# ez a főprogram, itt indul a végrehajtás
print ("Program indul!")

# legyen két levesünk és egy főételünk
leves1 = etel()                  # !!!!!!!!!!!!!!!! ez a módja annak, hogy az étel osztály egy példányát létrehozzuk
leves1.neve=leves1.etelek[3]
leves2 = etel()
leves2.neve = leves1.etelek[4]
foetel1 = etel()
foetel1.neve = leves1.etelek[0]
print ("Ételek:",leves1.etelek, "első leves:",leves1.neve)

# legyen egy éttermünk
pipacsarda = etterem("Pipa csárda")
print ("az éttermünk neve:",pipacsarda.neve)

# leghyen az étteremnek menüje, vagyis étlapja
pipacsarda.menu.append(leves1)          # ez a fontos: a listában etel típusú objektumok vannak!!!!!
pipacsarda.menu.append(leves2)
pipacsarda.menu.append(foetel1)

# mi az etterem menujeben az első étel neve ????????? EZ:
elso_etel_neve = pipacsarda.menu[0].neve
print ("Az étterem étlapján az első étel:",elso_etel_neve)
print ("")

# nyomtassuk a teljes menut !
pipacsarda.menu_nyom()
print ("")

#  ÉRTSÜK MEG mind a 48-ös sor, mind a 23-as sor működését!!!!

# most legyen hetfore es keddre egy napi ajanlatunk ebben az etteremben:
pipacsarda.napi_ajanlat["hetfo"]=[]
pipacsarda.napi_ajanlat["hetfo"].append(leves1)
pipacsarda.napi_ajanlat["hetfo"].append(foetel1)
pipacsarda.napi_ajanlat["kedd"]=[]
pipacsarda.napi_ajanlat["kedd"].append(leves2)
pipacsarda.napi_ajanlat["kedd"].append(foetel1)

# nyomtassuk a keddi napi ajanlat elso ket elemet (nincs is neki tobb):
print ("Keddi napi ajanlat elso ket eleme:")
print(pipacsarda.napi_ajanlat["kedd"][0].neve)     # itt ertsunk meg mindent: mi a "kedd", mi utana a 0, mi a .neve
print(pipacsarda.napi_ajanlat["kedd"][1].neve)

