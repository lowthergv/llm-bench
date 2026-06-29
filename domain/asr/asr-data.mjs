// Shared data for the on-device ASR benchmark (benchmark/asr.mjs).
//
// SCRIPTS are short, FAKE (no real PHI) RBT-style utterances written in the house style
// (observable language, "the client", "behavior technician") and deliberately dense with
// ABA jargon — that jargon is the hard part for a generic speech model, so it's what we
// score. Numbers are spelled out on purpose: ASR "twelve" vs "12" formatting differences
// would otherwise pollute word-error-rate for reasons unrelated to acoustic accuracy.
//
// `voice`/`rate` spread the clips across macOS `say` accents + speaking rates for speaker
// diversity (the clean-TTS realism gap is then attacked acoustically by augment-asr-corpus.mjs).
//
// JARGON is the clinical-term list scored separately (jargon error rate). Multi-word phrases
// are matched as normalized substrings; see scoreJargon() in asr.mjs.

export const SCRIPTS = [
  {
    id: "01-arrival",
    voice: "Samantha", // en_US
    rate: 185,
    text: "The client arrived with the caregiver and separated without crying or protest. The client greeted the behavior technician and walked to the table after one verbal prompt.",
  },
  {
    id: "02-dtt-tact",
    voice: "Daniel", // en_GB
    rate: 200,
    text: "During discrete trial training the client tacted twelve of twenty picture cards correctly. The behavior technician used a least-to-most prompting hierarchy and faded to independent responses by the final block.",
  },
  {
    id: "03-mand-echoic",
    voice: "Karen", // en_AU
    rate: 175,
    text: "The client emitted eight independent mands for preferred items during the session. On echoic trials the client imitated three of five vocal models, approximating the word more as muh.",
  },
  {
    id: "04-problem-behavior",
    voice: "Moira", // en_IE
    rate: 195,
    text: "When the nonpreferred task was presented the client engaged in head hitting four times. The behavior technician blocked the response, withheld attention, and implemented differential reinforcement of alternative behavior.",
  },
  {
    id: "05-schedule",
    voice: "Rishi", // en_IN
    rate: 180,
    text: "Reinforcement was delivered on a fixed ratio schedule of three correct responses. The behavior technician thinned the schedule to a variable ratio across the session and provided noncontingent reinforcement during breaks.",
  },
  {
    id: "06-pecs-elopement",
    voice: "Tessa", // en_ZA
    rate: 205,
    text: "On the picture exchange communication system the client discriminated between two icons with eight of eight correct. The client eloped toward the door once, and the behavior technician used blocking and a verbal redirect to return to the activity.",
  },
  {
    id: "07-stereotypy-dro",
    voice: "Samantha",
    rate: 215,
    text: "The client engaged in vocal stereotypy during independent play. The behavior technician implemented differential reinforcement of other behavior and provided access to a preferred item after intervals without stereotypy.",
  },
  {
    id: "08-group-social",
    voice: "Daniel",
    rate: 165,
    text: "In the social skills group the client responded to a peer's play initiation and took turns during a cooperative game. The client required two gestural prompts to remain with the group for the full activity.",
  },
];

// Clinical terms scored for jargon error rate. Lowercase; hyphens are normalized to spaces
// before matching, so "least-to-most" also matches "least to most".
export const JARGON = [
  "mand",
  "mands",
  "tact",
  "tacted",
  "echoic",
  "discrete trial training",
  "least to most",
  "prompting hierarchy",
  "faded",
  "differential reinforcement",
  "fixed ratio",
  "variable ratio",
  "noncontingent reinforcement",
  "picture exchange communication system",
  "discriminated",
  "eloped",
  "elopement",
  "blocking",
  "redirect",
  "stereotypy",
  "gestural",
  "echoic trials",
  "vocal models",
];

// Pure-silence clips (seconds) to expose hallucination: a faithful model emits nothing.
export const SILENCE_CLIPS = [2, 4];
