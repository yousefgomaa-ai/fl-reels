# FB Legends topics (`topics/en.json`)

The owner's rule (2026-11-14): «المواضيع تجيلي علي تليجرام بعد ماتتاكد صحتها و انا اختار الموضوع اللي يتعمل ريلز من تلجرام بعدها يتعمل و يتبعتلي الفيديو جاهز و انا انشره».

How it works:
1. A session checks each topic and adds it to `topics/en.json`, then pushes to `main`.
2. The site's server reads this file every tick (`fbEnTopicsAnnounce`) and sends each new topic once to the owner's Telegram. The message shows what the topic says, the facts that were checked and their sources.
3. The owner presses 🎬 to make the reel or ❌ to drop it. «مواضيع» / `/topics` in the bot lists the topics still open.
4. 🎬 queues the reel (`fbEnNewMake`). It is rendered like every English reel, and the finished video comes back to Telegram for the owner to publish.

## Before a topic goes in
- Check every number, name, date and quote against its source on the web on the day. Never write one from memory: transfers and records change.
- Read a player's caps and goals from Wikipedia's infobox (or the federation's page), and note the date you read it.
- Take a quote word for word from a named outlet, and put the date and place in `context` and the outlet in `source`. If the outlets disagree on the words, use the most widely printed version, or leave the quote out.
- Leave out anything disputed or still running. Example: a manager's current job, whose record table may not be up to date.
- Pick photos by eye from Commons contact sheets (fl-reels branch `claude/nla-probe`, `sample/photos.py`). Each one must show the face clearly and be the right person.
  - A club topic needs the player's current club shirt.
  - A national-team topic needs the national shirt, or a neutral photo.
  - Give each photo its credit as `Author (licence)`.
  - A cut-out from `anim/cut/` can be used as `photo: 'cut/<slug>.webp'`, with its credit from `anim/cut/CREDITS.md`.
- Follow the editorial rules: no women's football, nothing about Israel, and use Commons photos only.

## Shape of one topic
```json
{ "id": "mirror-esposito",            // a-z, 0-9 and dashes; never reused
  "added": "2026-11-14",
  "ar": "one or two lines in Arabic for the owner: what the reel says",
  "facts": ["each checked fact, in Arabic, with where it came from"],
  "sources": ["https://… the pages read"],
  "spec": { … } }
```
`spec` is what the reel page gets, with these extra fields:
- `kind`: one of `en-mirror`, `en-number`, `en-said` or `en-next`.
- `title`: the search phrase, which is also the caption's first line.
- `caption` and `tags`.
- `voice`: one spoken line per beat, with numbers written in words.
- `minBeats`.
- Photos, in one of two forms:
  - Commons photos as `file` + `credit` + `pos`. The server turns `file` into the Commons address.
  - Cut-outs as `photo`.
- Crests by club name in `crest`, filled from the site's team index.

See the four first topics in `en.json` for one complete example of each kind:
- `en-mirror`: needs `now`, `legend`, `stat` (`n`, `unit`, `nowGames`, `legGames`), three `clues`, `fact`, `endH` and `cta`. It has 8 beats: the hook, three clues, the countdown, the reveal, the race and the question.
- `en-number`: needs `num`, `unit`, `hook`, `who`, `head`, `line` (optional: `span`, `marks`, `label`), `match` (optional), `fact` and `cta`. It has 3 beats.
- `en-said`: needs `quote` (words in `*stars*` are lit in gold), three `options`, `answer` (0-2), `context` and `source`. It has 4 beats. The caption must not give the answer away.
- `en-next`: needs `who`, `head`, `record.rows` (`club`, `crest`, `years`, `p`, `w`, `d`, `l`) and `fixtures.rows` (`opp`, `crest`, `date`, `comp`, `ha`). It has 4 beats.
