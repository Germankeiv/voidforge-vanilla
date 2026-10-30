#!/usr/bin/env python3
"""Build vanilla Minecraft Java 1.20.4 Voidforge datapack and resource pack.
Uses Python standard library only. No Paper, Fabric, or Forge required.
"""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import json, struct, zlib, math

OUT = Path("dist")
OUT.mkdir(exist_ok=True)
ITEMS = [
    ("sword", "netherite_sword", 41001, "Voidbreaker Sword", "Void Strike"),
    ("pickaxe", "netherite_pickaxe", 41002, "Titan Pickaxe", "Titan Miner"),
    ("axe", "netherite_axe", 41003, "Timber Axe", "Timber Force"),
    ("shovel", "netherite_shovel", 41004, "Earthshaker Shovel", "Earthshaker"),
    ("hoe", "netherite_hoe", 41005, "Harvest Hoe", "Harvest Blessing"),
    ("helmet", "leather_helmet", 41101, "Voidguard Helmet", "Crystal Vision"),
    ("chestplate", "leather_chestplate", 41102, "Voidguard Chestplate", "Void Shield"),
    ("leggings", "leather_leggings", 41103, "Voidguard Leggings", "Phantom Step"),
    ("boots", "leather_boots", 41104, "Voidguard Boots", "Gravity Walker"),
]
def j(obj):
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"
def put(z, name, value):
    z.writestr(name, value)
def png_pixels(kind, size=16):
    # Pixel-art icons in the original black/cyan/purple Voidforge palette.
    transparent=(0,0,0,0)
    steel=(42,47,65,255)
    edge=(65,232,248,255)
    purple=(163,77,242,255)
    light=(205,242,255,255)
    dark=(20,24,35,255)
    pixels=[]
    for y in range(size):
        row=[]
        for x in range(size):
            p=transparent
            if kind in ("sword","pickaxe","axe","shovel","hoe"):
                if 3 <= x <= 11 and abs((x+y)-15)<=1:
                    p=steel
                if kind=="sword" and 2<=x<=11 and abs(x-y)<=1:
                    p=edge if x%3 else light
                if kind=="pickaxe" and 2<=y<=5 and 2<=x<=13:
                    p=edge if y==2 else steel
                if kind=="axe" and 2<=x<=8 and 2<=y<=8 and x+y<=14:
                    p=edge if x in (2,8) or y in (2,8) else steel
                if kind=="shovel" and 2<=x<=8 and 2<=y<=7 and abs(x-5)<=3:
                    p=edge if x in (2,8) or y==2 else steel
                if kind=="hoe" and 2<=y<=5 and 2<=x<=12 and x+y>=7:
                    p=edge if y==2 else steel
                if 6<=x<=9 and 7<=y<=10 and abs(x+y-16)<=2:
                    p=purple
            else:
                if kind=="helmet":
                    inside=3<=x<=12 and 3<=y<=12 and not (5<=x<=10 and 10<=y<=12)
                elif kind=="chestplate":
                    inside=(2<=x<=13 and 3<=y<=11 and (x<=5 or x>=10 or 5<=y<=12))
                elif kind=="leggings":
                    inside=(3<=x<=12 and 2<=y<=7) or (3<=x<=6 and 7<=y<=14) or (9<=x<=12 and 7<=y<=14)
                else:
                    inside=(3<=x<=6 and 4<=y<=12) or (9<=x<=12 and 4<=y<=12) or (2<=x<=7 and 11<=y<=14) or (8<=x<=13 and 11<=y<=14)
                if inside:
                    p=steel
                    if x in (3,12) or y in (3,12):
                        p=edge
                    if 7<=x<=9 and 6<=y<=9:
                        p=purple
            row.append(p)
        pixels.append(row)
    return pixels
def png_bytes(pixels):
    h=len(pixels); w=len(pixels[0])
    raw=b"".join(b"\x00"+b"".join(bytes(px) for px in row) for row in pixels)
    def chunk(tag,data):
        return struct.pack(">I",len(data))+tag+data+struct.pack(">I",zlib.crc32(tag+data)&0xffffffff)
    return b"\x89PNG\r\n\x1a\n"+chunk(b"IHDR",struct.pack(">IIBBBBB",w,h,8,6,0,0,0))+chunk(b"IDAT",zlib.compress(raw,9))+chunk(b"IEND",b"")
def mcgive(base, model, name, ability, key):
    # Java 1.20.4 legacy NBT item syntax (not 1.20.5+ components).
    display=json.dumps({"text":name,"color":"aqua","italic":False},separators=(",",":"))
    lore=json.dumps({"text":"Voidforge | "+ability,"color":"light_purple","italic":False},separators=(",",":"))
    ench='[{id:"minecraft:unbreaking",lvl:3s},{id:"minecraft:mending",lvl:1s}]'
    return ('give @s minecraft:'+base+'{CustomModelData:'+str(model)+
        ',Voidforge:"'+key+'",display:{Name:\''+display+'\',Lore:[\''+lore+'\']},Enchantments:'+ench+'} 1\n')
with ZipFile(OUT/"Voidforge-Datapack-1.20.4.zip","w",ZIP_DEFLATED) as z:
    put(z,"pack.mcmeta",j({"pack":{"pack_format":26,"description":"Voidforge equipment abilities for Java 1.20.4"}}))
    put(z,"data/minecraft/tags/functions/load.json",j({"values":["voidforge:load"]}))
    put(z,"data/minecraft/tags/functions/tick.json",j({"values":["voidforge:tick"]}))
    put(z,"data/voidforge/functions/load.mcfunction","tellraw @a {\"text\":\"Voidforge loaded! Use /function voidforge:give/all\",\"color\":\"aqua\"}\n")
    tick=[]
    # Held-item NBT matching; use short effects to turn powers off after unequipping.
    for key,base,model,name,ability in ITEMS:
        put(z,f"data/voidforge/functions/give/{key}.mcfunction",mcgive(base,model,name,ability,key))
    tick += [
        'execute as @a[nbt={SelectedItem:{tag:{Voidforge:"pickaxe"}}}] run effect give @s minecraft:haste 2 1 true',
        'execute as @a[nbt={SelectedItem:{tag:{Voidforge:"axe"}}}] run effect give @s minecraft:strength 2 0 true',
        'execute as @a[nbt={SelectedItem:{tag:{Voidforge:"shovel"}}}] run effect give @s minecraft:haste 2 0 true',
        'execute as @a[nbt={Inventory:[{Slot:103b,tag:{Voidforge:"helmet"}}]}] run effect give @s minecraft:night_vision 12 0 true',
        'execute as @a[nbt={Inventory:[{Slot:102b,tag:{Voidforge:"chestplate"}}]}] run effect give @s minecraft:resistance 2 0 true',
        'execute as @a[nbt={Inventory:[{Slot:101b,tag:{Voidforge:"leggings"}}]}] run effect give @s minecraft:speed 2 0 true',
        'execute as @a[nbt={Inventory:[{Slot:100b,tag:{Voidforge:"boots"}}]}] run effect give @s minecraft:slow_falling 2 0 true'
    ]
    put(z,"data/voidforge/functions/tick.mcfunction","\n".join(tick)+"\n")
    put(z,"data/voidforge/functions/give/all.mcfunction","\n".join("function voidforge:give/"+k for k,*_ in ITEMS)+"\n")
    put(z,"data/voidforge/functions/give/hopper.mcfunction",
        'give @s minecraft:hopper{display:{Name:\'{"text":"Super Hopper","color":"light_purple","italic":false}\'}} 1\n')
    put(z,"README.txt","Vanilla Java 1.20.4. Install in world/datapacks and run /reload then /function voidforge:give/all.\n"
        "Sword combat, crop bonuses and Super Hopper auto-collection are NOT implemented in this initial pack.\n"
        "Armor powers are potion effects; worn armor has vanilla leather geometry. Test on a backup world.\n")
with ZipFile(OUT/"Voidforge-ResourcePack-1.20.4.zip","w",ZIP_DEFLATED) as z:
    put(z,"pack.mcmeta",j({"pack":{"pack_format":22,"description":"Voidforge cyan-purple custom item icons for Java 1.20.4"}}))
    for key,base,model,name,ability in ITEMS:
        # Minecraft's original vanilla base model texture, plus a CMD override.
        texture="minecraft:item/"+base
        if base.startswith("leather_"):
            texture="minecraft:item/"+base
        put(z,"assets/minecraft/models/item/"+base+".json",j({
            "parent":"minecraft:item/generated","textures":{"layer0":texture},
            "overrides":[{"predicate":{"custom_model_data":model},"model":"minecraft:item/voidforge/"+key}]
        }))
        put(z,"assets/minecraft/models/item/voidforge/"+key+".json",j({
            "parent":"minecraft:item/generated",
            "textures":{"layer0":"minecraft:item/voidforge/"+key}
        }))
        put(z,"assets/minecraft/textures/item/voidforge/"+key+".png",png_bytes(png_pixels(key)))
    put(z,"README.txt","Vanilla Java 1.20.4 item icons. Enable this ZIP in Options > Resource Packs.\n"
        "These are simple original pixel-art icons, NOT the rendered concept art or a full custom worn-armor model.\n"
        "This pack does not replace the existing Super Hopper design or include its original texture.\n")
print("Built:")
for p in sorted(OUT.glob("*.zip")):
    print(" ",p, p.stat().st_size,"bytes")

