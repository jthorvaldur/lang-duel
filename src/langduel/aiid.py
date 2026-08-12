"""Domain: telling humans from machines, and surviving the call that follows.

This exists because voice-clone and deepfake scams are now cheap and routine,
and the people most often targeted get the least practice. It is defensive
training, not trivia.

Two production poles, which is what makes this a useful second domain for the
engine: **spot** (identify what you are looking at) and **act** (choose what to
do about it). They are tracked separately, so the app can notice that you are
good at recognising a fake and bad at handling one — the more dangerous gap.

Honesty rules for this content:
* Detection tests that are degrading as models improve are labelled as such.
  Teaching a test that stops working is worse than teaching none.
* The protocol advice (call back on a known number, agree a passphrase) does not
  depend on detection working, which is exactly why it is the core of the domain.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Drill:
    pole: str               # "spot" | "act"
    prompt: str
    options: tuple[str, ...]
    answer: str             # must match one of options
    why: str                # shown after answering, right or wrong
    tag: str = ""
    level: int = 1


# --------------------------------------------------------------------------
# act — the protocol. This is the part that keeps working when detection fails.
# --------------------------------------------------------------------------

ACT: tuple[Drill, ...] = (
    Drill(
        "act",
        "A call comes from your son's number. It is his voice, he is crying, he "
        "has been in an accident and needs bail money now. What do you do first?",
        ("Hang up and call him back on the number you already have for him",
         "Ask him a personal question to confirm it is really him",
         "Stay on the line and keep him talking while you find the money"),
        "Hang up and call him back on the number you already have for him",
        "Hanging up and calling back is the one move that survives a perfect fake. "
        "The attacker controls the channel they called you on — caller ID is trivially "
        "spoofed — but not the number in your own contacts. A real emergency is still "
        "there in two minutes. Staying on the line is what the script is designed to "
        "achieve: it exists to stop you from checking.",
        "callback",
    ),
    Drill(
        "act",
        "They anticipate the callback: 'Don't hang up, don't tell Mum, my phone is "
        "dead, this lawyer's line is the only way to reach me.' What does that tell you?",
        ("It is consistent with a genuine emergency, so continue carefully",
         "The secrecy and channel control are the scam's signature — end the call",
         "Ask to speak to the lawyer to verify their identity"),
        "The secrecy and channel control are the scam's signature — end the call",
        "Urgency plus secrecy plus 'only reachable this way' is the fingerprint. Real "
        "emergencies generate more contact, not less — hospitals and police want you to "
        "call other family. Any pressure not to verify IS the verification: it tells you "
        "verification would break the story.",
        "pressure",
    ),
    Drill(
        "act",
        "What is the single best thing to set up with your family BEFORE any of this "
        "happens?",
        ("An agreed passphrase that never appears online or in messages",
         "A rule that you only speak by video call",
         "Sharing everyone's location with each other"),
        "An agreed passphrase that never appears online or in messages",
        "A shared word or phrase, agreed out loud and never written anywhere digital, "
        "is cheap and holds up even against a flawless voice clone — the model can copy "
        "a voice, but it cannot know something that was never published. Do not use a "
        "pet's name, a birthday or anything answerable from social media.",
        "passphrase",
    ),
    Drill(
        "act",
        "The caller wants payment in gift cards. What does the payment method tell you?",
        ("It is unusual but some legitimate services do accept them",
         "Gift cards, crypto, wire transfer and cash couriers are all irreversibility "
         "tells — no legitimate institution asks for them",
         "It suggests a small enough amount to be low-risk"),
        "Gift cards, crypto, wire transfer and cash couriers are all irreversibility "
        "tells — no legitimate institution asks for them",
        "Every one of these is chosen for the same property: once sent, it cannot be "
        "clawed back. No bank, court, police force or tax authority collects this way. "
        "The payment method alone is sufficient grounds to end the call.",
        "payment",
    ),
    Drill(
        "act",
        "'This is your bank's fraud team. To secure your account, move your money to "
        "this safe account we have opened for you.' What is happening?",
        ("A standard fraud-containment procedure",
         "There is no such thing as a 'safe account' — this is the theft itself",
         "It is legitimate if the number matches the one on your card"),
        "There is no such thing as a 'safe account' — this is the theft itself",
        "Banks never move your money to a new account to protect it. The instruction IS "
        "the attack. Caller ID matching your card's number proves nothing; spoofing the "
        "displayed number is a solved problem for attackers.",
        "bank",
    ),
    Drill(
        "act",
        "You are on a video call with someone claiming to be a colleague, and something "
        "feels off. Which check is most reliable in 2026?",
        ("Ask them to turn their head fully sideways or pass a hand across their face",
         "Contact them through a different channel you already trust and ask if they are "
         "on a call with you",
         "Ask them to say a random sentence to test lip sync"),
        "Contact them through a different channel you already trust and ask if they are "
        "on a call with you",
        "The profile-turn and hand-across-face tests exploited weaknesses in early "
        "real-time face swaps and are steadily degrading as a defence — treat them as a "
        "weak signal, never a clearance. Out-of-band contact does not depend on the fake "
        "being imperfect, so it does not rot as the models improve.",
        "out-of-band",
        level=2,
    ),
    Drill(
        "act",
        "How much recorded audio does a usable voice clone of someone need today?",
        ("Roughly an hour of clean studio speech",
         "A few seconds — a voicemail greeting or a social video is plenty",
         "It cannot be done without the person's cooperation"),
        "A few seconds — a voicemail greeting or a social video is plenty",
        "This is the fact that reframes everything else: 'it sounded exactly like him' "
        "is no longer evidence of anything. Anyone with a public voicemail greeting, a "
        "podcast appearance or a video on social media is clonable. Stop treating a "
        "familiar voice as identification.",
        "capability",
    ),
    Drill(
        "act",
        "After you realise a family member has been targeted, what is worth doing "
        "beyond warning them?",
        ("Nothing — awareness is enough once they know",
         "Report it, and tell the wider family, because target lists get reused and "
         "shared",
         "Change their phone number"),
        "Report it, and tell the wider family, because target lists get reused and "
        "shared",
        "A household that responded once — even by engaging without paying — is marked "
        "as reachable and gets retried, often with a different pretext. Telling the "
        "wider family matters because the next call may impersonate the person who was "
        "targeted this time.",
        "aftermath",
        level=2,
    ),
    Drill(
        "act",
        "A caller correctly knows your address, your employer and your mother's maiden "
        "name. How much should that raise your trust?",
        ("Substantially — that information is not public",
         "Not at all — it is all purchasable from breach data and public records",
         "Enough to continue the call, but not enough to send money"),
        "Not at all — it is all purchasable from breach data and public records",
        "Knowing things about you is the cheapest part of the attack. Breach dumps, data "
        "brokers and public records supply it in bulk, and correct details are used "
        "precisely because they buy trust. Personal knowledge is not authentication.",
        "knowledge",
    ),
    Drill(
        "act",
        "What is the right posture to teach an older relative, in one sentence?",
        ("Learn to spot the fakes",
         "Anyone who creates urgency about money gets hung up on and called back on a "
         "known number — no exceptions, no embarrassment",
         "Never answer calls from unknown numbers"),
        "Anyone who creates urgency about money gets hung up on and called back on a "
        "known number — no exceptions, no embarrassment",
        "Rules beat judgement under pressure, and these calls are engineered to destroy "
        "judgement — panic, a familiar voice, a countdown. A rule that runs before "
        "thinking does not care how good the fake was. Add the 'no embarrassment' part "
        "explicitly: shame about hanging up on a real relative is what the script "
        "exploits, and it is also what stops victims reporting afterwards.",
        "posture",
    ),
)


# --------------------------------------------------------------------------
# spot — recognising synthetic media and machine-written text
# --------------------------------------------------------------------------

SPOT: tuple[Drill, ...] = (
    Drill(
        "spot",
        "Which of these is the WEAKEST evidence that a call is genuine?",
        ("The number matches your contact for that person",
         "The caller knows a shared memory from years ago",
         "The voice sounds exactly right"),
        "The number matches your contact for that person",
        "Caller ID is display data, not identity — spoofing it is free and requires no "
        "skill. Of the three, it is the only one that can be forged with no information "
        "about the target at all.",
        "caller-id",
    ),
    Drill(
        "spot",
        "In machine-written prose, which pattern is the most reliable tell?",
        ("Perfect spelling and grammar",
         "Relentless structural symmetry — balanced paragraphs, triples, "
         "'not just X, but Y' — with no idiolect",
         "Long words"),
        "Relentless structural symmetry — balanced paragraphs, triples, "
        "'not just X, but Y' — with no idiolect",
        "Careful humans also spell well, and plenty use long words. What is unusual is "
        "sustained rhythmic evenness with no personal verbal habits, no pet phrases, no "
        "lopsided paragraph that went on too long because the writer cared about it.",
        "text-rhythm",
    ),
    Drill(
        "spot",
        "A message is fluent, well organised, and hedges every claim carefully. What "
        "should you conclude?",
        ("Almost certainly machine-written",
         "Very little on its own — fluency is weak evidence and confident detection "
         "claims are usually overstated",
         "Almost certainly human, since machines are overconfident"),
        "Very little on its own — fluency is weak evidence and confident detection "
        "claims are usually overstated",
        "This is the honest floor of the domain: past a certain quality, text detection "
        "is unreliable, and automated detectors are notoriously bad — including at "
        "falsely accusing non-native speakers. The goal is calibrated suspicion plus "
        "verification habits, not a detector you carry in your head.",
        "humility",
        level=2,
    ),
    Drill(
        "spot",
        "Which is a genuine current weakness in generated video and images?",
        ("Faces are always blurry",
         "Physical consistency over time and between elements — reflections, shadows, "
         "hands interacting with objects, text on signs, jewellery that changes",
         "They are always too short"),
        "Physical consistency over time and between elements — reflections, shadows, "
        "hands interacting with objects, text on signs, jewellery that changes",
        "Generators model appearance better than they model persistence. Look for things "
        "that must stay consistent: a reflection that disagrees with the room, an earring "
        "that changes shape between shots, text that dissolves when you look twice. Treat "
        "this as a tell that is weakening every year, not a reliable test.",
        "video",
        level=2,
    ),
    Drill(
        "spot",
        "In a live voice call, what is a genuine (if fading) sign of synthesis?",
        ("Any background noise at all",
         "Flat prosody under interruption — odd pauses, breathing that does not match "
         "the sentence, emotion that does not shift when you interrupt",
         "The caller speaking slowly"),
        "Flat prosody under interruption — odd pauses, breathing that does not match "
        "the sentence, emotion that does not shift when you interrupt",
        "Interruption is the useful move: real conversation is full of overlap and "
        "repair, and systems handle that worse than they handle clean monologue. Ask an "
        "unexpected question mid-sentence. Still: treat this as a hint, never a clearance.",
        "voice",
        level=2,
    ),
    Drill(
        "spot",
        "Which question best verifies a caller you know well?",
        ("'What is my date of birth?'",
         "'What did we argue about in the kitchen last Christmas?'",
         "'What is your mother's maiden name?'"),
        "'What did we argue about in the kitchen last Christmas?'",
        "The good question is specific, shared, unpublished, and cannot be answered from "
        "any record. Dates of birth and maiden names are in breach data. Note the "
        "sharper version: ask about something that never happened and see whether they "
        "agree it did.",
        "challenge",
    ),
    Drill(
        "spot",
        "What is the most dangerous thing about a deepfake that is only 80% convincing?",
        ("Nothing — people spot it",
         "It does not need to convince you, only to hold for the ninety seconds of panic "
         "the script needs",
         "It looks obviously wrong"),
        "It does not need to convince you, only to hold for the ninety seconds of panic "
        "the script needs",
        "The fake is not competing with your calm judgement, it is competing with your "
        "judgement while your child is apparently crying. Quality is not the variable "
        "that matters — the time pressure is. Which is why the defence is a rule that "
        "runs before assessment, not a better assessment.",
        "threat-model",
    ),
)

DRILLS: tuple[Drill, ...] = ACT + SPOT
POLES = ("spot", "act")
POLE_LABEL = {"spot": "SPOT IT", "act": "ACT ON IT"}
