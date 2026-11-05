// In-game Mad Libs.
//
// Dialogue can contain blanks like {MADLIB_FOOD}. The player fills them in from
// menus (data/scripts/mad_libs.inc): every blank at the start of the game, and
// four more words after each Gym. Each blank keeps up to MADLIB_PICKS words in
// one save variable (5 bits each, 0 = empty), and the text switches between them.
// The words themselves are in src/data/mad_libs.h, written by the Emerald Editor.
#include "global.h"
#include "event_data.h"
#include "mad_libs.h"
#include "random.h"
#include "constants/vars.h"
#include "data/mad_libs.h"

#define MADLIB_PICKS 3
#define MADLIB_BITS  5
#define MADLIB_MASK  ((1 << MADLIB_BITS) - 1)

STATIC_ASSERT(MADLIB_WORD_COUNT < MADLIB_MASK, MadLibWordsFitInFiveBits);

const u8 *GetMadLibWord(u32 slot)
{
    u16 value, picks[MADLIB_PICKS];
    u32 i, count = 0;

    if (slot >= MADLIB_SLOT_COUNT)
        return sMadLibWords[0][0];
    value = VarGet(sMadLibVars[slot]);
    for (i = 0; i < MADLIB_PICKS; i++)
    {
        u16 pick = (value >> (i * MADLIB_BITS)) & MADLIB_MASK;
        if (pick != 0 && pick <= MADLIB_WORD_COUNT)
            picks[count++] = pick - 1;
    }
    if (count == 0)
        return sMadLibWords[slot][0];
    // Switch words now and then without touching the game's random numbers.
    return sMadLibWords[slot][picks[(gSaveBlock2Ptr->playTimeMinutes + slot) % count]];
}

// Adds a word to a blank. VAR_0x8004: the blank. VAR_RESULT: the word, or a
// number past the end of the list for a random one. A blank that already has
// MADLIB_PICKS words forgets its oldest one.
void MadLibs_AddWord(void)
{
    u32 slot = gSpecialVar_0x8004;
    u32 choice = gSpecialVar_Result;
    u16 value;
    u32 i;

    if (slot >= MADLIB_SLOT_COUNT)
        return;
    if (choice >= MADLIB_WORD_COUNT)
        choice = Random() % MADLIB_WORD_COUNT;
    value = VarGet(sMadLibVars[slot]);
    for (i = 0; i < MADLIB_PICKS; i++)
    {
        if (((value >> (i * MADLIB_BITS)) & MADLIB_MASK) == 0)
            break;
    }
    if (i == MADLIB_PICKS)
    {
        value >>= MADLIB_BITS;
        i = MADLIB_PICKS - 1;
    }
    value |= (choice + 1) << (i * MADLIB_BITS);
    VarSet(sMadLibVars[slot], value);
}
