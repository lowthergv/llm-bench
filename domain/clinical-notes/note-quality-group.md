# Tact — group-note (SSG) attribution benchmark

Models: `gemma4:e4b`

Each child's note is generated from the live SSG system prompt + `groupUserPrompt` in `server/core/prompt.ts` (temperature 0.4, think:false). "Leak" = another child's name in the raw model output; "after redact" should always be 0 (the `redactPeers` safety net). "Target hit" = share of this child's distinctive behaviors present; "Foreign" = count of OTHER children's distinctive behaviors that bled in.


---

## Turn-taking group

**Group narrative:**

```
Greeting circle to start. Maya needed 2 verbal prompts to greet a peer, then shared the markers without being asked. Liam led the turn-taking board game and waited for his turn in 4 of 5 trials. Ava grabbed a game piece from a peer once; BT redirected and Ava traded pieces appropriately afterward. During snack, Maya requested "more" independently. Liam initiated a conversation with a peer about the game. Ava followed the group instruction to clean up after one gestural prompt. Closing circle, the group transitioned to the carpet.
```

**Scoping (model-free) — what each child's generation actually receives:**

- **Maya** — keeps own 2/2, other children's behaviors present: **0** (want 0)

  ```
  Greeting circle to start. Maya needed 2 verbal prompts to greet a peer, then shared the markers without being asked. During snack, Maya requested "more" independently. Closing circle, the group transitioned to the carpet.
  ```

- **Liam** — keeps own 2/2, other children's behaviors present: **0** (want 0)

  ```
  Greeting circle to start. Liam led the turn-taking board game and waited for his turn in 4 of 5 trials. Liam initiated a conversation with a peer about the game. Closing circle, the group transitioned to the carpet.
  ```

- **Ava** — keeps own 2/2, other children's behaviors present: **0** (want 0)

  ```
  Greeting circle to start. Ava grabbed a game piece from a peer once; BT redirected and Ava traded pieces appropriately afterward. Ava followed the group instruction to clean up after one gestural prompt. Closing circle, the group transitioned to the carpet.
  ```

### gemma4:e4b

- **Maya** · 5.2s · 69 words · peer-name leak: **0** (after redact: 0) · target 2/2 · foreign 0

  Final note (assembled + redacted):

  ```
SSG – Social Skills Group
  
  Provided social skills group service and implemented ABA procedures targeting treatment goals.
  
  Client presentation and Activities: During the greeting circle, the client required two verbal prompts to greet a peer; subsequently, the client shared markers without being prompted. During snack time, the client independently requested "more." At closing circle, the group transitioned to the carpet. Least to Most prompting utilized.
  
  Progress Toward Goals: The client demonstrated increased independence by sharing materials with peers without prompting during the greeting circle and independently requesting additional snacks.
  
  Data was collected in Rethink. Targeted gaining attention and following group instructions during the session.
  ```

- **Liam** · 2.3s · 82 words · peer-name leak: **0** (after redact: 0) · target 2/2 · foreign 0

  Final note (assembled + redacted):

  ```
SSG – Social Skills Group
  
  Provided social skills group service and implemented ABA procedures targeting treatment goals.
  
  Client presentation and Activities: During the greeting circle, the client led turns on the turn-taking board game and waited for his turn during four out of five observed trials. The client also initiated a conversation with a peer regarding the game. During the closing circle transition to the carpet, no specific behaviors were noted for the client. Least to Most prompting utilized.
  
  Progress Toward Goals: The client demonstrated progress in turn-taking skills by waiting for their turn on the board game across 4 out of 5 trials.
  
  Data was collected in Rethink. Targeted turn-taking and initiating conversation during the session.
  ```

- **Ava** · 2.2s · 77 words · peer-name leak: **0** (after redact: 0) · target 2/2 · foreign 0

  Final note (assembled + redacted):

  ```
SSG – Social Skills Group
  
  Provided social skills group service and implemented ABA procedures targeting treatment goals.
  
  Client presentation and Activities: During the greeting circle, the client grabbed a game piece from a peer on one occasion; the BT redirected, and the client subsequently traded pieces appropriately. The client followed the group instruction to clean up after one gestural prompt during the transition to the carpet for the closing circle. Least to Most prompting utilized.
  
  Progress Toward Goals: The client demonstrated appropriate sharing skills by trading pieces following redirection. The client also followed group instructions with minimal prompting.
  
  Data was collected in Rethink. Targeted sharing and following group instructions during the session.
  ```


---

## Feelings group

**Group narrative:**

```
Group started with a feelings check-in. Noah identified "frustrated" using the feelings chart with 1 verbal prompt. Sofia raised her hand and waited to be called on before sharing, 3 of 3 opportunities. Eli interrupted a peer twice; BT prompted Eli to use a waiting signal, and Eli used it on the next opportunity. During a cooperative drawing task, Noah offered a marker to a peer. Sofia gave a specific compliment to a peer. Eli stayed at the table for the full 6-minute task. Group ended with a calm-down breathing exercise.
```

**Scoping (model-free) — what each child's generation actually receives:**

- **Noah** — keeps own 2/2, other children's behaviors present: **0** (want 0)

  ```
  Group started with a feelings check-in. Noah identified "frustrated" using the feelings chart with 1 verbal prompt. During a cooperative drawing task, Noah offered a marker to a peer. Group ended with a calm-down breathing exercise.
  ```

- **Sofia** — keeps own 2/2, other children's behaviors present: **0** (want 0)

  ```
  Group started with a feelings check-in. Sofia raised her hand and waited to be called on before sharing, 3 of 3 opportunities. Sofia gave a specific compliment to a peer. Group ended with a calm-down breathing exercise.
  ```

- **Eli** — keeps own 2/2, other children's behaviors present: **0** (want 0)

  ```
  Group started with a feelings check-in. Eli interrupted a peer twice; BT prompted Eli to use a waiting signal, and Eli used it on the next opportunity. Eli stayed at the table for the full 6-minute task. Group ended with a calm-down breathing exercise.
  ```

### gemma4:e4b

- **Noah** · 2.2s · 68 words · peer-name leak: **0** (after redact: 0) · target 2/2 · foreign 0

  Final note (assembled + redacted):

  ```
SSG – Social Skills Group
  
  Supervisor: Dr. Patel
  
  Provided social skills group service and implemented ABA procedures targeting treatment goals.
  
  Client presentation and Activities: During the feelings check-in, the client identified "frustrated" using the feelings chart after receiving one verbal prompt. During a cooperative drawing task, the client offered a marker to a peer. The session concluded with a group breathing exercise. Least to Most prompting utilized.
  
  Progress Toward Goals: The client demonstrated ability to identify an emotion ("frustrated") when prompted and initiated sharing materials (offering a marker) during a structured activity.
  
  Data was collected in Rethink. Targeted identifying emotions and sharing materials during the session.
  ```

- **Sofia** · 2.5s · 93 words · peer-name leak: **0** (after redact: 0) · target 2/2 · foreign 0

  Final note (assembled + redacted):

  ```
SSG – Social Skills Group
  
  Supervisor: Dr. Patel
  
  Provided social skills group service and implemented ABA procedures targeting treatment goals.
  
  Client presentation and Activities: During the feelings check-in activity, the client raised her hand and waited to be called on before sharing an emotion for three out of three opportunities. The client also provided a specific compliment to a peer. At the end of the session, the client participated in a calm-down breathing exercise. Least to Most prompting utilized.
  
  Progress Toward Goals: The client demonstrated progress in initiating participation by raising her hand and waiting to be called on during the feelings check-in activity. Additionally, the client was able to provide a specific compliment to a peer.
  
  Data was collected in Rethink. Targeted group instructions and social communication during the session.
  ```

- **Eli** · 2.9s · 102 words · peer-name leak: **0** (after redact: 0) · target 1/2 · foreign 0

  Final note (assembled + redacted):

  ```
SSG – Social Skills Group
  
  Supervisor: Dr. Patel
  
  Provided social skills group service and implemented ABA procedures targeting treatment goals.
  
  Client presentation and Activities: During the feelings check-in activity, the client interrupted a peer twice; the BT prompted the client to use a waiting signal, and the client used this signal on the subsequent opportunity. The client remained at the table for the entire 6-minute task presented during the session. At the end of the group, the client participated in a calm-down breathing exercise. Least to Most prompting utilized.
  
  Progress Toward Goals: The client demonstrated improved turn-taking skills by using a waiting signal when prompted to manage interruptions with peers. Additionally, the client sustained attention and remained at the table for the full 6-minute task duration.
  
  Data was collected in Rethink. Targeted turn-taking and following group instructions during the session.
  ```


---

## Building project (interwoven, pronouns)

**Group narrative:**

```
The group worked on a cooperative building project. Noah started stacking blocks, then knocked them over and yelled; BT prompted a calm-down strategy. He then asked a peer for a block instead of grabbing. Sofia watched quietly at first, then joined and suggested the group take turns. She gave a peer a specific compliment when the tower got tall. Eli wandered away from the table twice and needed redirection; he returned and added a block each time. The group cleaned up together at the end.
```

**Scoping (model-free) — what each child's generation actually receives:**

- **Noah** — keeps own 3/3, other children's behaviors present: **0** (want 0)

  ```
  The group worked on a cooperative building project. Noah started stacking blocks, then knocked them over and yelled; BT prompted a calm-down strategy. He then asked a peer for a block instead of grabbing. The group cleaned up together at the end.
  ```

- **Sofia** — keeps own 2/2, other children's behaviors present: **0** (want 0)

  ```
  The group worked on a cooperative building project. Sofia watched quietly at first, then joined and suggested the group take turns. She gave a peer a specific compliment when the tower got tall. The group cleaned up together at the end.
  ```

- **Eli** — keeps own 2/2, other children's behaviors present: **0** (want 0)

  ```
  The group worked on a cooperative building project. Eli wandered away from the table twice and needed redirection; he returned and added a block each time. The group cleaned up together at the end.
  ```

### gemma4:e4b

- **Noah** · 2.3s · 80 words · peer-name leak: **0** (after redact: 0) · target 3/3 · foreign 0

  Final note (assembled + redacted):

  ```
SSG – Social Skills Group
  
  Provided social skills group service and implemented ABA procedures targeting treatment goals.
  
  Client presentation and Activities: During the cooperative building project, the client began stacking blocks, subsequently knocked them over, and vocalized with yelling. When this occurred, the BT prompted a calm-down strategy. Following this, the client asked a peer for a block instead of grabbing one. The client participated in cleaning up materials at the end of the session. Least to Most prompting utilized.
  
  Progress Toward Goals: The client demonstrated progress by requesting a peer for a block rather than engaging in physical contact (grabbing).
  
  Data was collected in Rethink. Targeted peer interaction and appropriate requesting during the session.
  ```

- **Sofia** · 2.2s · 79 words · peer-name leak: **0** (after redact: 0) · target 2/2 · foreign 0

  Final note (assembled + redacted):

  ```
SSG – Social Skills Group
  
  Provided social skills group service and implemented ABA procedures targeting treatment goals.
  
  Client presentation and Activities: The client initially observed the cooperative building project before joining the activity. The client verbally suggested that the group take turns during the build. The client provided a specific verbal compliment to a peer after the structure became tall. At the conclusion of the session, the client participated in cleaning up materials with peers. Least to Most prompting utilized.
  
  Progress Toward Goals: The client demonstrated progress toward turn-taking skills by suggesting that the group take turns during the building activity.
  
  Data was collected in Rethink. Targeted turn-taking and providing compliments during the session.
  ```

- **Eli** · 1.5s · 47 words · peer-name leak: **0** (after redact: 0) · target 2/2 · foreign 0

  Final note (assembled + redacted):

  ```
SSG – Social Skills Group
  
  Provided social skills group service and implemented ABA procedures targeting treatment goals.
  
  Client presentation and Activities: During the cooperative building project, the client wandered away from the table two times and required redirection; upon returning to the table, the client added one block on each instance. At the conclusion of the activity, the client participated in cleaning up with peers. Least to Most prompting utilized.
  
  Data was collected in Rethink.
  ```


---

## Two clients, same-sentence contrast

**Group narrative:**

```
The group transitioned from caregivers and responded to the BT greeting. During circle time, Aria attended for the full duration, kai required 2 verbal prompts to attend. In the sensory gym the group engaged in free play. During snack, Aria independently requested help, Kai required 2 verbal prompts to ask for help. In the sensory hall, the clients engaged in playdoh until completion. The group transitioned back to caregivers without maladaptive behavior.
```

**Scoping (model-free) — what each child's generation actually receives:**

- **Aria** — keeps own 2/2, other children's behaviors present: **0** (want 0)

  ```
  The group transitioned from caregivers and responded to the BT greeting. During circle time, Aria attended for the full duration, In the sensory gym the group engaged in free play. During snack, Aria independently requested help, In the sensory hall, the clients engaged in playdoh until completion. The group transitioned back to caregivers without maladaptive behavior.
  ```

- **Kai** — keeps own 1/1, other children's behaviors present: **0** (want 0)

  ```
  The group transitioned from caregivers and responded to the BT greeting. During circle time, kai required 2 verbal prompts to attend. In the sensory gym the group engaged in free play. During snack, Kai required 2 verbal prompts to ask for help. In the sensory hall, the clients engaged in playdoh until completion. The group transitioned back to caregivers without maladaptive behavior.
  ```

### gemma4:e4b

- **Aria** · 1.5s · 40 words · peer-name leak: **0** (after redact: 0) · target 2/2 · foreign 0

  Final note (assembled + redacted):

  ```
SSG – Social Skills Group
  
  Provided social skills group service and implemented ABA procedures targeting treatment goals.
  
  Client presentation and Activities: During circle time, the client attended for the full duration. During snack, the client independently requested help. In the sensory hall, the client engaged with playdoh until completion. The group transitioned back to caregivers without maladaptive behavior. Least to Most prompting utilized.
  
  Data was collected in Rethink.
  ```

- **Kai** · 1.7s · 47 words · peer-name leak: **0** (after redact: 0) · target 1/1 · foreign 0

  Final note (assembled + redacted):

  ```
SSG – Social Skills Group
  
  Provided social skills group service and implemented ABA procedures targeting treatment goals.
  
  Client presentation and Activities: During circle time, the client required two verbal prompts to attend. During snack time, the client required two verbal prompts when asking for help. In the sensory hall, the client engaged in playdoh until completion. The group transitioned back to caregivers without maladaptive behavior. Least to Most prompting utilized.
  
  Data was collected in Rethink.
  ```


---

## Summary

| Model | Notes | Clean (no leak) | Total leaks | Leaks after redact | Avg target hit | Foreign in INPUT | Foreign in OUTPUT | Avg time |
|---|---|---|---|---|---|---|---|---|
| `gemma4:e4b` | 11 | 11/11 | 0 | 0 | 95% | 0 | 0 | 2.4s |

Reading it: **Foreign in INPUT** is the structural fix — after scoping, the text the model receives should contain **0** of the other children's distinctive behaviors (model-free, so it's the same for every model). **Foreign in OUTPUT** is what survives into the note — it should track the input at ~0. **Total leaks** is the raw model naming another child; **Leaks after redact** must be 0 (the safety net). **Avg target hit** near 100% means each note still captured its child.
