"""Stills + hailuo clips for 'Room at the Table' (Suno folk track, 102s).

One scene per lyric beat: the stranger climbing the hill in the rain, the
basket at the door, the hearth, the kettle, the shared table. All in one
hand-painted storybook style so the cuts read as one film; illustrated (not
photoreal) figures also keep the video filters happy.
"""
import os
from generate import generate_image, generate_video

STYLE = ("hand-painted animated film still, soft gouache textures, warm storybook "
         "illustration, gentle film grain, cinematic composition, 16:9")

SCENES = {
    "room_1_hill": (
        f"A small stone cottage on a misty green hillside at dusk in soft rain, one window "
        f"glowing amber, a winding dirt path up the hill, low grey clouds, {STYLE}",
        "Soft drizzle and mist drifting slowly across the hillside, grass swaying gently in "
        "the wind, the cottage window glowing and flickering warmly, very slow push-in, "
        "calm and still"),
    "room_2_traveler": (
        f"A traveler in a long rain-soaked wool coat walking up a muddy hill path toward a "
        f"distant glowing cottage, carrying a woven basket of grain, rain falling, seen "
        f"from behind at a slight angle, {STYLE}",
        "The traveler walks steadily up the hill path through the rain, coat flapping in "
        "the wind, rain streaking down, camera follows slowly from behind"),
    "room_3_door": (
        f"A woven basket of grain set down on the stone step beside an old weathered wooden "
        f"cottage door, the door half open with warm firelight spilling out onto the wet "
        f"step, rain dripping from the eaves, {STYLE}",
        "Warm firelight flickers through the half-open door, rain drips steadily from the "
        "eaves, light glints on the wet stones, static camera, gentle slow push-in"),
    "room_4_hearth": (
        f"Cozy cottage interior at night, a glowing hearth with warm coals and a small fire, "
        f"a rough wooden table set with bread and cups, an empty chair pulled out waiting, "
        f"candles, warm amber light, {STYLE}",
        "The fire crackles and the warm coals glow and pulse, candle flames flicker softly, "
        "warm light dances across the table, static camera, very slow push-in"),
    "room_5_kettle": (
        f"A black iron kettle steaming on a hook over a hearth fire, a small cottage window "
        f"beside it with wind and rain lashing the glass outside, warm interior light, {STYLE}",
        "Steam curls steadily from the kettle spout, fire flickers beneath it, wind-blown "
        "rain streams down the window glass, static camera"),
    "room_6_table": (
        f"Two friends laughing together at a candlelit wooden table in a cozy cottage, one "
        f"splitting an apple in half with a small knife, a coat with a torn sleeve and a "
        f"needle and thread on the table, autumn leaves blowing past the window outside, "
        f"warm amber light, {STYLE}",
        "The two friends laugh warmly and lean toward each other, candlelight flickers, "
        "autumn leaves drift past the window outside, gentle natural motion, static camera"),
}

if __name__ == "__main__":
    os.makedirs("room", exist_ok=True)
    for name, (img_prompt, vid_prompt) in SCENES.items():
        img, clip = f"{name}.png", f"room/{name}.mp4"
        try:
            if not os.path.exists(img):
                generate_image(img_prompt, img)
            if not os.path.exists(clip):
                for attempt in range(3):   # hailuo's text filter is nondeterministic
                    try:
                        generate_video(img, vid_prompt, clip, loop=False,
                                       model="minimax/hailuo-3-max", resolution="768p")
                        break
                    except RuntimeError as e:
                        print(f"attempt {attempt} failed: {e}", flush=True)
                else:
                    raise RuntimeError("all attempts failed")
        except Exception as e:
            print(f"FAILED {name}: {e}", flush=True)
