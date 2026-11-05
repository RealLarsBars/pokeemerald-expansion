#include "global.h"
#include "test/test.h"
#include "event_data.h"
#include "mad_libs.h"
#include "string_util.h"
#include "constants/characters.h"
#include "constants/vars.h"

// Each blank keeps up to 3 picks, 5 bits each, stored as word number + 1.
#define PICK(word) ((word) + 1)

TEST("Mad Libs blanks show the words the player picked")
{
    u8 buffer[96];

    VarSet(VAR_MADLIB_THING, PICK(3));
    VarSet(VAR_MADLIB_PLACE, PICK(0));
    VarSet(VAR_MADLIB_ADJ, PICK(1));
    VarSet(VAR_MADLIB_SHOUT, PICK(8));
    VarSet(VAR_MADLIB_COLOR, PICK(0));
    StringExpandPlaceholders(buffer, COMPOUND_STRING("{MADLIB_SHOUT}! My {MADLIB_ADJ} {MADLIB_THING} is in the {MADLIB_PLACE}. {MADLIB_COLOR}"));
    EXPECT_EQ(StringCompare(buffer, COMPOUND_STRING("Slay! My feral mixtape is in the food court. beige")), 0);
}

TEST("Mad Libs blanks show the first word when nothing was picked")
{
    u8 buffer[32];

    VarSet(VAR_MADLIB_THING, 0);
    StringExpandPlaceholders(buffer, COMPOUND_STRING("{MADLIB_THING}"));
    EXPECT_EQ(StringCompare(buffer, COMPOUND_STRING("rizz")), 0);
}

TEST("Mad Libs keeps three words per blank and forgets the oldest")
{
    VarSet(VAR_MADLIB_FOOD, 0);
    gSpecialVar_0x8004 = 4; // FOOD
    gSpecialVar_Result = 2;
    MadLibs_AddWord();
    EXPECT_EQ(VarGet(VAR_MADLIB_FOOD), PICK(2));
    gSpecialVar_Result = 5;
    MadLibs_AddWord();
    gSpecialVar_Result = 7;
    MadLibs_AddWord();
    EXPECT_EQ(VarGet(VAR_MADLIB_FOOD), PICK(2) | (PICK(5) << 5) | (PICK(7) << 10));
    gSpecialVar_Result = 9;
    MadLibs_AddWord();
    EXPECT_EQ(VarGet(VAR_MADLIB_FOOD), PICK(5) | (PICK(7) << 5) | (PICK(9) << 10));
}

TEST("Mad Libs Surprise me picks a real word")
{
    u8 buffer[32];

    VarSet(VAR_MADLIB_NAME, 0);
    gSpecialVar_0x8004 = 13; // NAME
    gSpecialVar_Result = 255;
    MadLibs_AddWord();
    EXPECT_NE(VarGet(VAR_MADLIB_NAME), 0);
    EXPECT_LE(VarGet(VAR_MADLIB_NAME), 20);
    StringExpandPlaceholders(buffer, COMPOUND_STRING("{MADLIB_NAME}"));
    EXPECT_NE(buffer[0], EOS);
}
