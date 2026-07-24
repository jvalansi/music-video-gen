from generate import generate_video
prompt = ("Flowing aurora light ribbons undulating and morphing in teal, magenta and gold, "
          "bokeh particles drifting, hypnotic liquid light motion, seamless loop")
generate_video("dream_4_neon.png", prompt, "dream_4_neon_clip.mp4", loop=True)
print("OK dream_4_neon_clip.mp4", flush=True)
