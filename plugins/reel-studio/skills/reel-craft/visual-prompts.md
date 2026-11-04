# Writing Higgsfield prompts

Shots are generated one by one, then cut together, so they must look like one video.

1. **Lock a look first.** Decide one line of style for the whole reel and append it to every prompt, e.g.
   `cinematic, warm tungsten light, 35mm, shallow depth of field, vertical 9:16`.
2. **One subject, one action.** "A barista slams a cup on the counter, coffee splashes" beats a list of things.
3. **Describe, don't instruct.** Write what the camera sees, not "show that…".
4. **Camera motion in `motion`**, not in the prompt: `slow push in`, `handheld`, `orbit left`, `crash zoom`, `static`.
5. **Recurring person** → describe them identically every time (age, hair, clothes) or use the same reference image.
6. **No text in AI shots.** Models garble letters. Text comes from `on_screen` captions.
7. **Avoid**: real brand logos, real celebrities, hands doing fine detail work, crowds of faces.
8. **Hook shot** (b1) gets the most dynamic action. Calmer shots for explanation beats.
9. `ai_image` is fine for explanation beats: the editor adds Ken Burns zoom. Use `ai_video` where motion tells the story.
10. Shot length: ask for 5 s clips; the editor trims to the beat.
