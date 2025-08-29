from psychopy import visual, core, event, data, gui
import random

# Setup experiment info
exp_info = {"Participant": "", "Block Order (1=Baseline first, 2=Anxiety first)": random.choice([1, 2])}
dlg = gui.DlgFromDict(exp_info)
if not dlg.OK:
    core.quit()



######### CHAT TOLD ME TO, but idk if i need a decision marker like DECISION_X, should i get a 
######### full 2-second trajectory for later analyses so maybe I can get more subconscious movements?
# =========================
# PARAMETERS (movement-only)
# =========================
DECISION_X = 0.35   # how far left/right counts as a decision (units="height")
INIT_EPS   = 0.02   # radius from center that marks "movement started"
TRIAL_MAX  = 2.0    # seconds per trial
FINAL_EPS  = 0.05   # small dead zone near center for final-side scoring
MIN_DISP   = 0.05   # optional QC: minimal displacement to count as "moved"



###################### fix
#mouse_position = []
#mouse_time = []
#pos = mouse.getPos()




# ==== Text Stimuli Lists ====
go_words_neutral = [
    "chair", "window", "pencil", "book", "lamp", "table", "bottle", "paper", "clock", "door",
    "cup", "plate", "spoon", "bed", "carpet", "mirror", "curtain", "shelf", "wall"
]

go_words_anxiety = [
    "torture", "depression", "nauseous", "unfortunate", "vulnerability", "hopeless", "despair",
    "violence", "devastate", "disapproving", "betrayal", "shameful", "embarrass", "crying",
    "rejection", "disappointing", "sorrow", "terrible", "autopsy", "distressing", "bleeding",
    "insecurity", "unemployed", "abuse", "suffocating", "failure", "panic", "disease", "worry",
    "stress", "anxiety", "nightmare"
]

no_go_words = ["glome", "blint", "snarp", "flart", "dreb", "nust", "vark", "plome", "shant", 
               "drall", "crabble", "jarn", "bliff", "skanter", "crint", "blosh", "jant", "shorp", 
               "broll", "chindle", "twomp", "blaven", "framble", "sprode", "shalp", "drasken", "zindle",
               "snent", "chunder", "fampet"] 


# Sample stimuli
neutral_sample = random.sample(go_words_neutral, 15)
anxiety_sample = random.sample(go_words_anxiety, 15)
pseudo_sample = random.sample(no_go_words, 30)


# Split into blocks
baseline_trials = [{"word": w, "type": "neutral", "go": True, "block": "baseline"} for w in neutral_sample]
baseline_trials += [{"word": w, "type": "pseudoword", "go": False, "block": "baseline"} for w in pseudo_sample[:15]]

anxiety_trials = [{"word": w, "type": "anxiety", "go": True, "block": "anxiety"} for w in anxiety_sample]
anxiety_trials += [{"word": w, "type": "pseudoword", "go": False, "block": "anxiety"} for w in pseudo_sample[15:]]

random.shuffle(baseline_trials)
random.shuffle(anxiety_trials)


# Counterbalance the 2 blocks 
if int(exp_info["Block Order (1=Baseline first, 2=Anxiety first)"]) == 1:
    blocks = [("baseline", baseline_trials), ("anxiety", anxiety_trials)]
else:
    blocks = [("anxiety", anxiety_trials), ("baseline", baseline_trials)]





# Create a window
win = visual.Window(size=(1200, 800), color="black", units="height", fullscr=False)
# Initialize mouse
mouse = event.Mouse(visible=False, win=win)


# Instruction screen
instruction = visual.TextStim(win, text=""" 
Welcome to the task!

On the screen, you will see one word appear at a time.

• If the word is a **REAL English word**, move your hand to the RIGHT as quickly and accurately as you can.
• If the word is **NOT a real English word (a fake word)**, move LEFT.

Try your best to respond quickly and accurately.
Some words may be emotionally intense or unpleasant — this is part of the experiment.

Press the **spacebar** to begin.
""", height=0.035, wrapWidth=1.0, color="white")


# Define fixation cross & End Text 
fixation = visual.TextStim(win, text="+", height=0.1, color="white", pos=(0, 0))
end_text = visual.TextStim(win, text="Experiment complete!\nPress any key to exit.", height=0.07, color="white")


# All my stimuli
stimulus = visual.TextStim(win, text="", height=0.08, color="white")
break_text = visual.TextStim(win, text="Take a short break.\n\nPress space to continue.", height=0.06, color="white")
# Stimuli: anxiety induction elements for the anxiety block
countdown_display = visual.TextStim(win, text="", pos=(0, -0.3), height=0.05, color="red")
feedback_display = visual.TextStim(win, text="", pos=(0, 0), height=0.08, color="red")


clock = core.Clock()
results = []

# display instruction
instruction.draw()
win.flip()
event.waitKeys(keyList=["space"])




# the actual task: Task Loop: with anxiety-inducing countdown and negative feedback 
for block_name, trials in blocks:
    for i, trial in enumerate(trials):
        fixation.draw()
        win.flip()
        core.wait(0.8)

        #reset clocks and mouse each trial
        clock.reset()
        mouse.setPos((0,0))
        mouse.clickReset()

        traj_x, traj_y, traj_t = [], [], []
        init_time  = None            # first movement beyond INIT_EPS
        cross_side = None            # "left"/"right"/None (first crossing of DECISION_X)
        cross_time = None            # time of that first crossing
        stim_onset = clock.getTime()

        
        
        # === stimulus presentation window (2s) ===
        # (present word for full TRIAL_MAX seconds, no stop at crossing)
        stimulus.text = trial["word"]
        while clock.getTime() - stim_onset < TRIAL_MAX:
            stimulus.draw()
            if block_name == "anxiety":
                t_left = TRIAL_MAX - (clock.getTime() - stim_onset)
                countdown_display.text = f"Time Left: {max(0.0, round(t_left, 1))}s"
                countdown_display.draw()
            win.flip()

             # Sample cursor each frame
            x, y = mouse.getPos()
            t = clock.getTime() - stim_onset
            traj_x.append(x); traj_y.append(y); traj_t.append(t)

            # Movement initiation marker
            if init_time is None and (abs(x) > INIT_EPS or abs(y) > INIT_EPS):
                init_time = t

            # Early commitment marker (first side crossed)
            if cross_side is None:
                if x <= -DECISION_X:
                    cross_side = "left"
                    cross_time = t
                elif x >= DECISION_X:
                    cross_side = "right"
                    cross_time = t

        # --------- Final-position accuracy (at end of 2s) ---------
        if len(traj_x) == 0:
            final_side = None
        else:
            final_x = traj_x[-1]
            if abs(final_x) < FINAL_EPS:
                final_side = None  # ended too close to center
            else:
                final_side = "left" if final_x < 0 else "right"


        # Response/RT for storage
        response_final = final_side          # what counts for accuracy
        response_first_cross = cross_side    # optional anchor
        rt_first_cross = cross_time          # optional anchor
        init_latency = init_time             # hesitation time

        # Accuracy by final position
        if trial["go"]:   # real word should end RIGHT
            correct = (response_final == "right") if response_final is not None else None
        else:             # pseudoword should end LEFT
            correct = (response_final == "left") if response_final is not None else None




        # Anxiety feedback (same style as before)
        if block_name == "anxiety":
            if response_final is None:
                feedback_display.text = "Too slow!"
            elif not correct:
                feedback_display.text = "Incorrect!"
            else:
                feedback_display.text = ""
            if feedback_display.text:
                feedback_display.draw()
                win.flip()
                core.wait(1.0)

        # Save trial
        results.append({
            "Participant": exp_info["Participant"],
            "Trial": i + 1,
            "Block": block_name,
            "Word": trial["word"],
            "Type": trial["type"],
            "Go_Trial": trial["go"],
            # Primary outcome (your chosen definition)
            "FinalSide": response_final,       # "left"/"right"/None
            "Correct": correct,                # True/False/None

            # Optional anchors (do NOT end trial at these)
            "InitTime": init_latency,          # first movement time
            "FirstCrossSide": response_first_cross,
            "FirstCrossTime": rt_first_cross,

            # Full continuous trajectory
            "Trajectory_X": traj_x,
            "Trajectory_Y": traj_y,
            "Trajectory_T": traj_t
        })




    # === Break between blocks (doesn't show for last block) ===
    if block_name != blocks[-1][0]:
        break_text.draw()
        win.flip()
        event.waitKeys(keyList=["space"])

 


  




# Save data to file
import os
os.makedirs("GoNoGo_ResultsData", exist_ok=True)
filename_base = f"GoNoGo_ResultsData/GoNoGo_{exp_info['Participant']}"
filename = filename_base
counter = 1
while os.path.exists(filename + ".csv"):
    filename = f"{filename_base}_{counter}"
    counter += 1

data_file = data.ExperimentHandler(dataFileName=filename)

for trial in results:
    for key, value in trial.items():
        data_file.addData(key, value)
    data_file.nextEntry()

data_file.saveAsWideText(filename + ".csv")


# Show end screen
end_text.draw()
win.flip()
event.waitKeys()

# close experiment
win.close()
core.quit()









########### OLD SPACE BAR PRESSING CODE
"""
        if block_name == "anxiety":
            # Show countdown during word presentation
            stimulus.text = trial["word"]
            for j in range(20):  # 2 seconds total (20 x 0.1s)
                countdown_display.text = f"Time Left: {round(2.0 - j * 0.1, 1)}s"
                stimulus.draw()
                countdown_display.draw()
                win.flip()
                keys = event.getKeys(keyList=["space"], timeStamped=clock)
                if keys:
                    break
                core.wait(0.1)
        else:
            # Baseline (no countdown)
            stimulus.text = trial["word"]
            stimulus.draw()
            win.flip()
            keys = event.waitKeys(maxWait=2, keyList=["space"], timeStamped=clock)


        # === Evaluate response and correctness ===
        response = keys is not None and len(keys) > 0
        correct = (trial["go"] and response) or (not trial["go"] and not response)

        # === Show negative feedback if needed (anxiety block only) ===
        if block_name == "anxiety":
            if not response:
                feedback_display.text = "Too slow!"
            elif not correct:
                feedback_display.text = "Incorrect!"
            else:
                feedback_display.text = ""

            if feedback_display.text:
                feedback_display.draw()
                win.flip()
                core.wait(1.0)

        # === Store trial result ===
        results.append({
            "Participant": exp_info["Participant"],
            "Trial": i + 1,
            "Block": block_name,
            "Word": trial["word"],
            "Type": trial["type"],
            "Go_Trial": trial["go"],
            "Response": response,
            "Correct": correct,
            "RT": keys[0][1] if response else None
        })
"""