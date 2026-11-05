@ In-game Mad Libs menus. Written by the Emerald Editor (editor/madlibs_live.py).

MadLibs_EventScript_Start::
	msgbox MadLibs_Text_Intro, MSGBOX_DEFAULT
	call MadLibs_EventScript_AskHow
	call MadLibs_EventScript_PickThing
	call MadLibs_EventScript_PickPlace
	call MadLibs_EventScript_PickAdj
	call MadLibs_EventScript_PickShout
	call MadLibs_EventScript_PickFood
	call MadLibs_EventScript_PickDrink
	call MadLibs_EventScript_PickPerson
	call MadLibs_EventScript_PickBodypart
	call MadLibs_EventScript_PickActivity
	call MadLibs_EventScript_PickFeeling
	call MadLibs_EventScript_PickVehicle
	call MadLibs_EventScript_PickClothing
	call MadLibs_EventScript_PickCreature
	call MadLibs_EventScript_PickName
	call MadLibs_EventScript_PickSound
	call MadLibs_EventScript_PickColor
	goto MadLibs_EventScript_Finish

MadLibs_EventScript_Badge1::
	msgbox MadLibs_Text_Badge1, MSGBOX_DEFAULT
	call MadLibs_EventScript_AskHow
	call MadLibs_EventScript_PickThing
	call MadLibs_EventScript_PickPlace
	call MadLibs_EventScript_PickFood
	call MadLibs_EventScript_PickName
	goto MadLibs_EventScript_Finish

MadLibs_EventScript_Badge2::
	msgbox MadLibs_Text_Badge2, MSGBOX_DEFAULT
	call MadLibs_EventScript_AskHow
	call MadLibs_EventScript_PickAdj
	call MadLibs_EventScript_PickShout
	call MadLibs_EventScript_PickPerson
	call MadLibs_EventScript_PickSound
	goto MadLibs_EventScript_Finish

MadLibs_EventScript_Badge3::
	msgbox MadLibs_Text_Badge3, MSGBOX_DEFAULT
	call MadLibs_EventScript_AskHow
	call MadLibs_EventScript_PickDrink
	call MadLibs_EventScript_PickBodypart
	call MadLibs_EventScript_PickActivity
	call MadLibs_EventScript_PickFeeling
	goto MadLibs_EventScript_Finish

MadLibs_EventScript_Badge4::
	msgbox MadLibs_Text_Badge4, MSGBOX_DEFAULT
	call MadLibs_EventScript_AskHow
	call MadLibs_EventScript_PickVehicle
	call MadLibs_EventScript_PickClothing
	call MadLibs_EventScript_PickCreature
	call MadLibs_EventScript_PickColor
	goto MadLibs_EventScript_Finish

MadLibs_EventScript_Badge5::
	msgbox MadLibs_Text_Badge5, MSGBOX_DEFAULT
	call MadLibs_EventScript_AskHow
	call MadLibs_EventScript_PickThing
	call MadLibs_EventScript_PickPlace
	call MadLibs_EventScript_PickFood
	call MadLibs_EventScript_PickName
	goto MadLibs_EventScript_Finish

MadLibs_EventScript_Badge6::
	msgbox MadLibs_Text_Badge6, MSGBOX_DEFAULT
	call MadLibs_EventScript_AskHow
	call MadLibs_EventScript_PickAdj
	call MadLibs_EventScript_PickShout
	call MadLibs_EventScript_PickPerson
	call MadLibs_EventScript_PickSound
	goto MadLibs_EventScript_Finish

MadLibs_EventScript_Badge7::
	msgbox MadLibs_Text_Badge7, MSGBOX_DEFAULT
	call MadLibs_EventScript_AskHow
	call MadLibs_EventScript_PickDrink
	call MadLibs_EventScript_PickBodypart
	call MadLibs_EventScript_PickActivity
	call MadLibs_EventScript_PickFeeling
	goto MadLibs_EventScript_Finish

MadLibs_EventScript_Badge8::
	msgbox MadLibs_Text_Badge8, MSGBOX_DEFAULT
	call MadLibs_EventScript_AskHow
	call MadLibs_EventScript_PickVehicle
	call MadLibs_EventScript_PickClothing
	call MadLibs_EventScript_PickCreature
	call MadLibs_EventScript_PickColor
	goto MadLibs_EventScript_Finish

@ VAR_0x8005: YES = the player picks, NO = surprise
MadLibs_EventScript_AskHow::
	msgbox MadLibs_Text_PickOrSurprise, MSGBOX_YESNO
	copyvar VAR_0x8005, VAR_RESULT
	return

MadLibs_EventScript_Finish::
	goto_if_eq VAR_0x8005, NO, MadLibs_EventScript_FinishSurprise
	msgbox MadLibs_Text_Done, MSGBOX_DEFAULT
	return

MadLibs_EventScript_FinishSurprise::
	msgbox MadLibs_Text_Surprised, MSGBOX_DEFAULT
	return

MadLibs_EventScript_Random::
	setvar VAR_RESULT, 255
	special MadLibs_AddWord
	return

MadLibs_EventScript_PickThing::
	setvar VAR_0x8004, 0
	goto_if_eq VAR_0x8005, NO, MadLibs_EventScript_Random
	message MadLibs_Text_PickThing
	waitmessage
	dynmultichoice 0, 0, TRUE, 6, 0, DYN_MULTICHOICE_CB_NONE, MadLibs_Text_Thing0, MadLibs_Text_Thing1, MadLibs_Text_Thing2, MadLibs_Text_Thing3, MadLibs_Text_Thing4, MadLibs_Text_Thing5, MadLibs_Text_Thing6, MadLibs_Text_Thing7, MadLibs_Text_Thing8, MadLibs_Text_Thing9, MadLibs_Text_Thing10, MadLibs_Text_Thing11, MadLibs_Text_Thing12, MadLibs_Text_Thing13, MadLibs_Text_Thing14, MadLibs_Text_Thing15, MadLibs_Text_Thing16, MadLibs_Text_Thing17, MadLibs_Text_Thing18, MadLibs_Text_Thing19, MadLibs_Text_Surprise
	closemessage
	special MadLibs_AddWord
	return

MadLibs_EventScript_PickPlace::
	setvar VAR_0x8004, 1
	goto_if_eq VAR_0x8005, NO, MadLibs_EventScript_Random
	message MadLibs_Text_PickPlace
	waitmessage
	dynmultichoice 0, 0, TRUE, 6, 0, DYN_MULTICHOICE_CB_NONE, MadLibs_Text_Place0, MadLibs_Text_Place1, MadLibs_Text_Place2, MadLibs_Text_Place3, MadLibs_Text_Place4, MadLibs_Text_Place5, MadLibs_Text_Place6, MadLibs_Text_Place7, MadLibs_Text_Place8, MadLibs_Text_Place9, MadLibs_Text_Place10, MadLibs_Text_Place11, MadLibs_Text_Place12, MadLibs_Text_Place13, MadLibs_Text_Place14, MadLibs_Text_Place15, MadLibs_Text_Place16, MadLibs_Text_Place17, MadLibs_Text_Place18, MadLibs_Text_Place19, MadLibs_Text_Surprise
	closemessage
	special MadLibs_AddWord
	return

MadLibs_EventScript_PickAdj::
	setvar VAR_0x8004, 2
	goto_if_eq VAR_0x8005, NO, MadLibs_EventScript_Random
	message MadLibs_Text_PickAdj
	waitmessage
	dynmultichoice 0, 0, TRUE, 6, 0, DYN_MULTICHOICE_CB_NONE, MadLibs_Text_Adj0, MadLibs_Text_Adj1, MadLibs_Text_Adj2, MadLibs_Text_Adj3, MadLibs_Text_Adj4, MadLibs_Text_Adj5, MadLibs_Text_Adj6, MadLibs_Text_Adj7, MadLibs_Text_Adj8, MadLibs_Text_Adj9, MadLibs_Text_Adj10, MadLibs_Text_Adj11, MadLibs_Text_Adj12, MadLibs_Text_Adj13, MadLibs_Text_Adj14, MadLibs_Text_Adj15, MadLibs_Text_Adj16, MadLibs_Text_Adj17, MadLibs_Text_Adj18, MadLibs_Text_Adj19, MadLibs_Text_Surprise
	closemessage
	special MadLibs_AddWord
	return

MadLibs_EventScript_PickShout::
	setvar VAR_0x8004, 3
	goto_if_eq VAR_0x8005, NO, MadLibs_EventScript_Random
	message MadLibs_Text_PickShout
	waitmessage
	dynmultichoice 0, 0, TRUE, 6, 0, DYN_MULTICHOICE_CB_NONE, MadLibs_Text_Shout0, MadLibs_Text_Shout1, MadLibs_Text_Shout2, MadLibs_Text_Shout3, MadLibs_Text_Shout4, MadLibs_Text_Shout5, MadLibs_Text_Shout6, MadLibs_Text_Shout7, MadLibs_Text_Shout8, MadLibs_Text_Shout9, MadLibs_Text_Shout10, MadLibs_Text_Shout11, MadLibs_Text_Shout12, MadLibs_Text_Shout13, MadLibs_Text_Shout14, MadLibs_Text_Shout15, MadLibs_Text_Shout16, MadLibs_Text_Shout17, MadLibs_Text_Shout18, MadLibs_Text_Shout19, MadLibs_Text_Surprise
	closemessage
	special MadLibs_AddWord
	return

MadLibs_EventScript_PickFood::
	setvar VAR_0x8004, 4
	goto_if_eq VAR_0x8005, NO, MadLibs_EventScript_Random
	message MadLibs_Text_PickFood
	waitmessage
	dynmultichoice 0, 0, TRUE, 6, 0, DYN_MULTICHOICE_CB_NONE, MadLibs_Text_Food0, MadLibs_Text_Food1, MadLibs_Text_Food2, MadLibs_Text_Food3, MadLibs_Text_Food4, MadLibs_Text_Food5, MadLibs_Text_Food6, MadLibs_Text_Food7, MadLibs_Text_Food8, MadLibs_Text_Food9, MadLibs_Text_Food10, MadLibs_Text_Food11, MadLibs_Text_Food12, MadLibs_Text_Food13, MadLibs_Text_Food14, MadLibs_Text_Food15, MadLibs_Text_Food16, MadLibs_Text_Food17, MadLibs_Text_Food18, MadLibs_Text_Food19, MadLibs_Text_Surprise
	closemessage
	special MadLibs_AddWord
	return

MadLibs_EventScript_PickDrink::
	setvar VAR_0x8004, 5
	goto_if_eq VAR_0x8005, NO, MadLibs_EventScript_Random
	message MadLibs_Text_PickDrink
	waitmessage
	dynmultichoice 0, 0, TRUE, 6, 0, DYN_MULTICHOICE_CB_NONE, MadLibs_Text_Drink0, MadLibs_Text_Drink1, MadLibs_Text_Drink2, MadLibs_Text_Drink3, MadLibs_Text_Drink4, MadLibs_Text_Drink5, MadLibs_Text_Drink6, MadLibs_Text_Drink7, MadLibs_Text_Drink8, MadLibs_Text_Drink9, MadLibs_Text_Drink10, MadLibs_Text_Drink11, MadLibs_Text_Drink12, MadLibs_Text_Drink13, MadLibs_Text_Drink14, MadLibs_Text_Drink15, MadLibs_Text_Drink16, MadLibs_Text_Drink17, MadLibs_Text_Drink18, MadLibs_Text_Drink19, MadLibs_Text_Surprise
	closemessage
	special MadLibs_AddWord
	return

MadLibs_EventScript_PickPerson::
	setvar VAR_0x8004, 6
	goto_if_eq VAR_0x8005, NO, MadLibs_EventScript_Random
	message MadLibs_Text_PickPerson
	waitmessage
	dynmultichoice 0, 0, TRUE, 6, 0, DYN_MULTICHOICE_CB_NONE, MadLibs_Text_Person0, MadLibs_Text_Person1, MadLibs_Text_Person2, MadLibs_Text_Person3, MadLibs_Text_Person4, MadLibs_Text_Person5, MadLibs_Text_Person6, MadLibs_Text_Person7, MadLibs_Text_Person8, MadLibs_Text_Person9, MadLibs_Text_Person10, MadLibs_Text_Person11, MadLibs_Text_Person12, MadLibs_Text_Person13, MadLibs_Text_Person14, MadLibs_Text_Person15, MadLibs_Text_Person16, MadLibs_Text_Person17, MadLibs_Text_Person18, MadLibs_Text_Person19, MadLibs_Text_Surprise
	closemessage
	special MadLibs_AddWord
	return

MadLibs_EventScript_PickBodypart::
	setvar VAR_0x8004, 7
	goto_if_eq VAR_0x8005, NO, MadLibs_EventScript_Random
	message MadLibs_Text_PickBodypart
	waitmessage
	dynmultichoice 0, 0, TRUE, 6, 0, DYN_MULTICHOICE_CB_NONE, MadLibs_Text_Bodypart0, MadLibs_Text_Bodypart1, MadLibs_Text_Bodypart2, MadLibs_Text_Bodypart3, MadLibs_Text_Bodypart4, MadLibs_Text_Bodypart5, MadLibs_Text_Bodypart6, MadLibs_Text_Bodypart7, MadLibs_Text_Bodypart8, MadLibs_Text_Bodypart9, MadLibs_Text_Bodypart10, MadLibs_Text_Bodypart11, MadLibs_Text_Bodypart12, MadLibs_Text_Bodypart13, MadLibs_Text_Bodypart14, MadLibs_Text_Bodypart15, MadLibs_Text_Bodypart16, MadLibs_Text_Bodypart17, MadLibs_Text_Bodypart18, MadLibs_Text_Bodypart19, MadLibs_Text_Surprise
	closemessage
	special MadLibs_AddWord
	return

MadLibs_EventScript_PickActivity::
	setvar VAR_0x8004, 8
	goto_if_eq VAR_0x8005, NO, MadLibs_EventScript_Random
	message MadLibs_Text_PickActivity
	waitmessage
	dynmultichoice 0, 0, TRUE, 6, 0, DYN_MULTICHOICE_CB_NONE, MadLibs_Text_Activity0, MadLibs_Text_Activity1, MadLibs_Text_Activity2, MadLibs_Text_Activity3, MadLibs_Text_Activity4, MadLibs_Text_Activity5, MadLibs_Text_Activity6, MadLibs_Text_Activity7, MadLibs_Text_Activity8, MadLibs_Text_Activity9, MadLibs_Text_Activity10, MadLibs_Text_Activity11, MadLibs_Text_Activity12, MadLibs_Text_Activity13, MadLibs_Text_Activity14, MadLibs_Text_Activity15, MadLibs_Text_Activity16, MadLibs_Text_Activity17, MadLibs_Text_Activity18, MadLibs_Text_Activity19, MadLibs_Text_Surprise
	closemessage
	special MadLibs_AddWord
	return

MadLibs_EventScript_PickFeeling::
	setvar VAR_0x8004, 9
	goto_if_eq VAR_0x8005, NO, MadLibs_EventScript_Random
	message MadLibs_Text_PickFeeling
	waitmessage
	dynmultichoice 0, 0, TRUE, 6, 0, DYN_MULTICHOICE_CB_NONE, MadLibs_Text_Feeling0, MadLibs_Text_Feeling1, MadLibs_Text_Feeling2, MadLibs_Text_Feeling3, MadLibs_Text_Feeling4, MadLibs_Text_Feeling5, MadLibs_Text_Feeling6, MadLibs_Text_Feeling7, MadLibs_Text_Feeling8, MadLibs_Text_Feeling9, MadLibs_Text_Feeling10, MadLibs_Text_Feeling11, MadLibs_Text_Feeling12, MadLibs_Text_Feeling13, MadLibs_Text_Feeling14, MadLibs_Text_Feeling15, MadLibs_Text_Feeling16, MadLibs_Text_Feeling17, MadLibs_Text_Feeling18, MadLibs_Text_Feeling19, MadLibs_Text_Surprise
	closemessage
	special MadLibs_AddWord
	return

MadLibs_EventScript_PickVehicle::
	setvar VAR_0x8004, 10
	goto_if_eq VAR_0x8005, NO, MadLibs_EventScript_Random
	message MadLibs_Text_PickVehicle
	waitmessage
	dynmultichoice 0, 0, TRUE, 6, 0, DYN_MULTICHOICE_CB_NONE, MadLibs_Text_Vehicle0, MadLibs_Text_Vehicle1, MadLibs_Text_Vehicle2, MadLibs_Text_Vehicle3, MadLibs_Text_Vehicle4, MadLibs_Text_Vehicle5, MadLibs_Text_Vehicle6, MadLibs_Text_Vehicle7, MadLibs_Text_Vehicle8, MadLibs_Text_Vehicle9, MadLibs_Text_Vehicle10, MadLibs_Text_Vehicle11, MadLibs_Text_Vehicle12, MadLibs_Text_Vehicle13, MadLibs_Text_Vehicle14, MadLibs_Text_Vehicle15, MadLibs_Text_Vehicle16, MadLibs_Text_Vehicle17, MadLibs_Text_Vehicle18, MadLibs_Text_Vehicle19, MadLibs_Text_Surprise
	closemessage
	special MadLibs_AddWord
	return

MadLibs_EventScript_PickClothing::
	setvar VAR_0x8004, 11
	goto_if_eq VAR_0x8005, NO, MadLibs_EventScript_Random
	message MadLibs_Text_PickClothing
	waitmessage
	dynmultichoice 0, 0, TRUE, 6, 0, DYN_MULTICHOICE_CB_NONE, MadLibs_Text_Clothing0, MadLibs_Text_Clothing1, MadLibs_Text_Clothing2, MadLibs_Text_Clothing3, MadLibs_Text_Clothing4, MadLibs_Text_Clothing5, MadLibs_Text_Clothing6, MadLibs_Text_Clothing7, MadLibs_Text_Clothing8, MadLibs_Text_Clothing9, MadLibs_Text_Clothing10, MadLibs_Text_Clothing11, MadLibs_Text_Clothing12, MadLibs_Text_Clothing13, MadLibs_Text_Clothing14, MadLibs_Text_Clothing15, MadLibs_Text_Clothing16, MadLibs_Text_Clothing17, MadLibs_Text_Clothing18, MadLibs_Text_Clothing19, MadLibs_Text_Surprise
	closemessage
	special MadLibs_AddWord
	return

MadLibs_EventScript_PickCreature::
	setvar VAR_0x8004, 12
	goto_if_eq VAR_0x8005, NO, MadLibs_EventScript_Random
	message MadLibs_Text_PickCreature
	waitmessage
	dynmultichoice 0, 0, TRUE, 6, 0, DYN_MULTICHOICE_CB_NONE, MadLibs_Text_Creature0, MadLibs_Text_Creature1, MadLibs_Text_Creature2, MadLibs_Text_Creature3, MadLibs_Text_Creature4, MadLibs_Text_Creature5, MadLibs_Text_Creature6, MadLibs_Text_Creature7, MadLibs_Text_Creature8, MadLibs_Text_Creature9, MadLibs_Text_Creature10, MadLibs_Text_Creature11, MadLibs_Text_Creature12, MadLibs_Text_Creature13, MadLibs_Text_Creature14, MadLibs_Text_Creature15, MadLibs_Text_Creature16, MadLibs_Text_Creature17, MadLibs_Text_Creature18, MadLibs_Text_Creature19, MadLibs_Text_Surprise
	closemessage
	special MadLibs_AddWord
	return

MadLibs_EventScript_PickName::
	setvar VAR_0x8004, 13
	goto_if_eq VAR_0x8005, NO, MadLibs_EventScript_Random
	message MadLibs_Text_PickName
	waitmessage
	dynmultichoice 0, 0, TRUE, 6, 0, DYN_MULTICHOICE_CB_NONE, MadLibs_Text_Name0, MadLibs_Text_Name1, MadLibs_Text_Name2, MadLibs_Text_Name3, MadLibs_Text_Name4, MadLibs_Text_Name5, MadLibs_Text_Name6, MadLibs_Text_Name7, MadLibs_Text_Name8, MadLibs_Text_Name9, MadLibs_Text_Name10, MadLibs_Text_Name11, MadLibs_Text_Name12, MadLibs_Text_Name13, MadLibs_Text_Name14, MadLibs_Text_Name15, MadLibs_Text_Name16, MadLibs_Text_Name17, MadLibs_Text_Name18, MadLibs_Text_Name19, MadLibs_Text_Surprise
	closemessage
	special MadLibs_AddWord
	return

MadLibs_EventScript_PickSound::
	setvar VAR_0x8004, 14
	goto_if_eq VAR_0x8005, NO, MadLibs_EventScript_Random
	message MadLibs_Text_PickSound
	waitmessage
	dynmultichoice 0, 0, TRUE, 6, 0, DYN_MULTICHOICE_CB_NONE, MadLibs_Text_Sound0, MadLibs_Text_Sound1, MadLibs_Text_Sound2, MadLibs_Text_Sound3, MadLibs_Text_Sound4, MadLibs_Text_Sound5, MadLibs_Text_Sound6, MadLibs_Text_Sound7, MadLibs_Text_Sound8, MadLibs_Text_Sound9, MadLibs_Text_Sound10, MadLibs_Text_Sound11, MadLibs_Text_Sound12, MadLibs_Text_Sound13, MadLibs_Text_Sound14, MadLibs_Text_Sound15, MadLibs_Text_Sound16, MadLibs_Text_Sound17, MadLibs_Text_Sound18, MadLibs_Text_Sound19, MadLibs_Text_Surprise
	closemessage
	special MadLibs_AddWord
	return

MadLibs_EventScript_PickColor::
	setvar VAR_0x8004, 15
	goto_if_eq VAR_0x8005, NO, MadLibs_EventScript_Random
	message MadLibs_Text_PickColor
	waitmessage
	dynmultichoice 0, 0, TRUE, 6, 0, DYN_MULTICHOICE_CB_NONE, MadLibs_Text_Color0, MadLibs_Text_Color1, MadLibs_Text_Color2, MadLibs_Text_Color3, MadLibs_Text_Color4, MadLibs_Text_Color5, MadLibs_Text_Color6, MadLibs_Text_Color7, MadLibs_Text_Color8, MadLibs_Text_Color9, MadLibs_Text_Color10, MadLibs_Text_Color11, MadLibs_Text_Color12, MadLibs_Text_Color13, MadLibs_Text_Color14, MadLibs_Text_Color15, MadLibs_Text_Color16, MadLibs_Text_Color17, MadLibs_Text_Color18, MadLibs_Text_Color19, MadLibs_Text_Surprise
	closemessage
	special MadLibs_AddWord
	return

MadLibs_Text_PickThing:
	.string "Pick a THING!$"

MadLibs_Text_Thing0:
	.string "rizz$"

MadLibs_Text_Thing1:
	.string "side quest$"

MadLibs_Text_Thing2:
	.string "burrito$"

MadLibs_Text_Thing3:
	.string "mixtape$"

MadLibs_Text_Thing4:
	.string "group chat$"

MadLibs_Text_Thing5:
	.string "podcast$"

MadLibs_Text_Thing6:
	.string "fanny pack$"

MadLibs_Text_Thing7:
	.string "hot tub$"

MadLibs_Text_Thing8:
	.string "beanbag chair$"

MadLibs_Text_Thing9:
	.string "fidget spinner$"

MadLibs_Text_Thing10:
	.string "NFT$"

MadLibs_Text_Thing11:
	.string "gold star$"

MadLibs_Text_Thing12:
	.string "ring light$"

MadLibs_Text_Thing13:
	.string "air fryer$"

MadLibs_Text_Thing14:
	.string "lava lamp$"

MadLibs_Text_Thing15:
	.string "vision board$"

MadLibs_Text_Thing16:
	.string "stress ball$"

MadLibs_Text_Thing17:
	.string "karaoke mic$"

MadLibs_Text_Thing18:
	.string "rubber duck$"

MadLibs_Text_Thing19:
	.string "crypto wallet$"

MadLibs_Text_PickPlace:
	.string "Pick a PLACE!$"

MadLibs_Text_Place0:
	.string "food court$"

MadLibs_Text_Place1:
	.string "basement$"

MadLibs_Text_Place2:
	.string "swamp$"

MadLibs_Text_Place3:
	.string "laundromat$"

MadLibs_Text_Place4:
	.string "bouncy castle$"

MadLibs_Text_Place5:
	.string "skate park$"

MadLibs_Text_Place6:
	.string "gas station$"

MadLibs_Text_Place7:
	.string "parking lot$"

MadLibs_Text_Place8:
	.string "Discord server$"

MadLibs_Text_Place9:
	.string "escape room$"

MadLibs_Text_Place10:
	.string "ball pit$"

MadLibs_Text_Place11:
	.string "airport$"

MadLibs_Text_Place12:
	.string "DMV$"

MadLibs_Text_Place13:
	.string "water park$"

MadLibs_Text_Place14:
	.string "mall$"

MadLibs_Text_Place15:
	.string "backrooms$"

MadLibs_Text_Place16:
	.string "dentist office$"

MadLibs_Text_Place17:
	.string "thrift store$"

MadLibs_Text_Place18:
	.string "arcade$"

MadLibs_Text_Place19:
	.string "drive-thru$"

MadLibs_Text_PickAdj:
	.string "Pick a DESCRIBING WORD!$"

MadLibs_Text_Adj0:
	.string "unhinged$"

MadLibs_Text_Adj1:
	.string "feral$"

MadLibs_Text_Adj2:
	.string "soggy$"

MadLibs_Text_Adj3:
	.string "bussin$"

MadLibs_Text_Adj4:
	.string "mid$"

MadLibs_Text_Adj5:
	.string "sus$"

MadLibs_Text_Adj6:
	.string "cursed$"

MadLibs_Text_Adj7:
	.string "delulu$"

MadLibs_Text_Adj8:
	.string "goated$"

MadLibs_Text_Adj9:
	.string "crusty$"

MadLibs_Text_Adj10:
	.string "moist$"

MadLibs_Text_Adj11:
	.string "chaotic$"

MadLibs_Text_Adj12:
	.string "iconic$"

MadLibs_Text_Adj13:
	.string "cringe$"

MadLibs_Text_Adj14:
	.string "extra$"

MadLibs_Text_Adj15:
	.string "based$"

MadLibs_Text_Adj16:
	.string "salty$"

MadLibs_Text_Adj17:
	.string "sketchy$"

MadLibs_Text_Adj18:
	.string "crunchy$"

MadLibs_Text_Adj19:
	.string "spicy$"

MadLibs_Text_PickShout:
	.string "Pick something to SHOUT!$"

MadLibs_Text_Shout0:
	.string "Sheesh$"

MadLibs_Text_Shout1:
	.string "Bruh$"

MadLibs_Text_Shout2:
	.string "Yeehaw$"

MadLibs_Text_Shout3:
	.string "Holy moly$"

MadLibs_Text_Shout4:
	.string "Good grief$"

MadLibs_Text_Shout5:
	.string "Bazinga$"

MadLibs_Text_Shout6:
	.string "Oh my Arceus$"

MadLibs_Text_Shout7:
	.string "Big yikes$"

MadLibs_Text_Shout8:
	.string "Slay$"

MadLibs_Text_Shout9:
	.string "Let him cook$"

MadLibs_Text_Shout10:
	.string "No way$"

MadLibs_Text_Shout11:
	.string "Ayo$"

MadLibs_Text_Shout12:
	.string "Skibidi$"

MadLibs_Text_Shout13:
	.string "Cowabunga$"

MadLibs_Text_Shout14:
	.string "Bonjour$"

MadLibs_Text_Shout15:
	.string "Hot dog$"

MadLibs_Text_Shout16:
	.string "Jeepers$"

MadLibs_Text_Shout17:
	.string "Gadzooks$"

MadLibs_Text_Shout18:
	.string "Mamma mia$"

MadLibs_Text_Shout19:
	.string "Oh snap$"

MadLibs_Text_PickFood:
	.string "Pick a FOOD!$"

MadLibs_Text_Food0:
	.string "chicken nugget$"

MadLibs_Text_Food1:
	.string "avocado toast$"

MadLibs_Text_Food2:
	.string "chili dog$"

MadLibs_Text_Food3:
	.string "ramen$"

MadLibs_Text_Food4:
	.string "corn dog$"

MadLibs_Text_Food5:
	.string "boba$"

MadLibs_Text_Food6:
	.string "taco$"

MadLibs_Text_Food7:
	.string "pickle$"

MadLibs_Text_Food8:
	.string "mystery meat$"

MadLibs_Text_Food9:
	.string "pizza roll$"

MadLibs_Text_Food10:
	.string "cereal$"

MadLibs_Text_Food11:
	.string "spaghetti$"

MadLibs_Text_Food12:
	.string "burrito bowl$"

MadLibs_Text_Food13:
	.string "cheese puff$"

MadLibs_Text_Food14:
	.string "mac and cheese$"

MadLibs_Text_Food15:
	.string "burnt toast$"

MadLibs_Text_Food16:
	.string "hot sauce$"

MadLibs_Text_Food17:
	.string "sourdough$"

MadLibs_Text_Food18:
	.string "noodle cup$"

MadLibs_Text_Food19:
	.string "meatball$"

MadLibs_Text_PickDrink:
	.string "Pick a DRINK!$"

MadLibs_Text_Drink0:
	.string "energy drink$"

MadLibs_Text_Drink1:
	.string "oat milk latte$"

MadLibs_Text_Drink2:
	.string "pickle juice$"

MadLibs_Text_Drink3:
	.string "warm soda$"

MadLibs_Text_Drink4:
	.string "protein shake$"

MadLibs_Text_Drink5:
	.string "iced coffee$"

MadLibs_Text_Drink6:
	.string "swamp water$"

MadLibs_Text_Drink7:
	.string "kombucha$"

MadLibs_Text_Drink8:
	.string "tap water$"

MadLibs_Text_Drink9:
	.string "bubble tea$"

MadLibs_Text_Drink10:
	.string "chocolate milk$"

MadLibs_Text_Drink11:
	.string "lemonade$"

MadLibs_Text_Drink12:
	.string "slushie$"

MadLibs_Text_Drink13:
	.string "hot cocoa$"

MadLibs_Text_Drink14:
	.string "smoothie$"

MadLibs_Text_Drink15:
	.string "gravy$"

MadLibs_Text_Drink16:
	.string "root beer$"

MadLibs_Text_Drink17:
	.string "seltzer$"

MadLibs_Text_Drink18:
	.string "orange juice$"

MadLibs_Text_Drink19:
	.string "sweet tea$"

MadLibs_Text_PickPerson:
	.string "Pick a KIND OF PERSON!$"

MadLibs_Text_Person0:
	.string "influencer$"

MadLibs_Text_Person1:
	.string "life coach$"

MadLibs_Text_Person2:
	.string "podcaster$"

MadLibs_Text_Person3:
	.string "mall cop$"

MadLibs_Text_Person4:
	.string "crypto bro$"

MadLibs_Text_Person5:
	.string "streamer$"

MadLibs_Text_Person6:
	.string "theater kid$"

MadLibs_Text_Person7:
	.string "HOA president$"

MadLibs_Text_Person8:
	.string "landlord$"

MadLibs_Text_Person9:
	.string "gym bro$"

MadLibs_Text_Person10:
	.string "substitute$"

MadLibs_Text_Person11:
	.string "lifeguard$"

MadLibs_Text_Person12:
	.string "middle manager$"

MadLibs_Text_Person13:
	.string "vlogger$"

MadLibs_Text_Person14:
	.string "DJ$"

MadLibs_Text_Person15:
	.string "magician$"

MadLibs_Text_Person16:
	.string "barista$"

MadLibs_Text_Person17:
	.string "cowboy$"

MadLibs_Text_Person18:
	.string "mime$"

MadLibs_Text_Person19:
	.string "tour guide$"

MadLibs_Text_PickBodypart:
	.string "Pick a BODY PART!$"

MadLibs_Text_Bodypart0:
	.string "left elbow$"

MadLibs_Text_Bodypart1:
	.string "pinky toe$"

MadLibs_Text_Bodypart2:
	.string "eyebrow$"

MadLibs_Text_Bodypart3:
	.string "kneecap$"

MadLibs_Text_Bodypart4:
	.string "belly button$"

MadLibs_Text_Bodypart5:
	.string "armpit$"

MadLibs_Text_Bodypart6:
	.string "forehead$"

MadLibs_Text_Bodypart7:
	.string "earlobe$"

MadLibs_Text_Bodypart8:
	.string "spine$"

MadLibs_Text_Bodypart9:
	.string "nostril$"

MadLibs_Text_Bodypart10:
	.string "funny bone$"

MadLibs_Text_Bodypart11:
	.string "chin$"

MadLibs_Text_Bodypart12:
	.string "ankle$"

MadLibs_Text_Bodypart13:
	.string "big toe$"

MadLibs_Text_Bodypart14:
	.string "shoulder blade$"

MadLibs_Text_Bodypart15:
	.string "knuckle$"

MadLibs_Text_Bodypart16:
	.string "uvula$"

MadLibs_Text_Bodypart17:
	.string "eyelid$"

MadLibs_Text_Bodypart18:
	.string "tongue$"

MadLibs_Text_Bodypart19:
	.string "back molar$"

MadLibs_Text_PickActivity:
	.string "Pick an ACTIVITY (-ing)!$"

MadLibs_Text_Activity0:
	.string "yodeling$"

MadLibs_Text_Activity1:
	.string "doomscrolling$"

MadLibs_Text_Activity2:
	.string "mewing$"

MadLibs_Text_Activity3:
	.string "napping$"

MadLibs_Text_Activity4:
	.string "gatekeeping$"

MadLibs_Text_Activity5:
	.string "yapping$"

MadLibs_Text_Activity6:
	.string "speedrunning$"

MadLibs_Text_Activity7:
	.string "moonwalking$"

MadLibs_Text_Activity8:
	.string "manifesting$"

MadLibs_Text_Activity9:
	.string "vibing$"

MadLibs_Text_Activity10:
	.string "jazzercising$"

MadLibs_Text_Activity11:
	.string "tap dancing$"

MadLibs_Text_Activity12:
	.string "beatboxing$"

MadLibs_Text_Activity13:
	.string "ghosting$"

MadLibs_Text_Activity14:
	.string "glazing$"

MadLibs_Text_Activity15:
	.string "crying$"

MadLibs_Text_Activity16:
	.string "flossing$"

MadLibs_Text_Activity17:
	.string "rage quitting$"

MadLibs_Text_Activity18:
	.string "cosplaying$"

MadLibs_Text_Activity19:
	.string "meal prepping$"

MadLibs_Text_PickFeeling:
	.string "Pick a FEELING!$"

MadLibs_Text_Feeling0:
	.string "unwell$"

MadLibs_Text_Feeling1:
	.string "so seen$"

MadLibs_Text_Feeling2:
	.string "hangry$"

MadLibs_Text_Feeling3:
	.string "shook$"

MadLibs_Text_Feeling4:
	.string "big mad$"

MadLibs_Text_Feeling5:
	.string "lowkey sad$"

MadLibs_Text_Feeling6:
	.string "at peace$"

MadLibs_Text_Feeling7:
	.string "cooked$"

MadLibs_Text_Feeling8:
	.string "blessed$"

MadLibs_Text_Feeling9:
	.string "unbothered$"

MadLibs_Text_Feeling10:
	.string "spooked$"

MadLibs_Text_Feeling11:
	.string "emotional$"

MadLibs_Text_Feeling12:
	.string "giddy$"

MadLibs_Text_Feeling13:
	.string "betrayed$"

MadLibs_Text_Feeling14:
	.string "sleepy$"

MadLibs_Text_Feeling15:
	.string "chill$"

MadLibs_Text_Feeling16:
	.string "pressed$"

MadLibs_Text_Feeling17:
	.string "crushed$"

MadLibs_Text_Feeling18:
	.string "smug$"

MadLibs_Text_Feeling19:
	.string "confused$"

MadLibs_Text_PickVehicle:
	.string "Pick a VEHICLE!$"

MadLibs_Text_Vehicle0:
	.string "shopping cart$"

MadLibs_Text_Vehicle1:
	.string "scooter$"

MadLibs_Text_Vehicle2:
	.string "unicycle$"

MadLibs_Text_Vehicle3:
	.string "monster truck$"

MadLibs_Text_Vehicle4:
	.string "party bus$"

MadLibs_Text_Vehicle5:
	.string "hoverboard$"

MadLibs_Text_Vehicle6:
	.string "golf cart$"

MadLibs_Text_Vehicle7:
	.string "tractor$"

MadLibs_Text_Vehicle8:
	.string "canoe$"

MadLibs_Text_Vehicle9:
	.string "school bus$"

MadLibs_Text_Vehicle10:
	.string "pogo stick$"

MadLibs_Text_Vehicle11:
	.string "jet ski$"

MadLibs_Text_Vehicle12:
	.string "blimp$"

MadLibs_Text_Vehicle13:
	.string "tricycle$"

MadLibs_Text_Vehicle14:
	.string "go-kart$"

MadLibs_Text_Vehicle15:
	.string "food truck$"

MadLibs_Text_Vehicle16:
	.string "wheelbarrow$"

MadLibs_Text_Vehicle17:
	.string "roller skate$"

MadLibs_Text_Vehicle18:
	.string "limo$"

MadLibs_Text_Vehicle19:
	.string "rowboat$"

MadLibs_Text_PickClothing:
	.string "Pick something to WEAR!$"

MadLibs_Text_Clothing0:
	.string "foam clog$"

MadLibs_Text_Clothing1:
	.string "fedora$"

MadLibs_Text_Clothing2:
	.string "cowboy hat$"

MadLibs_Text_Clothing3:
	.string "onesie$"

MadLibs_Text_Clothing4:
	.string "tutu$"

MadLibs_Text_Clothing5:
	.string "beanie$"

MadLibs_Text_Clothing6:
	.string "hoodie$"

MadLibs_Text_Clothing7:
	.string "cape$"

MadLibs_Text_Clothing8:
	.string "toga$"

MadLibs_Text_Clothing9:
	.string "bucket hat$"

MadLibs_Text_Clothing10:
	.string "crop top$"

MadLibs_Text_Clothing11:
	.string "tracksuit$"

MadLibs_Text_Clothing12:
	.string "tiara$"

MadLibs_Text_Clothing13:
	.string "bow tie$"

MadLibs_Text_Clothing14:
	.string "sombrero$"

MadLibs_Text_Clothing15:
	.string "trench coat$"

MadLibs_Text_Clothing16:
	.string "ugly sweater$"

MadLibs_Text_Clothing17:
	.string "lucky sock$"

MadLibs_Text_Clothing18:
	.string "bathrobe$"

MadLibs_Text_Clothing19:
	.string "tuxedo$"

MadLibs_Text_PickCreature:
	.string "Pick an ANIMAL!$"

MadLibs_Text_Creature0:
	.string "raccoon$"

MadLibs_Text_Creature1:
	.string "goose$"

MadLibs_Text_Creature2:
	.string "possum$"

MadLibs_Text_Creature3:
	.string "capybara$"

MadLibs_Text_Creature4:
	.string "axolotl$"

MadLibs_Text_Creature5:
	.string "frog$"

MadLibs_Text_Creature6:
	.string "llama$"

MadLibs_Text_Creature7:
	.string "hamster$"

MadLibs_Text_Creature8:
	.string "pigeon$"

MadLibs_Text_Creature9:
	.string "seagull$"

MadLibs_Text_Creature10:
	.string "squirrel$"

MadLibs_Text_Creature11:
	.string "goat$"

MadLibs_Text_Creature12:
	.string "sloth$"

MadLibs_Text_Creature13:
	.string "corgi$"

MadLibs_Text_Creature14:
	.string "ferret$"

MadLibs_Text_Creature15:
	.string "crab$"

MadLibs_Text_Creature16:
	.string "alpaca$"

MadLibs_Text_Creature17:
	.string "moth$"

MadLibs_Text_Creature18:
	.string "duck$"

MadLibs_Text_Creature19:
	.string "hedgehog$"

MadLibs_Text_PickName:
	.string "Pick a NAME!$"

MadLibs_Text_Name0:
	.string "Kevin$"

MadLibs_Text_Name1:
	.string "Big Steve$"

MadLibs_Text_Name2:
	.string "Grandma Linda$"

MadLibs_Text_Name3:
	.string "Brenda$"

MadLibs_Text_Name4:
	.string "Chad$"

MadLibs_Text_Name5:
	.string "Lil Nugget$"

MadLibs_Text_Name6:
	.string "Doug$"

MadLibs_Text_Name7:
	.string "Gary$"

MadLibs_Text_Name8:
	.string "Sir Reginald$"

MadLibs_Text_Name9:
	.string "Uncle Rick$"

MadLibs_Text_Name10:
	.string "DJ Toast$"

MadLibs_Text_Name11:
	.string "Barbara$"

MadLibs_Text_Name12:
	.string "Todd$"

MadLibs_Text_Name13:
	.string "Coach Dave$"

MadLibs_Text_Name14:
	.string "Becky$"

MadLibs_Text_Name15:
	.string "Mr. Pickles$"

MadLibs_Text_Name16:
	.string "Tiffany$"

MadLibs_Text_Name17:
	.string "Gerald$"

MadLibs_Text_Name18:
	.string "Aunt Deb$"

MadLibs_Text_Name19:
	.string "Captain Bob$"

MadLibs_Text_PickSound:
	.string "Pick a SOUND!$"

MadLibs_Text_Sound0:
	.string "bonk$"

MadLibs_Text_Sound1:
	.string "vine boom$"

MadLibs_Text_Sound2:
	.string "honk$"

MadLibs_Text_Sound3:
	.string "oof$"

MadLibs_Text_Sound4:
	.string "yeet$"

MadLibs_Text_Sound5:
	.string "boing$"

MadLibs_Text_Sound6:
	.string "skrrt$"

MadLibs_Text_Sound7:
	.string "kaboom$"

MadLibs_Text_Sound8:
	.string "beep boop$"

MadLibs_Text_Sound9:
	.string "sad trombone$"

MadLibs_Text_Sound10:
	.string "womp womp$"

MadLibs_Text_Sound11:
	.string "ding$"

MadLibs_Text_Sound12:
	.string "splat$"

MadLibs_Text_Sound13:
	.string "bloop$"

MadLibs_Text_Sound14:
	.string "airhorn$"

MadLibs_Text_Sound15:
	.string "kazoo$"

MadLibs_Text_Sound16:
	.string "quack$"

MadLibs_Text_Sound17:
	.string "pew pew$"

MadLibs_Text_Sound18:
	.string "ka-ching$"

MadLibs_Text_Sound19:
	.string "dun dun dun$"

MadLibs_Text_PickColor:
	.string "Pick a COLOR!$"

MadLibs_Text_Color0:
	.string "beige$"

MadLibs_Text_Color1:
	.string "neon green$"

MadLibs_Text_Color2:
	.string "hot pink$"

MadLibs_Text_Color3:
	.string "salmon$"

MadLibs_Text_Color4:
	.string "mustard$"

MadLibs_Text_Color5:
	.string "teal$"

MadLibs_Text_Color6:
	.string "chartreuse$"

MadLibs_Text_Color7:
	.string "ketchup red$"

MadLibs_Text_Color8:
	.string "glitter$"

MadLibs_Text_Color9:
	.string "lime$"

MadLibs_Text_Color10:
	.string "lavender$"

MadLibs_Text_Color11:
	.string "sky blue$"

MadLibs_Text_Color12:
	.string "burnt orange$"

MadLibs_Text_Color13:
	.string "gold$"

MadLibs_Text_Color14:
	.string "camo$"

MadLibs_Text_Color15:
	.string "rainbow$"

MadLibs_Text_Color16:
	.string "periwinkle$"

MadLibs_Text_Color17:
	.string "maroon$"

MadLibs_Text_Color18:
	.string "mint$"

MadLibs_Text_Color19:
	.string "tie-dye$"

MadLibs_Text_Surprise:
	.string "Surprise me!$"

MadLibs_Text_Intro:
	.string "Before this adventure starts, the\n"
	.string "story has 16 blanks to fill in.\p"
	.string "Everyone in HOENN will use your words\n"
	.string "for the rest of the game.\p"
	.string "Every GYM BADGE adds 4 more.$"

MadLibs_Text_PickOrSurprise:
	.string "Pick the words yourself?\n"
	.string "(NO lets the game surprise you.)$"

MadLibs_Text_Done:
	.string "Your words are locked in.\n"
	.string "Go see what people do with them.$"

MadLibs_Text_Surprised:
	.string "Your words are picked. You don't get\n"
	.string "to know them. Good luck out there.$"

MadLibs_Text_Badge1:
	.string "New badge, new words!\n"
	.string "4 more blanks to fill in.$"

MadLibs_Text_Badge2:
	.string "New badge, new words!\n"
	.string "4 more blanks to fill in.$"

MadLibs_Text_Badge3:
	.string "New badge, new words!\n"
	.string "4 more blanks to fill in.$"

MadLibs_Text_Badge4:
	.string "New badge, new words!\n"
	.string "4 more blanks to fill in.$"

MadLibs_Text_Badge5:
	.string "New badge, new words!\n"
	.string "4 more blanks to fill in.$"

MadLibs_Text_Badge6:
	.string "New badge, new words!\n"
	.string "4 more blanks to fill in.$"

MadLibs_Text_Badge7:
	.string "New badge, new words!\n"
	.string "4 more blanks to fill in.$"

MadLibs_Text_Badge8:
	.string "New badge, new words!\n"
	.string "4 more blanks to fill in.$"
