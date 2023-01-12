import pyasge
import pyfmodex
from pyfmodex.flags import MODE
from game.gamedata import GameData
from enum import IntEnum


class TrackIndex(IntEnum):
    # music
    Title_music = 1
    Stage_music = 2
    Boss_music = 3
    win_music = 4
    lost_music = 5
    # effects
    Menu_jingle = 6
    Transition = 7
    Chest = 8
    Bow_shot = 9
    Sword_swing = 10
    oof = 11


class SoundHandler:

    def __init__(self, game_data: GameData):
        self.data = game_data
        self.sound_engine = pyfmodex.System()
        self.footstep_timer = 0
        self.footstep_instanced = False
        self.current_footstep = False
        self.volume_music = 0.10
        self.volume_sound_effects = 0.15
        self.volume_footsteps = 0.15

        # Music
        self.bg_audio_title = None
        self.bg_audio_dungeon = None
        self.bg_audio_boss = None
        self.bg_audio_gamewon = None
        self.bg_audio_gamelost = None

        # Audio effects
        self.menu_jingle = None
        self.effect_transition = None
        self.chest_open = None
        self.bow_shot = None
        self.sword_swing = None
        self.death_oof = None
        self.footsteps = []

        # audio channels
        self.audio_channel_music = None
        self.audio_channel_effects = None
        self.audio_channel_footsteps = None

        # starts sound engine
        self.sound_engine.init()

        self.initSounds()

    def initSounds(self):
        # Music
        self.bg_audio_title = self.sound_engine.create_sound("./data/soundtrack/Title.mp3", mode=MODE.LOOP_NORMAL)
        self.bg_audio_dungeon = self.sound_engine.create_sound("./data/soundtrack/dungeon_main.mp3", mode=MODE.LOOP_NORMAL)
        self.bg_audio_boss = self.sound_engine.create_sound("data/soundtrack/boss_ost.mp3", mode=MODE.LOOP_NORMAL)
        self.bg_audio_gamewon = self.sound_engine.create_sound("data/soundtrack/game_won.mp3", mode=MODE.LOOP_NORMAL)
        self.bg_audio_gamelost = self.sound_engine.create_sound("data/soundtrack/game_lost.mp3", mode=MODE.LOOP_NORMAL)
        # Sound effects
        self.effect_transition = self.sound_engine.create_sound("data/Effects/transition_effect.mp3", mode=MODE.LOOP_OFF)
        self.menu_jingle = self.sound_engine.create_sound("data/Effects/menu_jingle.mp3", mode=MODE.LOOP_OFF)
        self.chest_open = self.sound_engine.create_sound("data/Effects/chest_opening.mp3", mode=MODE.LOOP_OFF)
        self.bow_shot = self.sound_engine.create_sound("data/Effects/bow_shot.mp3", mode=MODE.LOOP_OFF)
        self.sword_swing = self.sound_engine.create_sound("data/Effects/sword_swing.mp3", mode=MODE.LOOP_OFF)
        self.death_oof = self.sound_engine.create_sound("data/Effects/deathsound.mp3", mode=MODE.LOOP_OFF)
        self.footsteps.append(self.sound_engine.create_sound("data/Effects/footstep01.mp3", mode=MODE.LOOP_OFF))
        self.footsteps.append(self.sound_engine.create_sound("data/Effects/footstep02.mp3", mode=MODE.LOOP_OFF))

    def PlayMusic(self, sound: TrackIndex):
        # stops eventual music playing
        try:
            self.audio_channel_music.stop()
        except:
            pass

        if sound == TrackIndex.Title_music:
            self.audio_channel_music = self.sound_engine.play_sound(self.bg_audio_title)
        elif sound == TrackIndex.Stage_music:
            self.audio_channel_music = self.sound_engine.play_sound(self.bg_audio_dungeon)
        elif sound == TrackIndex.Boss_music:
            self.audio_channel_music = self.sound_engine.play_sound(self.bg_audio_boss)
        elif sound == TrackIndex.lost_music:
            self.audio_channel_music = self.sound_engine.play_sound(self.bg_audio_gamelost)
        elif sound == TrackIndex.win_music:
            self.audio_channel_music = self.sound_engine.play_sound(self.bg_audio_gamewon)
        else:
            print("This is not a music track!")

        self.audio_channel_music.volume = self.volume_music

    def PlayEffect(self, sound: TrackIndex):
        # stops eventual sound effects that are playing
        try:
            self.audio_channel_effects.stop()
        except:
            pass

        if sound == TrackIndex.Transition:
            self.audio_channel_effects = self.sound_engine.play_sound(self.effect_transition)
        elif sound == TrackIndex.Menu_jingle:
            self.audio_channel_effects = self.sound_engine.play_sound(self.menu_jingle)
        elif sound == TrackIndex.Chest:
            self.audio_channel_effects = self.sound_engine.play_sound(self.chest_open)
        elif sound == TrackIndex.Bow_shot:
            self.audio_channel_effects = self.sound_engine.play_sound(self.bow_shot)
        elif sound == TrackIndex.Sword_swing:
            self.audio_channel_effects = self.sound_engine.play_sound(self.sword_swing)
        elif sound == TrackIndex.oof:
            self.audio_channel_effects = self.sound_engine.play_sound(self.death_oof)
        else:
            print("This is not an effect!")

        self.audio_channel_effects.volume = self.volume_sound_effects

    def PlayFootsteps(self, game_time: pyasge.GameTime, player_moving):
        # if the footsteps are playing keep updating timer
        if self.footstep_instanced:
            self.footstep_timer += game_time.fixed_timestep

        # there two ifs will alternate to provide a nice sounding footstep effect
        if player_moving:
            if 0.30 > self.footstep_timer < 0.36 and not self.footstep_instanced:
                self.audio_channel_footsteps = self.sound_engine.play_sound(self.footsteps[self.current_footstep])
                self.audio_channel_footsteps.volume = self.volume_footsteps
                self.current_footstep = not self.current_footstep
                self.footstep_instanced = True

        if self.footstep_timer > 0.41 and self.footstep_instanced:
            try:
                self.audio_channel_footsteps.stop()
            except:
                pass
            self.footstep_timer = 0
            self.footstep_instanced = False

    def RestartAudio(self):
        # This restart the sound engine completely, may cause a crash but if too many effects get played the sound will
        # break, so its risky but needed
        self.sound_engine.close()
        self.sound_engine.init()
