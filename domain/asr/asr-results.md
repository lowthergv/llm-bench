# Tact — on-device ASR benchmark (robustness)

Corpus: 8 clinical scripts (jargon-dense, 8 speakers/accents) × 5 acoustic conditions = 40 speech clips, plus 3 no-speech clips, 16 kHz mono.

Conditions: **clean**, **reverb**, **phone 12k**, **noise 10dB**, **noise 5dB**. Degraded clips are synthetic (TTS + ffmpeg noise/codec/reverb) — a recording-free stand-in for real dictation; **rerun on human recordings before locking the choice** (docs/voice-and-interview-plan.md §8).

### Word error rate by condition

| Model | clean | reverb | phone 12k | noise 10dB | noise 5dB |
|---|---|---|---|---|---|
| Parakeet TDT 0.6B v3 (mlx) | 4.4% | 4.4% | 4.8% | 5.2% | 8.0% |
| Whisper large-v3-turbo (mlx) | 4.4% | 6.0% | 4.8% | 6.4% | 6.8% |

### Jargon error rate by condition

| Model | clean | reverb | phone 12k | noise 10dB | noise 5dB |
|---|---|---|---|---|---|
| Parakeet TDT 0.6B v3 (mlx) | 9.1% | 9.1% | 9.1% | 13.6% | 13.6% |
| Whisper large-v3-turbo (mlx) | 9.1% | 18.2% | 9.1% | 22.7% | 13.6% |

### Speed & hallucination

| Model | Latency/clip | xRealtime | Load | Phantom words (no-speech) |
|---|---|---|---|---|
| Parakeet TDT 0.6B v3 (mlx) | 165 ms | 68.4x | 1.0s | 0 |
| Whisper large-v3-turbo (mlx) | 492 ms | 22.9x | 0.8s | 6 |

Lower WER / jargon-ER is better; higher xRealtime is faster; phantom should be 0.

---

## Parakeet TDT 0.6B v3 (mlx)

`mlx-community/parakeet-tdt-0.6b-v3` · load 1.0s · 165 ms/clip · 68.4x · phantom 0

Transcripts on **noise 5dB** (hardest condition):

**01-arrival** — WER 0.0%

> The client arrived with the caregiver and separated without crying or protest. The client greeted the behavior technician and walked to the table after one verbal prompt.

**02-dtt-tact** — WER 6.3%

> During discrete trial training the client tacted 12 of 20 picture cards correctly, the behavior technician used a least-to-most prompting hierarchy and faded to independent responses by the final block.

**03-mand-echoic** — WER 20.7%

> The client imitated independent man's for preferred items during the session. On echoic trials the client imitated three of five vocal models, approximating the word morisma.

**04-problem-behavior** — WER 3.4%

> When the nonprofit task was presented the client engaged in head hitting four times, the behavior technician blocked the response, withheld attention, and implemented differential reinforcement of alternative behavior.

**05-schedule** — WER 9.7%

> Reinforcement was delivered on a fixed ratio schedule of three correct responses. The behavior technician pinned the schedule to a variable ratio across the session and provided non-contingent reinforcement during breaks.

**06-pecs-elopement** — WER 15.4%

> On the picture exchange communication system the client discriminated between two icons with 8 of 8 for red, the client emote tore the door once, and the behavior technician used blocking and a verbal redirect to return to the activity.

**07-stereotypy-dro** — WER 0.0%

> The client engaged in vocal stereotypy during independent play, the behavior technician implemented differential reinforcement of other behavior and provided access to a preferred item after intervals without stereotypy.

**08-group-social** — WER 5.7%

> In the social skills group the client responded to a fizz play initiation and took turns during a cooperative game. The cloud required two gestural prompts to remain with the group for the full activity.


---

## Whisper large-v3-turbo (mlx)

`mlx-community/whisper-large-v3-turbo` · load 0.8s · 492 ms/clip · 22.9x · phantom 6

Transcripts on **noise 5dB** (hardest condition):

**01-arrival** — WER 0.0%

>  The client arrived with the caregiver and separated without crying or protest. The client greeted the behavior technician and walked to the table after one verbal prompt.

**02-dtt-tact** — WER 9.4%

>  During discrete trial training the client tacted 12 of 20 picture cards correctly. The behavior technician used a least a most prompting hierarchy and faded to independent responses by the final block.

**03-mand-echoic** — WER 13.8%

>  The client imitated independent mans for preferred items during the session. On echoic trials, the client imitated three of five vocal models, approximating the word more as mark.

**04-problem-behavior** — WER 6.9%

>  When the non-profit task was presented the client engaged in head hitting four times. The behavior technician blocked the response, withheld attention, and implemented differential reinforcement of alternative behavior.

**05-schedule** — WER 9.7%

>  Reinforcement was delivered on a fixed ratio schedule of three correct responses. The behavior technician pinned the schedule to a variable ratio across the session and provided non-contingent reinforcement during breaks.

**06-pecs-elopement** — WER 10.3%

>  On the picture exchange communication system the client discriminated between two icons with 8 of 8 per rig. The client eloped toward the door once, and the behavior technician used blocking and a verbal redirect to return to the activity.

**07-stereotypy-dro** — WER 0.0%

>  The client engaged in vocal stereotypy during independent play. The behavior technician implemented differential reinforcement of other behavior and provided access to a preferred item after intervals without stereotypy.

**08-group-social** — WER 2.9%

>  In the social skills group the client responded to a Fizz play initiation and took turns during a cooperative game. The client required two gestural prompts to remain with the group for the full activity.

