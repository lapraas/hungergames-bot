# Event syntax

Events are the basis of the entire game. All events are created using YAML, whose syntax is much simpler and more writable than JSON's. All events have a unique name, a set of requirements, and a set of results. Events have placeholder names (OKA local names) which reference game objects that get matched by the game.
```yaml
test event name: # event name is the YAML dictionary key and can have spaces
    in:
        # requirements go here
    out:
        # results go here
```

Each event should have a `chars` requirement, which will define what characters the event will include, and a `text` result, which will be what is displayed once the event is finished.

# Requirements
These are all of the criteria that must be satisfied for an event to be put into the game's event pool.

## chars
The `chars` requirement is a string whose elements are split by comma. Elements have a name denoted with a `$`, followed by a space, and then a series of space-separated qualifier clauses (though most will only need to use one clause). The game will match a qualified character to each element, stopping if it can't, and the character gets stored in the event with a given name for later use. The first element is always the main character of the event. The elements are read in order from left to right, so prior characters can be used in qualifiers.
```yaml
simple:
    in:
        # This is a chars requirement at its simplest.
        # "mainCharacter" can be replaced with whatever name you want, such as "main", "1", or "mc".
        # Note that the name starts with a $, this is how the event differentiates between a normal word and an actual character.
        chars: $mainCharacter
complicated:
    in:
        # Here we start to add qualifiers, of which there are currently four: "alone", "allied", "enemy", "ally".
        # The "enemy" and "ally" qualifiers tell the game whose enemy or ally the matched character should be. The target of these qualifiers
        #  defaults to the main character (and therefore can't be used with the first element), and can be changed by adding a name in
        #  parentheses.
        # The "alone" and "allied" qualifiers tell the game whether or not the matched character should be part of an alliance.
        #  These don't require targets, so they can be used with the first element (the main character).
        # If no qualifiers are given, any character can be matched.
        # For this example, a main character who isn't allied with anyone is matched (named $main),
        #  along with an enemy of the main character (named $victim),
        #  along with an enemy of the main character and an ally of the $victim character (named $victimFriend).
        chars: $main alone, $victim enemy, $victimFriend enemy ally($victim)
```

## items
The `items` requirement is a comma-separated list of items which are to be assigned to the event. Elements first have a name for the item starting with a `$`, followed by the name of the character who is meant to own the item, followed by a space-separated list of tags the item should have. If a specifically-named item is needed, a tag starting with a `!` can beused. Each matched item will be unique.
```yaml
items event:
    in:
        chars: $main
        # This requires the main character to have three items:
        #  an item tagged with "food" stored as "mainsFood",
        #  an item tagged with both "weapon" and "special" stored as "mainsWeapon",
        #  and an item with the name "scepter" stored as "mainsScepter".
        items: $mainsFood $main food, $mainsWeapon $main weapon special, $mainsScepter $main !scepter
```

## tags
The `tags` requirement is a comma-separated list of character tags

# Results
After all requirements have been met and everything has been assigned to the event, it has a chance to run. These are all of the things that happen when the event does run.

## text
The `text` result is a string which gets displayed by the game. Each name (denoted by $) in the string is replaced with the name of the corresponding character or item which was stored in the event when the requirements were met. These replacements are automatically capitalized. If a pronoun or article is to be used in place of the name, a single-character tag can be prepended to the name (before the `$`). For a character, these tags can be `s` for subjective, `o` for objective, and `p` for posessive. For an item, the tag can be `a` for article (which includes the item name, i.e. "a bandage").
```yaml
hello world:
    in:
        chars: $main
    out:
        text: $main says "Hello World!" to a supposedly invisible camera. Thanks for the help, $main!

heal:
    in:
        chars: $main
        item: $weapon($main weapon)
    out:
        # This example references a character as well as an item, and some of the names are tagged to use pronouns.
        text: $main decides o$main wants to practice with p$main $weapon.
```

## consume
The `consume` result is a comma-separated list of item names to be "consumed" by the event, or removed from their owners' inventories when the event triggers. The local name of the item is the only thing required for each element of the list. Consuming an item requires it to have been matched from a character using the `item` requirement.
```yaml
consume event:
    in:
        chars: $main
        item: $fooditem $main
    out:
        text: $main gets hungry and decides to eat p$main $fooditem.
        consume: $fooditem
