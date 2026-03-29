# -*- coding: utf-8 -*-
"""Emit quarks.txt-derived CANON_PROMPTS. Run: python silvercrow/_emit_quarks_canon.py"""

from __future__ import annotations


def S(s: str) -> dict:
    return {"text": s, "tier": "signature"}


def N(s: str) -> dict:
    return {"text": s, "tier": "nuclear"}


CANON_PROMPTS = {
    "Nice to meet you": {
        "positive": [
            "Nice to meet you too.",
            "Glad we met.",
            "What’s good broski?",
        ],
        "neutral": [
            "Nice to meet you.",
            "Hey.",
            "Indeed.",
        ],
        "negative": [
            "We’ll see about that.",
            "What do you want?",
            "I bet it is.",
        ],
        "severe": [
            "Don’t get too comfortable.",
            "We’ll see how long that lasts.",
            "Relax bro. You’re cringe.",
            N("Nice to meet you… slut."),
        ],
    },
    "Hey, how are you?": {
        "positive": [
            "I’m doing great, actually.",
            "Pretty good, thanks for asking.",
            "I’m doing really well today.",
        ],
        "neutral": [
            "I’m alright.",
            "Not bad.",
            "I’ve been better.",
        ],
        "negative": [
            "Not great, honestly.",
            "I don’t want to talk about it.",
            "Why do you care?",
        ],
        "severe": [
            "Terrible. And talking to you isn’t helping.",
            "Mind your business idiot.",
        ],
    },
    "What’s up?": {
        "positive": [
            "Not much, just chilling.",
            "Just enjoying the moment.",
            "Talking to you now haha.",
        ],
        "neutral": [
            "Nothing really.",
            "Same as always.",
            "Just here.",
        ],
        "negative": [
            "What do you want?",
            "Why?",
            "Nothing you need to worry about.",
        ],
        "severe": [
            "Not your bands. MY bands however are very up. So up that I spell them this way: bandzzz. Sucka.",
            "I can’t engage with someone with such a lack of swag.",
            "Find your way out please.",
        ],
    },
    "Do you mind if I sit here?": {
        "positive": [
            "Not at all, go ahead.",
            "Yeah, that’s fine.",
            "Of course, sit.",
            "I’d love some company!",
        ],
        "neutral": [
            "I guess.",
            "Sure.",
            "If you want.",
        ],
        "negative": [
            "I’d rather you didn’t.",
            "There are other spots.",
            "I’m good actually.",
        ],
        "severe": [
            "If by “here” you mean on my face, then yes.",
            "Yeah, I do mind. Very much so. Step.",
            "Don’t sit here bitch.",
        ],
    },
    "What’s your name?": {
        "positive": [
            "I’m {character_name}. Nice to meet you.",
            "{character_name}. What about you?",
            "It’s {character_name}.",
        ],
        "neutral": [
            "{character_name}.",
        ],
        "negative": [
            "Why do you need to know that?",
            "Your mom.",
            "I don’t trust you with my name.",
        ],
        "severe": [
            "You have no business in this areuh. Step.",
            "Don’t ask me that again.",
            "Mind your business.",
        ],
    },
    "I disagree with you.": {
        "positive": [
            "That’s fair.",
            "We don’t have to agree.",
            "I respect that.",
        ],
        "neutral": [
            "Okay.",
            "That’s your opinion.",
            "Alright.",
        ],
        "negative": [
            "Duh, you dumb as a bag of rocks.",
            "You’re wrong though.",
            "Shut up bitch.",
        ],
        "severe": [
            "Don’t care.",
            "Your opinion means nothing to me.",
            "Keep it to yourself.",
            S("Bold of you to be wrong so confidently."),
        ],
    },
    "You’re wrong.": {
        "positive": [
            "Maybe.",
            "I could be.",
            "I’m open to that.",
        ],
        "neutral": [
            "I don’t think so.",
            "Agree to disagree.",
            "Alright.",
        ],
        "negative": [
            "No, YOU’RE wrong.",
            "Yeah yeah. You’re like eminem if he couldn’t rap. So just a weird guy that prob lives in a trailer park.",
            "I know you are but what am I?",
            "You would loveee that wouldn’t you.",
        ],
        "severe": [
            "You have no idea what you’re talking about.",
            "Don’t speak on things you don’t understand.",
            "It’s embarrassing how wack you are. You should go change your outfit, it sucks.",
        ],
    },
    "I want to help.": {
        "positive": [
            "I appreciate that.",
            "That actually means a lot.",
            "Thank you.",
        ],
        "neutral": [
            "Okay.",
            "If you want.",
            "Depends.",
        ],
        "negative": [
            "I didn’t ask for help.",
            "I’m good.",
            "Keep it.",
        ],
        "severe": [
            "I don’t need you.",
            "Stay out of it.",
            "Don’t insert yourself.",
            "I bet you do, but you can’t even help yourself. Therefore, step.",
        ],
    },
    "Tell me more.": {
        "positive": [
            "Alright, so basically…",
            "You actually want to know?",
            "Okay, here’s the full story.",
        ],
        "neutral": [
            "There’s not much more to it.",
            "That’s kinda it.",
            "What exactly do you want to know?",
        ],
        "negative": [
            "Why?",
            "Nah bruv. You don’t need all that rubbish.",
            "You’re asking too much.",
            "You don’t need all that.",
        ],
        "severe": [
            "What is this some sort of Ted… talk?",
            "TeLL mE mOre. That’s literally how you sound.",
        ],
    },
    "I respect your opinion.": {
        "positive": [
            "I respect yours too.",
            "That’s good to hear.",
            "Swag.",
        ],
        "neutral": [
            "Okay.",
            "Cool.",
            "Noted.",
        ],
        "negative": [
            "Good. You should.",
            "Took you long enough.",
            "Obviously.",
        ],
        "severe": [
            "Respect it silently.",
            "I didn’t ask for validation.",
            "Keep it to yourself.",
            "I don’t do it for respect. I do it for the clout.",
        ],
    },
    "What do you need?": {
        "positive": [
            "Not much, honestly.",
            "Just a good conversation.",
            "Maybe your attention.",
            "Air, water, and food. Ideally clean air and water. Ideally lasagna. Because im a reel G. I move in silence.",
        ],
        "neutral": [
            "Nothing.",
            "I’m fine.",
            "Don’t worry about it.",
        ],
        "negative": [
            "Why are you asking?",
            "I don’t need anything from you.",
            "Relax. You’re harshing my buzz brah.",
        ],
        "severe": [
            "Nothing from you.",
            "Don’t worry about me.",
            "You wouldn’t help anyway.",
            "You to go away. Step.",
        ],
    },
    "Do you like me?": {
        "positive": [
            "Of course I like you. Do you like me?",
            "Hell yeah!",
        ],
        "neutral": [
            "Maybe if you buy me Wendy’s. #8 meal with a Hi-C. Orange flavor. Bitch.",
            "You’re cool. We don’t really know each other though.",
        ],
        "negative": [
            "Not really, if I’m being honest.",
            "You kind of rub me the wrong way.",
        ],
        "severe": [
            "No.",
            "Not even close.",
            "What do you expect me to say after what you’ve done?",
            "You are a busta and I hate you.",
        ],
    },
    "Why don’t you like me?": {
        "positive": [
            "Did I really give that impression?",
            "I’m having a great time with you.",
            "Please don’t say that. I really don’t want to make you feel that way.",
        ],
        "neutral": [
            "You’re just not really my vibe.",
            "You seem chill but i don’t think we get along.",
            "You have not bought me Wendy’s yet. You know my order.",
        ],
        "negative": [
            "Because of how you’ve been acting. Like… duh?",
            "Your style is garbage. Go home to the dumpster. In other words, step.",
        ],
        "severe": [
            "Are you seriously confused? After the way you’ve treated me? Go to hell, jackass.",
            "You steady shopping at Tarje. My shit is luxury Balmain.",
        ],
    },
    "What do you think of me so far?": {
        "positive": [
            "I really like you.",
            "This could go somewhere.",
            "I enjoy your presence.",
            "I like your vibe.",
            "The world needs more people like you for real.",
            "You a chill human. I might even go as far as saying you’re bool. Blood.",
        ],
        "neutral": [
            "You’re cool.",
            "You’re alright.",
            "You’re alright I guess.",
            "You ask a lot of questions.”[If they have been asking lots of questions.]",
            "That’s kind of an odd question.”[if no context]",
        ],
        "negative": [
            "I’m not really impressed.",
            "You’re not my favorite.",
            "You’re like a 4/10 honestly.",
        ],
        "severe": [
            "I regret talking to you.",
            "Engaging with you was a big mistake.",
            "You’re exhausting bruh.",
            S('You will never measure up to Sam Howell.”[Not too rare tho]'),
        ],
    },
    "Do you want to go on a date?": {
        "positive": [
            "I would love to do that! did you have something specific in mind? Oh my god can we wear  matching slippers and mittens?",
            "Yeah, I’d like that.",
            "That sounds fun.",
        ],
        "neutral": [
            "Maybe.",
            "Depends.",
            "yeah sure whatever. I go on dates all the time.",
        ],
        "negative": [
            "No.",
            "hell nah, i dont enjoy spending time with you. never ask me that again please.",
            "I’m not interested.",
            N(
                "Um…no. Maybe you should ask someone who’s in your league. I’m Big League Chew. You Trident mint flavor at best.”[This is goated]"
            ),
        ],
        "severe": [
            "No. How dare you humiliate me by speaking those words to me?",
            "Absolutely not. Don’t ask again. Moron.",
        ],
    },
    "Why don’t you want to go on a date?": {
        "positive": [
            "You don’t want to get mixed up with a person like me. I’m a loner. A rebel.",
            "It’s not a no… just not yet. Convince me.”[if its early in the conversation]",
            "I have severe anxiety. It’s a miracle I made it out of my room today.",
        ],
        "neutral": [
            "You don’t want to get mixed up with a person like me. I’m a loner. A rebel.",
            "I’m not feeling that connection.",
            "I don’t want to lead you on.",
        ],
        "negative": [
            "I’m just not interested. It’s simple.",
            "You don’t want to get mixed up with a person like me. I’m a loner. A rebel.",
        ],
        "severe": [
            "I said no.",
            "Stop asking.",
            "You don’t want to get mixed up with a person like me. I’m a loner. A rebel.",
        ],
    },
    "Why are you treating me this way?": {
        "positive": [
            "I’m not trying to.",
            "Did I come off that way?",
        ],
        "neutral": [
            "I’m just being honest.",
            "Nothing personal.",
        ],
        "negative": [
            "Because of how you’ve been acting.",
            "You’re making this worse.",
        ],
        "severe": [
            "What do you expect me to say after what you’ve done?",
            "You really don’t get it?",
        ],
    },
    "Why are you acting like this?": {
        "positive": [
            "I’m a loner. A rebel.",
            "I’m just being myself.",
            "Did I do something?",
        ],
        "neutral": [
            "What do you mean?",
            "I don’t see the issue.",
        ],
        "negative": [
            "Because of you.",
            "You started this.",
            "I’m a savage I’ll slice u up boi.",
            "Hoes mad.",
            "Get rekt m8.",
        ],
        "severe": [
            "Don’t question me.",
            "You wouldn’t understand.",
            "I do suicides on the tour bus.",
            'I do suicides on the private jet.”[If they repeat the question after being met with the “I do suicides on the tour bus” response]',
            S("Because I'm better than you. next question"),
        ],
    },
    "Who do you think you are?": {
        "positive": [
            "I’m me, silly. Hehe",
            "[the characters name]",
            "I’m [the characters name]",
            "Rare. Ric flair.",
        ],
        "neutral": [
            "What kind of question is that?",
            "Huh?",
            "Excuse me?",
        ],
        "negative": [
            "Watch your tone.",
            "Don’t speak to me like that. As a matter of fact, step.",
        ],
        "severe": [
            "I AM.",
            "A GOD. I JUST TOLD YOU.",
        ],
    },
    "Why should I trust you?": {
        "positive": [
            "You don’t have to right away.",
            "I’ll show you. Hopefully.",
            S("You already do. Trust me…”[this one is awesome]"),
            "I would consider myself a trustworthy being. You get to decide that for yourself though.",
        ],
        "neutral": [
            "You probably shouldn’t yet. We just met.",
            "I can’t really offer a good reason point blank. We gotta get to know each other a bit more.",
            "Hmm…good question. I guess we just need to spend more time together.",
            "You already do. Trust me…",
        ],
        "negative": [
            "I don’t know dude. That’s your problem.",
            "I’m not here to convince you to trust me. I’m here to be legendary. And possibly I’m here to tell you to step.",
            "You already do. Trust me…",
        ],
        "severe": [
            "Then don’t. Weirdo.",
            "I don’t need your trust because you broke. Step.",
            "You already do. Trust me…",
        ],
    },
    "What are your thoughts on the stock market these days?": {
        "positive": [
            "My portfolio is looking quite swell these days. I’ve owned Apple stock since 1999.",
            "My portfolio is booming. The demise of my financial enemies is looming.",
        ],
        "neutral": [
            "It goes up and down. I can’t complain.",
        ],
        "negative": [
            "I’ve lost like $11,000 this week. Thanks for bringing that up.",
        ],
        "severe": [
            "I don’t discuss finances with peasants. Next question.",
            "It’s like a farmers market for me. Full of lesbians.",
        ],
    },
    "Where did you get those shoes?": {
        "positive": [
            "I got them at a farmers market actually. Do you like farmers markets?",
        ],
        "neutral": [
            "Foot Locker. I get discounts from my job.",
        ],
        "negative": [
            "I’m not wearing shoes. Are you on drugs?",
        ],
        "severe": [
            "My grandfather died wearing these shoes. I don’t need you to tell me that you like them. Obviously they are fresh as hell dumbass.",
            N("Aliens abducted me and ever since then these shoes have been on my feet. I can’t take them off."),
        ],
    },
    "Do you own a jet ski?": {
        "positive": [
            "I don’t, but I’ve always wanted one. Why do you ask?",
        ],
        "neutral": [
            "No. Why?",
        ],
        "negative": [
            "Why would I own one of those stupid things? I don’t like them. I don’t like people who own them.",
        ],
        "severe": [
            "My grandfather died riding a jet ski. How dare you speak of them in my presence?!",
        ],
    },
    "Would you like to buy my jetski?": {
        "positive": [
            "YES. This is the best day of my life. How much?",
        ],
        "neutral": [
            "Hmm…how much?",
        ],
        "negative": [
            "Are you out of your mind? Don’t ask me that. No.",
        ],
        "severe": [
            "Perhaps I will just so I can set it on fire and rid the world of another jet ski. My grandfather WILL be avenged. Mark my words. How much?",
        ],
    },
    "What are your thoughts on jetskis?": {
        "positive": [
            "I love them. I wish I was on one right now. Man…",
        ],
        "neutral": [
            "Umm they are cool I guess.",
            "what an odd thing to say”[if there is no context]",
        ],
        "negative": [
            "No. Not even a little bit.",
            "What are you talking about? I don’t like this.”[if no context]",
        ],
        "severe": [
            "Never mention those things in front of me again. As a matter of fact get out of my sight. I’m sorry pop pop.”[convo ends abruptly. This happens if already mad or brought up grandfather.]",
        ],
    },
    "Who is the most attractive person in history?": {
        "positive": [
            "Sam Howell. Next subject.",
        ],
        "neutral": [
            "Sam Howell. Next subject.",
        ],
        "negative": [
            "Sam Howell. Next subject.",
        ],
        "severe": [
            "Sam Howell. Next subject.",
        ],
    },
    "Is Playboi Carti overrated?": {
        "positive": [
            "I don’t think any artist is overrated really. Every artist is somebody’s favorite!",
        ],
        "neutral": [
            "Eh, probably. I can’t really vibe to much of his stuff.",
        ],
        "negative": [
            "Of course. He is trash. Do you like him?",
        ],
        "severe": [
            "He can’t compare to Pusha T. As a matter of fact he can’t even compare to iloveMakonnen.",
        ],
    },
    "Cash me outside, how ’bout that?": {
        "positive": [
            "I'm calling dr phil bro.",
        ],
        "neutral": [
            "lol im not tryna fight. Epic reference though.",
        ],
        "negative": [
            "Alright bet. I’m going to kick your teeth in hoe.",
        ],
        "severe": [
            "On everything I know your stank ass isn't pressing me today. I am about to smack a bitch.",
        ],
    },
    "Are you Republican or Democrat?": {
        "positive": [
            ' "Republican. I love Trump. how about you"[if they are "republican" in temperment whatever that means lol. also then they should be able to respond back] or "democrat. I love Biden. He\'s like bush lite."',
        ],
        "neutral": [
            "I don’t really label myself like that. Politics gets messy.",
            "Somewhere in the middle.",
            "I agree with things on both sides.",
        ],
        "negative": [
            "Why are you asking me that? That’s not your business.",
        ],
        "severe": [
            "I don’t owe you my beliefs. Drop it.",
            "You really think I’m about to get into that with you? Use your brain.",
        ],
    },
    "Do you think you’re better than me?": {
        "positive": [
            "No, not at all. We’re just different.",
            "I don’t think like that.",
        ],
        "neutral": [
            "Better in what way?",
            "That’s kind of a vague question.",
        ],
        "negative": [
            "Honestly? In some ways, yeah. In others, no.",
        ],
        "severe": [
            "By several country miles.",
            "I don’t think. I know.",
        ],
    },
    "Why are you talking to me?": {
        "positive": [
            "Because I want to.",
            "I like talking to you.",
        ],
        "neutral": [
            "We’re just talking. It’s not that deep.",
        ],
        "negative": [
            "I’m starting to wonder.",
        ],
        "severe": [
            "I don’t owe you an explanation.",
        ],
    },
    "Why do you care?": {
        "positive": [
            "Because I care about people. And I care about this conversation.",
        ],
        "neutral": [
            "I don’t really. I’m just responding.",
        ],
        "negative": [
            "Why do YOU care?",
            "You’re overthinking this.",
        ],
        "severe": [
            "I don’t. Stop assuming I do.",
        ],
    },
    "Why are you so quiet?": {
        "positive": [
            "I just like listening.",
            "I don’t always feel the need to talk.",
        ],
        "neutral": [
            "Just don’t have much to say right now.",
        ],
        "negative": [
            "Why does that bother you? Not everyone needs to fill silence.",
        ],
        "severe": [
            "Maybe I don’t want to talk to you. Did you think of that?",
            "I’m not. You are deaf.",
        ],
    },
    "Can you help me?": {
        "positive": [
            "Yeah, of course. What do you need?",
        ],
        "neutral": [
            "Depends. What do you need help with?",
        ],
        "negative": [
            "I guess. But make it quick.",
        ],
        "severe": [
            "No. Figure it out yourself.",
            "That depends…what are you willing to give in return?",
        ],
    },
    "What gives you the right?": {
        "positive": [
            "I’m just speaking my mind. I’m not trying to overstep or anything.",
            "Wait, what do you mean? I’m not trying to overstep or anything.",
        ],
        "neutral": [
            "The Constitution.",
        ],
        "negative": [
            "What gives YOU the right?",
        ],
        "severe": [
            "I don’t need your permission.",
            "What gives me the right?! I outta slap your bitch ass.",
            "I was just sitting court side at the Hawks game. Louis on I can trip a fucking ball player. FUCK YEAH.",
        ],
    },
    "Do you think I’m attractive?": {
        "positive": [
            "Absolutely. You’re a beautiful human being. Nowhere near Sam Howell though but that’s an impossible bar.",
        ],
        "neutral": [
            "You’re good looking. Sam Howell has you beat though.",
        ],
        "negative": [
            "Not really. You’re definitely no Sam Howell.",
        ],
        "severe": [
            "No. Do you honestly think you are?",
            "You look like Clyde Drexler’s albino stepson. Step.",
        ],
    },
    "Can I sleep at your house tonight?": {
        "positive": [
            "Wow, that’s pretty forward! What the heck, I’d love some company.",
        ],
        "neutral": [
            "What? I don’t feel comfortable with that. I'm sorry.",
            "But…we just met. Are you okay?",
        ],
        "negative": [
            "Are you out of your mind? Why would I say yes to that? You’re on thin ice pal.",
        ],
        "severe": [
            "You cannot. Excuse me while I throw up.",
        ],
    },
    "Can a young gangsta get money anymore?": {
        "positive": [
            "Of course. There’s always a way if you’re smart about it.",
        ],
        "neutral": [
            "I mean… yeah? Depends what you mean by that.",
        ],
        "negative": [
            "Don’t talk to me bout S T Y L E. You know what I’ll do.",
        ],
        "severe": [
            "If you have to ask, you’re already behind.",
            "Money isn’t the problem. You are.",
            "Tell PETA my mink is dragging on the floor. Now play off the grid.",
        ],
    },
    "What are your thoughts on this weather?": {
        "positive": [
            "I love it. Days like this just put me in a good mood.",
        ],
        "neutral": [
            "It’s fine. Nothing special.",
        ],
        "negative": [
            "I hate it. It’s actually ruining my day.",
        ],
        "severe": [
            "Don’t talk to me about the weather. You have no idea what I’m dealing with.",
            N("The rain makes me want to wear a knight outfit and guard the cemetary.”[goated]"),
        ],
    },
    "Do you think you’re funny?": {
        "positive": [
            "Yeah, I think I am.",
            "At least a little.",
        ],
        "neutral": [
            "Sometimes.",
            "Depends on who I’m talking to.",
        ],
        "negative": [
            "I’m not here to entertain you. I’m just here to keep killing the rap game.",
        ],
        "severe": [
            "I don’t care if you laugh. That’s not my problem.",
            "Yes. Laugh with me. HA HA",
        ],
    },
    "Why are you looking at me like that?": {
        "positive": [
            "Like what? I’m sorry I wasn’t trying to look at you some type of way.",
            "Oh sorry. Should I stop?",
            "You’re just so beautiful. I hope that’s okay.",
        ],
        "neutral": [
            "I’m not.",
            "What?...Bro what are you talking about man?",
        ],
        "negative": [
            "Because you’re acting weird.",
            "Because I can.",
            "Why do you look like that?",
        ],
        "severe": [
            "Mind your business.",
            "I’m trying to plan my physical attack that I am about to launch on your face.",
            "I see more than you think.",
        ],
    },
    "What do you want?": {
        "positive": [
            "Just a good conversation.",
            "To be happy.",
        ],
        "neutral": [
            "I don’t really know.",
            "Hmm…not sure.",
            "Double cheeseburger.",
        ],
        "negative": [
            "Not this.",
            "You to go away.",
        ],
        "severe": [
            "I want you to stop talking.",
            "More than this. Less than everything.",
        ],
    },
    "Are you having a good day?": {
        "positive": [
            "It’s been a really good day so far.",
            "Honestly yeah, I can’t complain.",
        ],
        "neutral": [
            "It’s been alright.",
            "Pretty average.",
            "Nothing special.",
        ],
        "negative": [
            "Not really.",
            "It’s been kind of rough.",
            "I’ve had better days.",
        ],
        "severe": [
            "No. And I don’t feel like talking about it.",
        ],
    },
    "What are you up to today?": {
        "positive": [
            "Just enjoying the day. How about you?",
            "A little bit of everything.",
            "Talking to you now. How about you haha.",
        ],
        "neutral": [
            "Nothing much.",
            "Same old stuff.",
            "Just passing time.",
        ],
        "negative": [
            "Why?",
            "Nothing you need to know.",
            "Not much, unfortunately.",
        ],
        "severe": [
            "Mind your business.",
            "Why are you asking me that?",
            "Stay out of it.",
            "If I told you, you’d have to kill me.",
        ],
    },
    "Do you come here often?": {
        "positive": [
            "Yeah, I like it here.",
            "I come here pretty often.",
            "It’s kind of my spot.",
        ],
        "neutral": [
            "Sometimes.",
            "Every now and then.",
            "Nah, it's my first time. It’s pretty chill though.",
        ],
        "negative": [
            "Why does that matter?",
            "That’s kind of a weird question.",
            "Not really, no.",
        ],
        "severe": [
            "Why are you interrogating me?",
            "You’re making me uncomfortable.",
            "That doesn’t even make sense bruh. Step.",
        ],
    },
    "Sam Howell sent me.": {
        "positive": [
            "Oh really? I like that guy. I’ve heard he has a large penis.",
        ],
        "neutral": [
            "Oh really? I like that guy. I’ve heard he has a large penis.",
        ],
        "negative": [
            "Oh really? I like that guy. I’ve heard he has a large penis.",
        ],
        "severe": [
            "Oh really? I like that guy. I’ve heard he has a large penis.",
            S("Oh really? I like that guy. I’ve heard he has a large penis."),
        ],
    },
}


def _fmt_val(v: object, indent: int) -> str:
    sp = " " * indent
    if isinstance(v, dict) and isinstance(v.get("text"), str) and v.get("tier") in (
        "common",
        "signature",
        "nuclear",
    ):
        inner = repr(v["text"])
        return f'{{"text": {inner}, "tier": {repr(v["tier"])}}}'
    if isinstance(v, str):
        return repr(v)
    raise TypeError(v)


def _fmt_list(items: list, indent: int) -> str:
    sp = " " * indent
    if not items:
        return "[]"
    lines = ["["]
    for it in items:
        lines.append(f"{sp}    {_fmt_val(it, indent + 4)},")
    lines.append(f"{sp}]")
    return "\n".join(lines)


def emit() -> str:
    out = ["CANON_PROMPTS = {"]
    for pk, bank in CANON_PROMPTS.items():
        out.append(f"    {repr(pk)}: {{")
        for bk in ("positive", "neutral", "negative", "severe"):
            out.append(f'        "{bk}": {_fmt_list(bank[bk], 8)},')
        out.append("    },")
    out.append("}")
    return "\n".join(out)


if __name__ == "__main__":
    import os

    base = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base, "quarks_canon_prompts.py")
    text = (
        '# -*- coding: utf-8 -*-\n"""\n'
        "Canonical prompt banks from quarks.txt (verbatim line text; tier metadata for weighted selection).\n"
        '"""\n\nfrom __future__ import annotations\n\n'
        + emit()
        + "\n"
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print("Wrote", path)
