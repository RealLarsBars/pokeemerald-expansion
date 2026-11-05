// In-game Mad Libs words. Written by the Emerald Editor (editor/madlibs_live.py).
// The player picks words in data/scripts/mad_libs.inc; src/mad_libs.c shows them.

#ifndef GUARD_DATA_MAD_LIBS_H
#define GUARD_DATA_MAD_LIBS_H

#define MADLIB_SLOT_COUNT 16
#define MADLIB_WORD_COUNT 20

static const u16 sMadLibVars[MADLIB_SLOT_COUNT] =
{
    VAR_MADLIB_THING,
    VAR_MADLIB_PLACE,
    VAR_MADLIB_ADJ,
    VAR_MADLIB_SHOUT,
    VAR_MADLIB_FOOD,
    VAR_MADLIB_DRINK,
    VAR_MADLIB_PERSON,
    VAR_MADLIB_BODYPART,
    VAR_MADLIB_ACTIVITY,
    VAR_MADLIB_FEELING,
    VAR_MADLIB_VEHICLE,
    VAR_MADLIB_CLOTHING,
    VAR_MADLIB_CREATURE,
    VAR_MADLIB_NAME,
    VAR_MADLIB_SOUND,
    VAR_MADLIB_COLOR,
};

static const u8 *const sMadLibWords[MADLIB_SLOT_COUNT][MADLIB_WORD_COUNT] =
{
    { // THING
        COMPOUND_STRING("rizz"), COMPOUND_STRING("side quest"), COMPOUND_STRING("burrito"), COMPOUND_STRING("mixtape"), COMPOUND_STRING("group chat"),
        COMPOUND_STRING("podcast"), COMPOUND_STRING("fanny pack"), COMPOUND_STRING("hot tub"), COMPOUND_STRING("beanbag chair"), COMPOUND_STRING("fidget spinner"),
        COMPOUND_STRING("NFT"), COMPOUND_STRING("gold star"), COMPOUND_STRING("ring light"), COMPOUND_STRING("air fryer"), COMPOUND_STRING("lava lamp"),
        COMPOUND_STRING("vision board"), COMPOUND_STRING("stress ball"), COMPOUND_STRING("karaoke mic"), COMPOUND_STRING("rubber duck"), COMPOUND_STRING("crypto wallet"),
    },
    { // PLACE
        COMPOUND_STRING("food court"), COMPOUND_STRING("basement"), COMPOUND_STRING("swamp"), COMPOUND_STRING("laundromat"), COMPOUND_STRING("bouncy castle"),
        COMPOUND_STRING("skate park"), COMPOUND_STRING("gas station"), COMPOUND_STRING("parking lot"), COMPOUND_STRING("Discord server"), COMPOUND_STRING("escape room"),
        COMPOUND_STRING("ball pit"), COMPOUND_STRING("airport"), COMPOUND_STRING("DMV"), COMPOUND_STRING("water park"), COMPOUND_STRING("mall"),
        COMPOUND_STRING("backrooms"), COMPOUND_STRING("dentist office"), COMPOUND_STRING("thrift store"), COMPOUND_STRING("arcade"), COMPOUND_STRING("drive-thru"),
    },
    { // ADJ
        COMPOUND_STRING("unhinged"), COMPOUND_STRING("feral"), COMPOUND_STRING("soggy"), COMPOUND_STRING("bussin"), COMPOUND_STRING("mid"),
        COMPOUND_STRING("sus"), COMPOUND_STRING("cursed"), COMPOUND_STRING("delulu"), COMPOUND_STRING("goated"), COMPOUND_STRING("crusty"),
        COMPOUND_STRING("moist"), COMPOUND_STRING("chaotic"), COMPOUND_STRING("iconic"), COMPOUND_STRING("cringe"), COMPOUND_STRING("extra"),
        COMPOUND_STRING("based"), COMPOUND_STRING("salty"), COMPOUND_STRING("sketchy"), COMPOUND_STRING("crunchy"), COMPOUND_STRING("spicy"),
    },
    { // SHOUT
        COMPOUND_STRING("Sheesh"), COMPOUND_STRING("Bruh"), COMPOUND_STRING("Yeehaw"), COMPOUND_STRING("Holy moly"), COMPOUND_STRING("Good grief"),
        COMPOUND_STRING("Bazinga"), COMPOUND_STRING("Oh my Arceus"), COMPOUND_STRING("Big yikes"), COMPOUND_STRING("Slay"), COMPOUND_STRING("Let him cook"),
        COMPOUND_STRING("No way"), COMPOUND_STRING("Ayo"), COMPOUND_STRING("Skibidi"), COMPOUND_STRING("Cowabunga"), COMPOUND_STRING("Bonjour"),
        COMPOUND_STRING("Hot dog"), COMPOUND_STRING("Jeepers"), COMPOUND_STRING("Gadzooks"), COMPOUND_STRING("Mamma mia"), COMPOUND_STRING("Oh snap"),
    },
    { // FOOD
        COMPOUND_STRING("chicken nugget"), COMPOUND_STRING("avocado toast"), COMPOUND_STRING("chili dog"), COMPOUND_STRING("ramen"), COMPOUND_STRING("corn dog"),
        COMPOUND_STRING("boba"), COMPOUND_STRING("taco"), COMPOUND_STRING("pickle"), COMPOUND_STRING("mystery meat"), COMPOUND_STRING("pizza roll"),
        COMPOUND_STRING("cereal"), COMPOUND_STRING("spaghetti"), COMPOUND_STRING("burrito bowl"), COMPOUND_STRING("cheese puff"), COMPOUND_STRING("mac and cheese"),
        COMPOUND_STRING("burnt toast"), COMPOUND_STRING("hot sauce"), COMPOUND_STRING("sourdough"), COMPOUND_STRING("noodle cup"), COMPOUND_STRING("meatball"),
    },
    { // DRINK
        COMPOUND_STRING("energy drink"), COMPOUND_STRING("oat milk latte"), COMPOUND_STRING("pickle juice"), COMPOUND_STRING("warm soda"), COMPOUND_STRING("protein shake"),
        COMPOUND_STRING("iced coffee"), COMPOUND_STRING("swamp water"), COMPOUND_STRING("kombucha"), COMPOUND_STRING("tap water"), COMPOUND_STRING("bubble tea"),
        COMPOUND_STRING("chocolate milk"), COMPOUND_STRING("lemonade"), COMPOUND_STRING("slushie"), COMPOUND_STRING("hot cocoa"), COMPOUND_STRING("smoothie"),
        COMPOUND_STRING("gravy"), COMPOUND_STRING("root beer"), COMPOUND_STRING("seltzer"), COMPOUND_STRING("orange juice"), COMPOUND_STRING("sweet tea"),
    },
    { // PERSON
        COMPOUND_STRING("influencer"), COMPOUND_STRING("life coach"), COMPOUND_STRING("podcaster"), COMPOUND_STRING("mall cop"), COMPOUND_STRING("crypto bro"),
        COMPOUND_STRING("streamer"), COMPOUND_STRING("theater kid"), COMPOUND_STRING("HOA president"), COMPOUND_STRING("landlord"), COMPOUND_STRING("gym bro"),
        COMPOUND_STRING("substitute"), COMPOUND_STRING("lifeguard"), COMPOUND_STRING("middle manager"), COMPOUND_STRING("vlogger"), COMPOUND_STRING("DJ"),
        COMPOUND_STRING("magician"), COMPOUND_STRING("barista"), COMPOUND_STRING("cowboy"), COMPOUND_STRING("mime"), COMPOUND_STRING("tour guide"),
    },
    { // BODYPART
        COMPOUND_STRING("left elbow"), COMPOUND_STRING("pinky toe"), COMPOUND_STRING("eyebrow"), COMPOUND_STRING("kneecap"), COMPOUND_STRING("belly button"),
        COMPOUND_STRING("armpit"), COMPOUND_STRING("forehead"), COMPOUND_STRING("earlobe"), COMPOUND_STRING("spine"), COMPOUND_STRING("nostril"),
        COMPOUND_STRING("funny bone"), COMPOUND_STRING("chin"), COMPOUND_STRING("ankle"), COMPOUND_STRING("big toe"), COMPOUND_STRING("shoulder blade"),
        COMPOUND_STRING("knuckle"), COMPOUND_STRING("uvula"), COMPOUND_STRING("eyelid"), COMPOUND_STRING("tongue"), COMPOUND_STRING("back molar"),
    },
    { // ACTIVITY
        COMPOUND_STRING("yodeling"), COMPOUND_STRING("doomscrolling"), COMPOUND_STRING("mewing"), COMPOUND_STRING("napping"), COMPOUND_STRING("gatekeeping"),
        COMPOUND_STRING("yapping"), COMPOUND_STRING("speedrunning"), COMPOUND_STRING("moonwalking"), COMPOUND_STRING("manifesting"), COMPOUND_STRING("vibing"),
        COMPOUND_STRING("jazzercising"), COMPOUND_STRING("tap dancing"), COMPOUND_STRING("beatboxing"), COMPOUND_STRING("ghosting"), COMPOUND_STRING("glazing"),
        COMPOUND_STRING("crying"), COMPOUND_STRING("flossing"), COMPOUND_STRING("rage quitting"), COMPOUND_STRING("cosplaying"), COMPOUND_STRING("meal prepping"),
    },
    { // FEELING
        COMPOUND_STRING("unwell"), COMPOUND_STRING("so seen"), COMPOUND_STRING("hangry"), COMPOUND_STRING("shook"), COMPOUND_STRING("big mad"),
        COMPOUND_STRING("lowkey sad"), COMPOUND_STRING("at peace"), COMPOUND_STRING("cooked"), COMPOUND_STRING("blessed"), COMPOUND_STRING("unbothered"),
        COMPOUND_STRING("spooked"), COMPOUND_STRING("emotional"), COMPOUND_STRING("giddy"), COMPOUND_STRING("betrayed"), COMPOUND_STRING("sleepy"),
        COMPOUND_STRING("chill"), COMPOUND_STRING("pressed"), COMPOUND_STRING("crushed"), COMPOUND_STRING("smug"), COMPOUND_STRING("confused"),
    },
    { // VEHICLE
        COMPOUND_STRING("shopping cart"), COMPOUND_STRING("scooter"), COMPOUND_STRING("unicycle"), COMPOUND_STRING("monster truck"), COMPOUND_STRING("party bus"),
        COMPOUND_STRING("hoverboard"), COMPOUND_STRING("golf cart"), COMPOUND_STRING("tractor"), COMPOUND_STRING("canoe"), COMPOUND_STRING("school bus"),
        COMPOUND_STRING("pogo stick"), COMPOUND_STRING("jet ski"), COMPOUND_STRING("blimp"), COMPOUND_STRING("tricycle"), COMPOUND_STRING("go-kart"),
        COMPOUND_STRING("food truck"), COMPOUND_STRING("wheelbarrow"), COMPOUND_STRING("roller skate"), COMPOUND_STRING("limo"), COMPOUND_STRING("rowboat"),
    },
    { // CLOTHING
        COMPOUND_STRING("foam clog"), COMPOUND_STRING("fedora"), COMPOUND_STRING("cowboy hat"), COMPOUND_STRING("onesie"), COMPOUND_STRING("tutu"),
        COMPOUND_STRING("beanie"), COMPOUND_STRING("hoodie"), COMPOUND_STRING("cape"), COMPOUND_STRING("toga"), COMPOUND_STRING("bucket hat"),
        COMPOUND_STRING("crop top"), COMPOUND_STRING("tracksuit"), COMPOUND_STRING("tiara"), COMPOUND_STRING("bow tie"), COMPOUND_STRING("sombrero"),
        COMPOUND_STRING("trench coat"), COMPOUND_STRING("ugly sweater"), COMPOUND_STRING("lucky sock"), COMPOUND_STRING("bathrobe"), COMPOUND_STRING("tuxedo"),
    },
    { // CREATURE
        COMPOUND_STRING("raccoon"), COMPOUND_STRING("goose"), COMPOUND_STRING("possum"), COMPOUND_STRING("capybara"), COMPOUND_STRING("axolotl"),
        COMPOUND_STRING("frog"), COMPOUND_STRING("llama"), COMPOUND_STRING("hamster"), COMPOUND_STRING("pigeon"), COMPOUND_STRING("seagull"),
        COMPOUND_STRING("squirrel"), COMPOUND_STRING("goat"), COMPOUND_STRING("sloth"), COMPOUND_STRING("corgi"), COMPOUND_STRING("ferret"),
        COMPOUND_STRING("crab"), COMPOUND_STRING("alpaca"), COMPOUND_STRING("moth"), COMPOUND_STRING("duck"), COMPOUND_STRING("hedgehog"),
    },
    { // NAME
        COMPOUND_STRING("Kevin"), COMPOUND_STRING("Big Steve"), COMPOUND_STRING("Grandma Linda"), COMPOUND_STRING("Brenda"), COMPOUND_STRING("Chad"),
        COMPOUND_STRING("Lil Nugget"), COMPOUND_STRING("Doug"), COMPOUND_STRING("Gary"), COMPOUND_STRING("Sir Reginald"), COMPOUND_STRING("Uncle Rick"),
        COMPOUND_STRING("DJ Toast"), COMPOUND_STRING("Barbara"), COMPOUND_STRING("Todd"), COMPOUND_STRING("Coach Dave"), COMPOUND_STRING("Becky"),
        COMPOUND_STRING("Mr. Pickles"), COMPOUND_STRING("Tiffany"), COMPOUND_STRING("Gerald"), COMPOUND_STRING("Aunt Deb"), COMPOUND_STRING("Captain Bob"),
    },
    { // SOUND
        COMPOUND_STRING("bonk"), COMPOUND_STRING("vine boom"), COMPOUND_STRING("honk"), COMPOUND_STRING("oof"), COMPOUND_STRING("yeet"),
        COMPOUND_STRING("boing"), COMPOUND_STRING("skrrt"), COMPOUND_STRING("kaboom"), COMPOUND_STRING("beep boop"), COMPOUND_STRING("sad trombone"),
        COMPOUND_STRING("womp womp"), COMPOUND_STRING("ding"), COMPOUND_STRING("splat"), COMPOUND_STRING("bloop"), COMPOUND_STRING("airhorn"),
        COMPOUND_STRING("kazoo"), COMPOUND_STRING("quack"), COMPOUND_STRING("pew pew"), COMPOUND_STRING("ka-ching"), COMPOUND_STRING("dun dun dun"),
    },
    { // COLOR
        COMPOUND_STRING("beige"), COMPOUND_STRING("neon green"), COMPOUND_STRING("hot pink"), COMPOUND_STRING("salmon"), COMPOUND_STRING("mustard"),
        COMPOUND_STRING("teal"), COMPOUND_STRING("chartreuse"), COMPOUND_STRING("ketchup red"), COMPOUND_STRING("glitter"), COMPOUND_STRING("lime"),
        COMPOUND_STRING("lavender"), COMPOUND_STRING("sky blue"), COMPOUND_STRING("burnt orange"), COMPOUND_STRING("gold"), COMPOUND_STRING("camo"),
        COMPOUND_STRING("rainbow"), COMPOUND_STRING("periwinkle"), COMPOUND_STRING("maroon"), COMPOUND_STRING("mint"), COMPOUND_STRING("tie-dye"),
    },
};

#endif // GUARD_DATA_MAD_LIBS_H
