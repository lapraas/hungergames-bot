# The basis of the game is the Event.
Events are created using YAML, which operates with key/value pairs like a dictionary. All Events have a unique name, a chance value, a set of character requirements, a text result, and an optional set of character results. Each event uses placeholder names (OKA shorthands) to reference a Character or Item which has been matched to them.
The game uses events per round. It takes a Character, who will be referred to as the Main Character, and tests them against the requirements for each loaded Event, collecting a list of Events which have the potential to trigger. When all Events have been checked, one is selected from the pool of all possible Events, and that one gets triggered and performs its results on the Main Character (and potentially other characters).

At its most basic, an event looks like this:
```yaml
hello world: # event name
  chance: common # chance
  req: # requirements
    main: #empty requirement here
  text: | # text requirement (| makes multiline strings possible in YAML)
    @main says "Hello world!" to a supposedly invisible camera. Thanks for the help, @main!
```

# Event name
An event's name must be unique. It can contain all characters except commas, and is used only for debugging purposes (such as triggering an event by hand). In YAML, it serves as the key which gives the rest of the event's data. Everything associated with the event will be entabbed below the event name.

# Chance
The first thing an Event needs is a Chance value. This is either a positive integer value or one of a few specific string values, listed below:
| string   | value |
|----------|-------|
| common   | 30    |
| uncommon | 20    |
| rare     | 14    |
| rarer    | 10    |
| mythic   | 5     |
| secret   | 3     |
| shiny    | 1     |

The higher an Event's Chance, the more likely it is to trigger if it's matched. More values may be added to this list.

# Requirements
An Event's Requirements are all based on attributes of a Character - what they have, where they are, who they're with, etc. Each key in the Requirements is the shorthand name for a matched character. These shorthand names must be alphanumeric (uncluding underscores) and they're used in text replacement and to apply Results.
The first key is always the Main Character. Further keys are for other Characters near the Main Character.
The value of each key is a comma-separated list of criteria that a Character must meet. The value can be empty, which means any Character near the Main Character will match.

## Criteria

### Alone
Alone criteria start with one of either `alone` or `allied`.

`alone` will only match Characters who are not in an alliance.

`allied` will only match Characters who are in an alliance.

### Relationship
Relationship criteria start with one of either `ally` or `enemy`, and include a target for the relationship, which is a shorthand for a previously-matched Character. These criteria can only be used after the Main Character has been matched.

`ally` will only match Characters who are allied with the target Character.

`enemy` will only match Characters who are not allied with the target Character.

### Tag
Tag criteria start with `tag`, and include the name of the tag to be matched.

They will only match Characters who have the given tag.

### Item
Item criteria start with one of either `item` or `itemeq`, and include a shorthand for a matched item, and a space-separated list of tags.

`item` will only match Characters who have an item that has all of the given tags. If one of the given tags is ANY, all items match.

`itemeq` will only match Characters who have an item whose name matches the first tag.

The shorthand is used in text replacement and Results to refer to the matched item.

### Create
Create criteria start with one of either `create` or `createeq`, and include a shorthand for the created item, and a space-separated list of tags. This "criteria" is more of a setup for Results, because Items cannot be created in Results, only given.

`create` will put a random item with all of the given tags into the shorthand.

`createeq` will put an item with a specific name into the shorthand.

The shorthand is used in text replacement and Results to refer to the created item.

### Location
Location criteria start with `in`, and include the name of a location.

They will only match Characters who are inside of a zone with the given name.

# Text
When an Event triggers, it always has a flavor blurb that explains what the Event does to the matched Characters / Items. This goes under the Text key of the Event. It replaces any word starting with `@` or `&` with the name of a Character or Item, respectively. For each example, `main` has matched to a female Character named "Orial" and `item` has matched to an Item with the name "steak".

`@main says "Hello, world!" to an invisible camera.` -> **"Orial says "Hello, world!" to an invisible camera."**

Often, a pronoun or article is needed to have the Text make sense, and adding a "tag" before the `@` or `&` will accomplish this.

Character pronoun replacements have the tags `they` (subjective), `them` (objective), `their` (posessive), `theirs` (possessive pronoun), or `themself` (reflexive).

`@main gets hungry and eats their@main &food.` -> **"Orial gets hungry and eats her steak."**

An Item article replacement simply uses `a`, and includes the Item's name in the replacement (unlike a pronoun replacement).

`@main gets slapped with a@item.` -> **"Orial gets slapped with a steak."**

Sometimes, a verb needs to be conjugated for plurality (as in the difference between "she stops" and "they stop", the first of which needs an "s"), and this can be done by using the verb as the tag thanks to Jaraco's Inflect module.

`All of a sudden, a&item appears in front of @main. They@main pick@main it up without asking any questions.` -> **"All of a sudden, a steak appears in front of Orial. She picks it up without asking any questions."**

# Results
An Event's Results are a per-character list of effects. Each Result key must be the shorthand name for a Character matched by the Requirements, and their order does not matter.

## Effects

### Tag
Tag effects start with `tag` and include a name of a tag.

The matched Character will be given a tag with that name.

### Untag
Untag effects start with `untag` and include a name of a tag.

The matched Character will have the tag with that name removed from them.

### Item
Item effects start with `give` and include the shorthand name of an Item matched/created in the Requirements.

The matched Character will have a copy of the Item put into their inventory.

### Consume
Consume effects start with `consume` and include the shorthand name of an Item matched/created in the Requirements.

The matched Character will have the Item removed from their inventory.

### Ally
Ally effects start with `ally` and include the shorthand name of another Character.

If both the matched Character and the other Character are alone, they will form an alliance with each other.

If the matched Character is already in an alliance, the other Character will leave their alliance if they're in one and join the matched Character's.

If the other Character is already in an alliance and the matched Character is alone, the matched Character will join the other Character's alliance.

### Leave
Leave effects start with `leave`.

The matched Character will leave the alliance they're currently in.

### Move
Move effects start with `move` and may include the name of a Zone.

If a Zone name is given, the matched Character will be moved into that Zone.

Otherwise, the matched Character will be moved to a random Zone connected to the one they are currently in.

In either case, if the matched Character has a "running" tag, that tag is removed.

# Examples
Examples of Events can be found in the #yaml-dump channel in the Discord. If this guide hasn't answered a question about Events or needs to be clearer, please let lapras#0594 know.
