#!/usr/bin/env python3
"""
SoulX-Singer Metadata Generator
Generate vocal metadata with different styles: robotic, singing, speech, rap

The phoneme dictionary and statistical parameters (durations, pitches, F0)
are calibrated against 274 real working metadata files from the
SoulX-Singer-Eval-Dataset (English subset).
"""

import json
import math
import random
from typing import List, Dict, Tuple
from dataclasses import dataclass


# ============================================================================
# ENGLISH PHONEME DICTIONARY
# Extracted from 274 working metadata files in SoulX-Singer-Eval-Dataset.
# Format: en_<ARPABET phones joined with hyphens>
# ============================================================================

CMU_DICT = {
    "a": "en_AH0",
    "about": "en_AH0-B-AW1-T",
    "across": "en_AH0-K-R-AO1-S",
    "after": "en_AE1-F-T-ER0",
    "again": "en_AH0-G-EH1-N",
    "ago": "en_AH0-G-OW1",
    "ain't": "en_EY1-N-T",
    "air": "en_EH1-R",
    "alive": "en_AH0-L-AY1-V",
    "all": "en_AA1-L",
    "almost": "en_AA1-L-M-OW2-S-T",
    "alone": "en_AH0-L-OW1-N",
    "along": "en_AH0-L-AO1-NG",
    "already": "en_AO1-L-R-EH1-D-IY0",
    "always": "en_AA1-L-W-EY2-Z",
    "am": "en_AE1-M",
    "an": "en_AH0-N",
    "and": "en_AE1-N-D",
    "another": "en_AH0-N-AH1-DH-ER0",
    "anybody": "en_EH1-N-IY0-B-AH0-D-IY0",
    "anyone": "en_EH1-N-IY0-W-AH1-N",
    "anything": "en_EH1-N-IY0-TH-IH2-NG",
    "are": "en_AA1-R",
    "around": "en_ER0-AW1-N-D",
    "as": "en_AE1-Z",
    "asked": "en_AE1-S-K-T",
    "at": "en_AE1-T",
    "away": "en_AH0-W-EY1",
    "babe": "en_B-EY1-B",
    "baby": "en_B-EY1-B-IY0",
    "back": "en_B-AE1-K",
    "band": "en_B-AE1-N-D",
    "be": "en_B-IY1",
    "beach": "en_B-IY1-CH",
    "beast": "en_B-IY1-S-T",
    "beat": "en_B-IY1-T",
    "beats": "en_B-IY1-T-S",
    "beautiful": "en_B-Y-UW1-T-AH0-F-AH0-L",
    "beauty": "en_B-Y-UW1-T-IY0",
    "because": "en_B-IH0-K-AH0-Z",
    "been": "en_B-IH1-N",
    "before": "en_B-IH0-F-AO1-R",
    "begging": "en_B-EH1-G-IH0-NG",
    "begins": "en_B-IH0-G-IH1-N-Z",
    "believe": "en_B-IH0-L-IY1-V",
    "beneath": "en_B-IH0-N-IY1-TH",
    "best": "en_B-EH1-S-T",
    "better": "en_B-EH1-T-ER0",
    "between": "en_B-IY0-T-W-IY1",
    "big": "en_B-IH1-G",
    "birds": "en_B-ER1-D-Z",
    "bit": "en_B-IH1-T",
    "black": "en_B-L-AE1-K",
    "blame": "en_B-L-EY1-M",
    "blue": "en_B-L-UW1",
    "born": "en_B-AO1-R-N",
    "both": "en_B-OW1-TH",
    "brains": "en_B-R-EY1-N-Z",
    "brand": "en_B-R-AE1-N-D",
    "breathing": "en_B-R-IY1-DH-IH0-NG",
    "brightly": "en_B-R-AY1-T-L-IY0",
    "bring": "en_B-R-IH1-NG",
    "build": "en_B-IH1-L-D",
    "burned": "en_B-ER1-N-D",
    "burning": "en_B-ER1-N-IH0-NG",
    "burns": "en_B-ER1-N-Z",
    "but": "en_B-AH1-T",
    "butterfly": "en_B-AH1-T-ER0-F-L-AY2",
    "by": "en_B-AY1",
    "c'mon": "en_K-AH0-M-AA1-N",
    "came": "en_K-EY1-M",
    "can": "en_K-AE1-N",
    "can't": "en_K-AE1-N-T",
    "care": "en_K-EH1-R",
    "cast": "en_K-AE1-S-T",
    "catch": "en_K-AE1-CH",
    "cause": "en_K-AA1-Z",
    "celebrate": "en_S-EH1-L-AH0-B-R-EY2-T",
    "certain": "en_S-ER1-T-AH0-N",
    "chance": "en_CH-AE1-N-S",
    "change": "en_CH-EY1-N-JH",
    "child": "en_CH-AY1-L-D",
    "children": "en_CH-IH1-L-D-R-AH0-N",
    "choose": "en_CH-UW1-Z",
    "city": "en_S-IH1-T-IY0",
    "clear": "en_K-L-IH1-R",
    "close": "en_K-L-OW1-S",
    "cold": "en_K-OW1-L-D",
    "come": "en_K-AH1-M",
    "comes": "en_K-AH1-M-Z",
    "control": "en_K-AH0-N-T-R-OW1-L",
    "cosmic": "en_K-AA1-Z-M-IH0-K",
    "could": "en_K-UH1-D",
    "couldn't": "en_K-UH1-D-AH0-N",
    "cover": "en_K-AH1-V-ER0",
    "crazy": "en_K-R-EY1-Z-IY0",
    "cry": "en_K-R-AY1",
    "dance": "en_D-AE1-N-S",
    "dancing": "en_D-AE1-N-S-IH0-NG",
    "dare": "en_D-EH1-R",
    "dark": "en_D-AA1-R-K",
    "darling": "en_D-AA1-R-L-IH0-NG",
    "day": "en_D-EY1",
    "days": "en_D-EY1-Z",
    "dead": "en_D-EH1-D",
    "december": "en_D-IH0-S-EH1-M-B-ER0",
    "diamond": "en_D-AY1-M-AH0-N-D",
    "didn't": "en_D-IH1-D-AH0-N-T",
    "die": "en_D-AY1",
    "difference": "en_D-IH1-F-ER0-AH0-N-S",
    "distance": "en_D-IH1-S-T-AH0-N-S",
    "do": "en_D-UW1",
    "does": "en_D-AH1-Z",
    "don't": "en_D-OW1-N-T",
    "done": "en_D-AH1-N",
    "door": "en_D-AO1-R",
    "down": "en_D-AW1-N",
    "dreams": "en_D-R-IY1-M-Z",
    "dry": "en_D-R-AY1",
    "each": "en_IY1-CH",
    "ears": "en_IH1-R-Z",
    "easy": "en_IY1-Z-IY0",
    "else": "en_EH1-L-S",
    "embrace": "en_IH0-M-B-R-EY1-S",
    "empty": "en_EH1-M-T-IY0",
    "enough": "en_IH0-N-AH1-F",
    "even": "en_IY1-V-IH0-N",
    "ever": "en_EH1-V-ER0",
    "every": "en_EH1-V-R-IY0",
    "everybody": "en_EH1-V-R-IY0-B-AA2-D-IY0",
    "everything": "en_EH1-V-R-IY0-TH-IH2-NG",
    "everywhere": "en_EH1-V-R-IY0-W-EH2-R",
    "eyes": "en_AY1-Z",
    "face": "en_F-EY1-S",
    "fades": "en_F-EY1-D-Z",
    "fail": "en_F-EY1-L",
    "far": "en_F-AA1-R",
    "fast": "en_F-AE1-S-T",
    "fear": "en_F-IH1-R",
    "feel": "en_F-IY1-L",
    "feeling": "en_F-IY1-L-IH0-NG",
    "feels": "en_F-IY1-L-Z",
    "feet": "en_F-IY1-T",
    "fell": "en_F-EH1-L",
    "felt": "en_F-EH1-L-T",
    "few": "en_F-Y-UW1",
    "fight": "en_F-AY1-T",
    "find": "en_F-AY1-N-D",
    "fine": "en_F-AY1-N",
    "fire": "en_F-AY1-ER0",
    "first": "en_F-ER1-S-T",
    "flight": "en_F-L-AY1-T",
    "float": "en_F-L-OW1-T",
    "flowers": "en_F-L-AW1-ER0-Z",
    "for": "en_F-AO1-R",
    "forever": "en_F-ER0-EH1-V-ER0",
    "forget": "en_F-ER0-G-EH1-T",
    "found": "en_F-AW1-N-D",
    "freedom": "en_F-R-IY1-D-AH0-M",
    "friend": "en_F-R-EH1-N-D",
    "friends": "en_F-R-EH1-N-D-Z",
    "from": "en_F-R-AH1-M",
    "fun": "en_F-AH1-N",
    "funny": "en_F-AH1-N-IY0",
    "game": "en_G-EY1-M",
    "gave": "en_G-EY1-V",
    "get": "en_G-EH1-T",
    "gets": "en_G-EH1-T-S",
    "getting": "en_G-EH1-T-IH0-NG",
    "girl": "en_G-ER1-L",
    "girls": "en_G-ER1-L-Z",
    "give": "en_G-IH1-V",
    "glad": "en_G-L-AE1-D",
    "glass": "en_G-L-AE1-S",
    "go": "en_G-OW1",
    "goes": "en_G-OW1-Z",
    "going": "en_G-OW1-IH0-NG",
    "gold": "en_G-OW1-L-D",
    "gone": "en_G-AA1-N",
    "gonna": "en_G-AA1-N-AH0",
    "good": "en_G-UH1-D",
    "goodbye": "en_G-UH2-D-B-AY1",
    "got": "en_G-AA1-T",
    "gotta": "en_G-AA1-T-AH0",
    "green": "en_G-R-IY1-N",
    "ground": "en_G-R-AW1-N-D",
    "guard": "en_G-AA1-R-D",
    "guess": "en_G-EH1-S",
    "had": "en_HH-AE1-D",
    "hands": "en_HH-AE1-N-Z",
    "happy": "en_HH-AE1-P-IY0",
    "hard": "en_HH-AA1-R-D",
    "has": "en_HH-AE1-Z",
    "have": "en_HH-AE1-V",
    "he": "en_HH-IY1",
    "he's": "en_HH-IY1-Z",
    "head": "en_HH-EH1-D",
    "hear": "en_HH-IY1-R",
    "heard": "en_HH-ER1-D",
    "heart": "en_HH-AA1-R-T",
    "hearts": "en_HH-AA1-R-T-S",
    "help": "en_HH-EH1-L-P",
    "her": "en_HH-ER0",
    "here": "en_HH-IY1-R",
    "hide": "en_HH-AY1-D",
    "high": "en_HH-AY1",
    "him": "en_HH-IH1-M",
    "his": "en_HH-IH1-Z",
    "hold": "en_HH-OW1-L-D",
    "holding": "en_HH-OW1-L-D-IH0-NG",
    "home": "en_HH-OW1-M",
    "hope": "en_HH-OW1-P",
    "house": "en_HH-AW1-S",
    "how": "en_HH-AW1",
    "hurt": "en_HH-ER1-T",
    "hurts": "en_HH-ER1-T-S",
    "i": "en_AY1",
    "i'd": "en_AY1-D",
    "i'll": "en_AY1-L",
    "i'm": "en_AY1-M",
    "i've": "en_AY1-V",
    "if": "en_IH1-F",
    "in": "en_IH0-N",
    "inside": "en_IH0-N-S-AY1-D",
    "instead": "en_IH0-N-S-T-EH1-D",
    "into": "en_IH0-N-T-UW1",
    "is": "en_IH1-Z",
    "it": "en_IH1-T",
    "it's": "en_IH1-T-S",
    "its": "en_IH1-T-S",
    "journey": "en_JH-ER1-N-IY0",
    "joy": "en_JH-OY1",
    "just": "en_JH-AH1-S-T",
    "keep": "en_K-IY1-P",
    "keeps": "en_K-IY1-P-S",
    "kill": "en_K-IH1-L",
    "killed": "en_K-IH1-L-D",
    "king": "en_K-IH1-NG",
    "knew": "en_N-Y-UW1",
    "know": "en_N-OW1",
    "known": "en_N-OW1-N",
    "knows": "en_N-OW1-Z",
    "la": "en_L-AA1",
    "last": "en_L-AE1-S-T",
    "learned": "en_L-ER1-N-D",
    "learning": "en_L-ER1-N-IH0-NG",
    "leave": "en_L-IY1-V",
    "left": "en_L-EH1-F-T",
    "let": "en_L-EH1-T",
    "lies": "en_L-AY1-Z",
    "life": "en_L-AY1-F",
    "light": "en_L-AY1-T",
    "like": "en_L-AY1-K",
    "line": "en_L-AY1-N",
    "listen": "en_L-IH1-S-AH0-N",
    "little": "en_L-IH1-T-AH0-L",
    "lives": "en_L-IH1-V-Z",
    "long": "en_L-AO1-NG",
    "look": "en_L-UH1-K",
    "looking": "en_L-UH1-K-IH0-NG",
    "looks": "en_L-UH1-K-S",
    "lost": "en_L-AA1-S-T",
    "love": "en_L-AH1-V",
    "loved": "en_L-AH1-V-D",
    "low": "en_L-OW1",
    "lucky": "en_L-AH1-K-IY0",
    "made": "en_M-EY1-D",
    "make": "en_M-EY1-K",
    "makes": "en_M-EY1-K-S",
    "making": "en_M-EY1-K-IH0-NG",
    "man": "en_M-AE1-N",
    "many": "en_M-EH1-N-IY0",
    "matter": "en_M-AE1-T-ER0",
    "may": "en_M-EY1",
    "maybe": "en_M-EY1-B-IY0",
    "me": "en_M-IY1",
    "mean": "en_M-IY1-N",
    "meant": "en_M-EH1-N-T",
    "memory": "en_M-EH1-M-ER0-IY0",
    "might": "en_M-AY1-T",
    "mind": "en_M-AY1-N-D",
    "mine": "en_M-AY1-N",
    "missing": "en_M-IH1-S-IH0-NG",
    "mistakes": "en_M-IH0-S-T-EY1-K-S",
    "money": "en_M-AH1-N-IY0",
    "more": "en_M-AO1-R",
    "morning": "en_M-AO1-R-N-IH0-NG",
    "most": "en_M-OW1-S-T",
    "move": "en_M-UW1-V",
    "much": "en_M-AH1-CH",
    "music": "en_M-Y-UW1-Z-IH0-K",
    "my": "en_M-AY1",
    "myself": "en_M-AY2-S-EH1-L-F",
    "na": "en_N-AA1",
    "name": "en_N-EY1-M",
    "near": "en_N-IH1-R",
    "need": "en_N-IY1-D",
    "never": "en_N-EH1-V-ER0",
    "new": "en_N-UW1",
    "next": "en_N-EH1-K-S-T",
    "night": "en_N-AY1-T",
    "no": "en_N-OW1",
    "not": "en_N-AA1-T",
    "nothing": "en_N-AH1-TH-IH0-NG",
    "now": "en_N-AW1",
    "obsessed": "en_AH0-B-S-EH1-S-T",
    "ocean": "en_OW1-SH-AH0-N",
    "of": "en_AH1-V",
    "oh": "en_OW1",
    "old": "en_OW1-L-D",
    "on": "en_AA1-N",
    "once": "en_W-AH1-N-S",
    "one": "en_W-AH1-N",
    "only": "en_OW1-N-L-IY0",
    "ooh": "en_UW1",
    "open": "en_OW1-P-AH0-N",
    "or": "en_AO1-R",
    "other": "en_AH1-DH-ER0",
    "our": "en_AA1-R",
    "out": "en_AW1-T",
    "outside": "en_AW1-T-S-AY1-D",
    "over": "en_OW1-V-ER0",
    "own": "en_OW1-N",
    "pain": "en_P-EY1-N",
    "paradise": "en_P-EH1-R-AH0-D-AY2-S",
    "part": "en_P-AA1-R-T",
    "party": "en_P-AA1-R-T-IY0",
    "pass": "en_P-AE1-S",
    "passed": "en_P-AE1-S-T",
    "path": "en_P-AE1-TH",
    "pay": "en_P-EY1",
    "peace": "en_P-IY1-S",
    "people": "en_P-IY1-P-AH0-L",
    "perfect": "en_P-ER1-F-IH0-K-T",
    "place": "en_P-L-EY1-S",
    "play": "en_P-L-EY1",
    "played": "en_P-L-EY1-D",
    "please": "en_P-L-IY1-Z",
    "powerful": "en_P-AW1-ER0-F-AH0-L",
    "pray": "en_P-R-EY1",
    "pretty": "en_P-R-IH1-T-IY0",
    "price": "en_P-R-AY1-S",
    "pride": "en_P-R-AY1-D",
    "put": "en_P-UH1-T",
    "queen": "en_K-W-IY1-N",
    "quiet": "en_K-W-AY1-AH0-T",
    "radio": "en_R-EY1-D-IY0-OW2",
    "rather": "en_R-AH1-DH-ER0",
    "reach": "en_R-IY1-CH",
    "realize": "en_R-IY1-AH0-L-AY2-Z",
    "really": "en_R-IY1-L-IY0",
    "remember": "en_R-IH0-M-EH1-M-B-ER0",
    "rhyme": "en_R-AY1-M",
    "right": "en_R-AY1-T",
    "rise": "en_R-AY1-Z",
    "rising": "en_R-AY1-Z-IH0-NG",
    "river": "en_R-IH1-V-ER0",
    "road": "en_R-OW1-D",
    "rough": "en_R-AH1-F",
    "run": "en_R-AH1-N",
    "runs": "en_R-AH1-N-Z",
    "rush": "en_R-AH1-SH",
    "sad": "en_S-AE1-D",
    "safe": "en_S-EY1-F",
    "said": "en_S-EH1-D",
    "same": "en_S-EY1-M",
    "saw": "en_S-AO1",
    "say": "en_S-EY1",
    "saying": "en_S-EY1-IH0-NG",
    "says": "en_S-EH1-Z",
    "scared": "en_S-K-EH1-R-D",
    "seasons": "en_S-IY1-Z-AH0-N-Z",
    "see": "en_S-IY1",
    "seem": "en_S-IY1-M",
    "seems": "en_S-IY1-M-Z",
    "seen": "en_S-IY1-N",
    "send": "en_S-EH1-N-D",
    "shadows": "en_SH-AE1-D-OW2-Z",
    "shame": "en_SH-EY1-M",
    "she": "en_SH-IY1",
    "shelter": "en_SH-EH1-L-T-ER0",
    "shining": "en_SH-AY1-N-IH0-NG",
    "should": "en_SH-UH1-D",
    "show": "en_SH-OW1",
    "side": "en_S-AY1-D",
    "sight": "en_S-AY1-T",
    "silence": "en_S-AY1-L-AH0-N-S",
    "since": "en_S-IH1-N-S",
    "sing": "en_S-IH1-NG",
    "singing": "en_S-IH1-NG-IH0-NG",
    "sky": "en_S-K-AY1",
    "slow": "en_S-L-OW1",
    "small": "en_S-M-AO1-L",
    "smile": "en_S-M-AY1-L",
    "so": "en_S-OW1",
    "some": "en_S-AH1-M",
    "somebody": "en_S-AH1-M-B-AA2-D-IY0",
    "someone": "en_S-AH1-M-W-AH2-N",
    "something": "en_S-AH1-M-TH-IH0-NG",
    "sometimes": "en_S-AH1-M-T-AY2-M-Z",
    "song": "en_S-AO1-NG",
    "songs": "en_S-AO1-NG-Z",
    "sorry": "en_S-AA1-R-IY0",
    "soul": "en_S-OW1-L",
    "sound": "en_S-AW1-N-D",
    "spring": "en_S-P-R-IH1-NG",
    "star": "en_S-T-AA1-R",
    "stars": "en_S-T-AA1-R-Z",
    "stay": "en_S-T-EY1",
    "step": "en_S-T-EH1-P",
    "still": "en_S-T-IH1-L",
    "stop": "en_S-T-AA1-P",
    "story": "en_S-T-AO1-R-IY0",
    "strange": "en_S-T-R-EY1-N-JH",
    "streaming": "en_S-T-R-IY1-M-IH0-NG",
    "street": "en_S-T-R-IY1-T",
    "strong": "en_S-T-R-AO1-NG",
    "such": "en_S-AH1-CH",
    "sun": "en_S-AH1-N",
    "sure": "en_SH-UH1-R",
    "surprise": "en_S-ER0-P-R-AY1-Z",
    "sweet": "en_S-W-IY1-T",
    "take": "en_T-EY1-K",
    "tale": "en_T-EY1-L",
    "talk": "en_T-AO1-K",
    "tears": "en_T-IH1-R-Z",
    "tell": "en_T-EH1-L",
    "ten": "en_T-EH1-N",
    "testing": "en_T-EH1-S-T-IH0-NG",
    "than": "en_DH-AH0-N",
    "that": "en_DH-AE1-T",
    "that's": "en_DH-AE1-T-S",
    "the": "en_DH-AH0",
    "them": "en_DH-EH1-M",
    "then": "en_DH-EH1-N",
    "there": "en_DH-EH1-R",
    "there's": "en_DH-EH1-R-Z",
    "these": "en_DH-IY1-Z",
    "they": "en_DH-EY1",
    "they're": "en_DH-EH1-R",
    "thing": "en_TH-IH1-NG",
    "things": "en_TH-IH1-NG-Z",
    "think": "en_TH-IH1-NG-K",
    "this": "en_DH-IH1-S",
    "those": "en_DH-OW1-Z",
    "though": "en_DH-OW1",
    "through": "en_TH-R-UW1",
    "till": "en_T-IH1-L",
    "time": "en_T-AY1-M",
    "times": "en_T-AY1-M-Z",
    "to": "en_T-UW1",
    "today": "en_T-AH0-D-EY1",
    "together": "en_T-AH0-G-EH1-DH-ER0",
    "told": "en_T-OW1-L-D",
    "tonight": "en_T-AH0-N-AY1-T",
    "too": "en_T-UW1",
    "took": "en_T-UH1-K",
    "touch": "en_T-AH1-CH",
    "tough": "en_T-AH1-F",
    "town": "en_T-AW1-N",
    "train": "en_T-R-EY1-N",
    "trouble": "en_T-R-AH1-B-AH0-L",
    "true": "en_T-R-UW1",
    "trust": "en_T-R-AH1-S-T",
    "truth": "en_T-R-UW1-TH",
    "turn": "en_T-ER1-N",
    "turns": "en_T-ER1-N-Z",
    "twice": "en_T-W-AY1-S",
    "two": "en_T-UW1",
    "undone": "en_AH0-N-D-AH1-N",
    "up": "en_AH1-P",
    "upon": "en_AH0-P-AA1-N",
    "us": "en_AH1-S",
    "use": "en_Y-UW1-Z",
    "voice": "en_V-OY1-S",
    "waiting": "en_W-EY1-T-IH0-NG",
    "walked": "en_W-AO1-K-T",
    "wanna": "en_W-AA1-N-AH0",
    "want": "en_W-AA1-N-T",
    "wants": "en_W-AA1-N-T-S",
    "was": "en_W-AH0-Z",
    "watch": "en_W-AA1-CH",
    "water": "en_W-AO1-T-ER0",
    "way": "en_W-EY1",
    "we": "en_W-IY1",
    "we'll": "en_W-IY1-L",
    "we're": "en_W-IH1-R",
    "we've": "en_W-IY1-V",
    "weird": "en_W-IH1-R-D",
    "well": "en_W-EH1-L",
    "were": "en_W-ER0",
    "what": "en_W-AH1-T",
    "when": "en_W-EH1-N",
    "where": "en_W-EH1-R",
    "while": "en_W-AY1-L",
    "who": "en_HH-UW1",
    "whoa": "en_W-OW1",
    "whole": "en_HH-OW1-L",
    "why": "en_W-AY1",
    "will": "en_W-IH1-L",
    "wings": "en_W-IH1-NG-Z",
    "wish": "en_W-IH1-SH",
    "with": "en_W-IH1-DH",
    "within": "en_W-IH0-DH-IH1-N",
    "without": "en_W-IH0-DH-AW1-T",
    "won't": "en_W-OW1-N-T",
    "wonder": "en_W-AH1-N-D-ER0",
    "word": "en_W-ER1-D",
    "words": "en_W-ER1-D-Z",
    "work": "en_W-ER1-K",
    "world": "en_W-ER1-L-D",
    "worth": "en_W-ER1-TH",
    "would": "en_W-UH1-D",
    "wouldn't": "en_W-UH1-D-AH0-N-T",
    "wrong": "en_R-AO1-NG",
    "yeah": "en_Y-AE1",
    "years": "en_Y-IH1-R-Z",
    "yes": "en_Y-EH1-S",
    "yesterday": "en_Y-EH1-S-T-ER0-D-EY2",
    "yet": "en_Y-EH1-T",
    "you": "en_Y-UW1",
    "you'd": "en_Y-UW1-D",
    "you'll": "en_Y-UW1-L",
    "you're": "en_Y-UH1-R",
    "you've": "en_Y-UW1-V",
    "young": "en_Y-AH1-NG",
    "your": "en_Y-UH1-R",
    "yourself": "en_Y-ER0-S-EH1-L-F",
}


# ============================================================================
# STYLE CONFIGURATION
# ============================================================================

@dataclass
class VocalStyle:
    """Configuration for vocal delivery style"""
    name: str

    # Melodic parameters
    pitch_variation: str  # "minimal", "narrow", "wide"
    pitch_range: int  # semitones
    base_pitch: int  # MIDI note

    # Rhythmic parameters
    rhythm_type: str  # "even", "varied", "syncopated", "speech"
    avg_duration: float  # seconds (calibrated for a 3-phone word)
    duration_variance: float  # 0.0-1.0

    # Expressiveness
    vibrato_depth: float  # Hz
    vibrato_rate: float  # Hz
    portamento: bool  # smooth pitch slides

    # Phrasing
    phrase_length: int  # notes per phrase
    breathing_breaks: bool


# Preset styles — pitches calibrated to real data (median MIDI 63, range 40-74)
STYLE_PRESETS = {
    "robotic": VocalStyle(
        name="Robotic/Monotone",
        pitch_variation="minimal",
        pitch_range=0,
        base_pitch=60,          # C4 — neutral center
        rhythm_type="even",
        avg_duration=0.30,      # real median for 3-phone word: 0.41s
        duration_variance=0.0,
        vibrato_depth=0.0,
        vibrato_rate=0.0,
        portamento=False,
        phrase_length=100,      # No breaks
        breathing_breaks=False
    ),

    "singing": VocalStyle(
        name="Melodic Singing",
        pitch_variation="wide",
        pitch_range=12,
        base_pitch=63,          # Eb4 — real median
        rhythm_type="varied",
        avg_duration=0.45,      # slightly above real median 0.41
        duration_variance=0.5,
        vibrato_depth=5.0,
        vibrato_rate=5.0,
        portamento=True,
        phrase_length=4,
        breathing_breaks=True
    ),

    "speech": VocalStyle(
        name="Natural Speech",
        pitch_variation="narrow",
        pitch_range=4,
        base_pitch=60,          # C4
        rhythm_type="speech",
        avg_duration=0.30,
        duration_variance=0.3,
        vibrato_depth=1.0,
        vibrato_rate=3.0,
        portamento=False,
        phrase_length=5,
        breathing_breaks=True
    ),

    "rap": VocalStyle(
        name="Rap Flow",
        pitch_variation="minimal",
        pitch_range=3,
        base_pitch=59,          # B3
        rhythm_type="syncopated",
        avg_duration=0.18,
        duration_variance=0.2,
        vibrato_depth=0.0,
        vibrato_rate=0.0,
        portamento=False,
        phrase_length=8,
        breathing_breaks=False
    ),

    "expressive": VocalStyle(
        name="Expressive/Emotional",
        pitch_variation="wide",
        pitch_range=15,
        base_pitch=63,          # Eb4 — real median
        rhythm_type="varied",
        avg_duration=0.55,
        duration_variance=0.7,
        vibrato_depth=8.0,
        vibrato_rate=6.0,
        portamento=True,
        phrase_length=3,
        breathing_breaks=True
    )
}


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def midi_to_hz(midi_note: int) -> float:
    """Convert MIDI note number to frequency in Hz"""
    return 440.0 * (2 ** ((midi_note - 69) / 12))


def lyrics_to_phonemes(lyrics: str) -> Tuple[List[str], List[str]]:
    """
    Convert lyrics to phonemes using CMU dictionary
    Returns: (phoneme_list, word_list) - one-to-one mapping

    CRITICAL: One word = one phoneme entry (not syllable splitting!)
    """
    words = lyrics.lower().split()
    phonemes = []
    valid_words = []

    for word in words:
        if word in ("<sp>", "<SP>"):
            phonemes.append("<SP>")
            valid_words.append("<SP>")
        elif word in ("<ap>", "<AP>"):
            phonemes.append("<AP>")
            valid_words.append("<AP>")
        elif word in CMU_DICT:
            phonemes.append(CMU_DICT[word])
            valid_words.append(word)
        else:
            print(f"Warning: '{word}' not in dictionary, skipping")

    return phonemes, valid_words


# Phones that are produced without vocal-fold vibration → F0 = 0 in real audio
VOICELESS_PHONES = frozenset({
    'P', 'T', 'K',          # voiceless stops
    'F', 'TH', 'S', 'SH',  # voiceless fricatives
    'HH',                   # glottal fricative
    'CH',                   # voiceless affricate
})


def _get_phones(phoneme: str) -> List[str]:
    """Extract the list of base phones (stress stripped) from a phoneme entry."""
    if phoneme in ("<SP>", "<AP>"):
        return []
    parts = phoneme.split("_", 1)
    raw = parts[1] if len(parts) == 2 else phoneme
    return [p.rstrip('012') for p in raw.split("-")]


def _boundary_silence_frames(phoneme: str, note_type: int = 2) -> Tuple[int, int]:
    """
    How many F0=0.0 frames to place at the onset / offset of a word.

    In real speech & singing the F0 tracker returns 0 during voiceless
    consonants and at inter-word pauses.  The reference working metadata
    shows 2-5 zero frames at most word boundaries.

    Returns (onset_frames, offset_frames).
    """
    if phoneme in ("<SP>", "<AP>"):
        return (0, 0)

    phones = _get_phones(phoneme)
    if not phones:
        return (2, 0)

    first, last = phones[0], phones[-1]

    # --- onset ---
    if first in VOICELESS_PHONES:
        onset = 3          # voiceless consonant: ~60 ms of silence
    elif first not in {'AA', 'AE', 'AH', 'AO', 'AW', 'AY',
                       'EH', 'ER', 'EY', 'IH', 'IY',
                       'OW', 'OY', 'UH', 'UW'}:
        onset = 2          # voiced consonant: ~40 ms word-boundary gap
    else:
        onset = 1          # vowel-initial: brief glottal onset

    # --- offset ---
    if last in VOICELESS_PHONES:
        offset = 2         # voiceless ending: ~40 ms
    else:
        offset = 0         # voiced ending: F0 continues to boundary

    return (onset, offset)


def count_phones(phoneme: str) -> int:
    """
    Count individual phones in a phoneme entry like 'en_T-AH0-N-AY1-T'

    Each hyphen-separated segment is one phone.
    """
    if phoneme in ("<SP>", "<AP>"):
        return 0
    parts = phoneme.split("_", 1)
    if len(parts) == 2:
        phone_part = parts[1]
    else:
        phone_part = phoneme
    return len(phone_part.split("-"))


# ============================================================================
# DURATION GENERATION — calibrated to real data
# ============================================================================

# Median duration (seconds) by phone count, from 274 real metadata files
# 1-phone: 0.260,  2: 0.290,  3: 0.410,  4: 0.520,  5: 0.680,
# 6: 0.820,  7: 0.735,  8+: ~1.0
_DURATION_BY_PHONE_COUNT = {
    1: 0.26, 2: 0.29, 3: 0.41, 4: 0.52, 5: 0.68,
    6: 0.82, 7: 0.74, 8: 1.00,
}


def _reference_duration(phone_count: int) -> float:
    """Look up the calibrated median duration for a given phone count."""
    if phone_count <= 0:
        return 0.30
    if phone_count in _DURATION_BY_PHONE_COUNT:
        return _DURATION_BY_PHONE_COUNT[phone_count]
    # Extrapolate for very long words
    return 1.0 + 0.08 * (phone_count - 8)


def generate_f0_contour(
    note_pitches: List[int],
    durations: List[float],
    style: VocalStyle,
    phonemes: List[str] = None,
    note_types: List[int] = None,
    f0_sample_rate: float = 50.0  # Hz (50 samples per second)
) -> List[float]:
    """
    Generate F0 contour with vibrato, portamento, and natural word-
    boundary silence (onset / offset F0=0.0 frames).

    Uses cumulative rounding so the total number of F0 samples
    exactly equals  round(sum(durations) * sample_rate).
    """
    f0_contour = []
    cumulative_duration = 0.0

    for i, (pitch, dur) in enumerate(zip(note_pitches, durations)):
        cumulative_duration += dur
        target_total = round(cumulative_duration * f0_sample_rate)
        num_samples = max(1, target_total - len(f0_contour))

        if pitch == 0:  # Rest / <SP>
            f0_contour.extend([0.0] * num_samples)
            continue

        # ---- word-boundary silence (onset + offset) ----
        onset_frames = 0
        offset_frames = 0
        if phonemes and i < len(phonemes):
            nt = note_types[i] if note_types and i < len(note_types) else 2
            onset_frames, offset_frames = _boundary_silence_frames(
                phonemes[i], nt
            )
            # Never let silence exceed 40% of the word's frames
            max_silence = num_samples * 2 // 5
            total_silence = onset_frames + offset_frames
            if total_silence > max_silence:
                scale = max_silence / total_silence
                onset_frames = int(onset_frames * scale)
                offset_frames = int(offset_frames * scale)

        voiced_frames = num_samples - onset_frames - offset_frames
        voiced_frames = max(1, voiced_frames)

        # ---- onset silence ----
        f0_contour.extend([0.0] * onset_frames)

        # ---- voiced portion ----
        base_f0 = midi_to_hz(pitch)

        for sample_idx in range(voiced_frames):
            t = (sample_idx / max(1, voiced_frames - 1)
                 if voiced_frames > 1 else 0.0)

            f0_value = base_f0

            # Add vibrato
            if style.vibrato_depth > 0:
                vibrato_phase = 2 * math.pi * style.vibrato_rate * t
                vibrato = style.vibrato_depth * math.sin(vibrato_phase)
                f0_value += vibrato

            # Add portamento (smooth slide to next note)
            if style.portamento and i < len(note_pitches) - 1:
                next_pitch = note_pitches[i + 1]
                if next_pitch != 0:
                    next_f0 = midi_to_hz(next_pitch)
                    if t > 0.7:
                        slide_progress = (t - 0.7) / 0.3
                        f0_value = (base_f0
                                    + (next_f0 - base_f0) * slide_progress)

            f0_contour.append(round(f0_value, 1))

        # ---- offset silence ----
        f0_contour.extend([0.0] * offset_frames)

    return f0_contour


# ============================================================================
# MAIN GENERATOR
# ============================================================================

def generate_metadata(
    lyrics: str,
    style: str = "singing",
    bpm: int = 128,
    melody_guide: List[int] = None,
    custom_style: VocalStyle = None,
    add_phrase_breaks: bool = True
) -> Dict:
    """
    Generate complete SoulX-Singer metadata

    Args:
        lyrics: Text to sing/speak (can include <SP> markers)
        style: Preset name ("robotic", "singing", "speech", "rap", "expressive")
        bpm: Tempo (currently informational)
        melody_guide: Optional MIDI note sequence
        custom_style: Optional custom VocalStyle object
        add_phrase_breaks: Auto-add <SP> markers for phrasing

    Returns:
        Dictionary with complete metadata in SoulX-Singer format
    """

    # Get style configuration
    if custom_style:
        style_config = custom_style
    else:
        style_config = STYLE_PRESETS.get(style, STYLE_PRESETS["singing"])

    print(f"\n{'='*60}")
    print(f"Generating metadata with style: {style_config.name}")
    print(f"{'='*60}\n")

    # 1. Add phrase breaks if needed
    if add_phrase_breaks and style_config.breathing_breaks:
        words = lyrics.split()
        processed_words = ["<SP>"]  # Start with <SP>

        for i, word in enumerate(words):
            processed_words.append(word)
            if (i + 1) % style_config.phrase_length == 0 and i < len(words) - 1:
                processed_words.append("<SP>")

        processed_words.append("<SP>")  # End with <SP>
        lyrics_with_breaks = " ".join(processed_words)
    else:
        lyrics_with_breaks = lyrics
        if not lyrics_with_breaks.startswith("<SP>"):
            lyrics_with_breaks = "<SP> " + lyrics_with_breaks
        if not lyrics_with_breaks.endswith("<SP>"):
            lyrics_with_breaks = lyrics_with_breaks + " <SP>"

    print(f"Processed lyrics: {lyrics_with_breaks}")

    # 2. Convert to phonemes (one word = one phoneme)
    phonemes, words_list = lyrics_to_phonemes(lyrics_with_breaks)
    num_entries = len(phonemes)

    print(f"Total entries: {num_entries} (words + <SP> markers)")

    # 3. Generate pitch sequence
    note_pitches = []
    for i, phoneme in enumerate(phonemes):
        if phoneme in ("<SP>", "<AP>"):
            note_pitches.append(0)
        else:
            if melody_guide and len(melody_guide) > len([p for p in note_pitches if p != 0]):
                melody_idx = len([p for p in note_pitches if p != 0])
                note_pitches.append(melody_guide[melody_idx])
            else:
                if style_config.pitch_variation == "minimal":
                    note_pitches.append(style_config.base_pitch)
                elif style_config.pitch_variation == "narrow":
                    note_pitches.append(
                        style_config.base_pitch + random.randint(-2, 2)
                    )
                else:  # wide
                    base = style_config.base_pitch
                    variation = random.choice([0, 2, 3, 5, 7, -2, -3, -5])
                    pitch = base + variation
                    pitch = max(base - 7,
                                min(base + style_config.pitch_range, pitch))
                    note_pitches.append(pitch)

    if note_pitches:
        non_zero = [p for p in note_pitches if p != 0]
        if non_zero:
            print(f"Pitch range: MIDI {min(non_zero)} to {max(non_zero)}")

    # 4. Generate durations — calibrated to real data statistics
    #    Uses _reference_duration(phone_count) as the baseline for each word,
    #    then applies style-specific variance.
    durations = []
    for i, phoneme in enumerate(phonemes):
        if phoneme in ("<SP>", "<AP>"):
            # Real SP: median 0.36s, mean 0.68s, range 0.04-4.77s
            durations.append(round(random.uniform(0.20, 0.80), 2))
        else:
            phone_count = count_phones(phoneme)
            ref_dur = _reference_duration(phone_count)

            if style_config.rhythm_type == "even":
                dur = ref_dur * 0.75  # robotic = slightly faster than natural
            elif style_config.rhythm_type == "syncopated":
                # Rap: fast, rhythmic patterns
                pattern = [0.8, 0.6, 0.8, 0.6, 1.0]
                dur = ref_dur * pattern[i % len(pattern)] * 0.6
            elif style_config.rhythm_type == "speech":
                # Natural speech variance
                dur = ref_dur * random.uniform(0.7, 1.3)
            else:  # "varied" — singing / expressive
                variance = random.uniform(
                    -style_config.duration_variance,
                    style_config.duration_variance
                )
                dur = ref_dur * (1.0 + variance)

            # Enforce per-phone minimum (60ms) and cap
            min_dur = 0.06 * phone_count if phone_count > 0 else 0.10
            dur = max(min_dur, min(2.5, dur))
            durations.append(round(dur, 2))

    print(f"Duration range: {min(durations):.2f}s to {max(durations):.2f}s")

    # 5. Generate note types
    #    Type 1 = rest (<SP>/<AP>), Type 2 = regular lyric note.
    #    Type 3 = slur — requires real melodic analysis to place correctly.
    #    Using type 3 incorrectly causes the model to garble words, so
    #    we default to type 2 for all pitched entries.
    note_types = []
    for i, phoneme in enumerate(phonemes):
        if phoneme in ("<SP>", "<AP>"):
            note_types.append(1)  # Rest marker
        else:
            note_types.append(2)  # Regular note

    # 6. Generate F0 contour (with word-boundary silence for melody mode)
    f0_contour = generate_f0_contour(
        note_pitches, durations, style_config,
        phonemes=phonemes, note_types=note_types
    )

    print(f"F0 samples: {len(f0_contour)}")
    print(f"F0 samples per entry: {len(f0_contour) / len(phonemes):.1f} average")

    # 7. Build text string from words
    text_string = " ".join(words_list)

    # 8. Build metadata
    # CRITICAL: derive time from F0 count so that  time / 20 == len(f0)
    # exactly (the working examples satisfy this invariant).
    time_ms = len(f0_contour) * 20  # 20 ms per frame at 50 Hz

    metadata = {
        "index": f"generated_{style}_001",
        "language": "English",
        "time": [0, time_ms],
        "duration": " ".join([f"{d:.2f}" for d in durations]),
        "text": text_string,
        "phoneme": " ".join(phonemes),
        "note_pitch": " ".join(map(str, note_pitches)),
        "note_type": " ".join(map(str, note_types)),
        "f0": " ".join([f"{f:.1f}" for f in f0_contour])
    }

    print(f"\n✅ Metadata generated successfully!")
    print(f"Total duration: {sum(durations):.2f}s")
    print(f"{'='*60}\n")

    return metadata


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    import os

    test_lyrics = "tonight love feel music"
    output_dir = os.path.dirname(os.path.abspath(__file__))

    # Use a fixed seed for reproducible benchmarks
    random.seed(42)

    print("\n" + "="*70)
    print("SOULX-SINGER METADATA GENERATOR")
    print("="*70)

    styles = ["singing", "robotic", "speech", "rap", "expressive"]

    for style_name in styles:
        print(f"\n🎵 GENERATING {style_name.upper()} STYLE...")
        metadata = generate_metadata(
            lyrics=test_lyrics,
            style=style_name,
            bpm=128
        )

        output_path = os.path.join(output_dir, f"metadata_{style_name}.json")
        with open(output_path, 'w') as f:
            json.dump([metadata], f, indent=2)
        print(f"✅ Saved: {output_path}")

    print("\n" + "="*70)
    print("ALL STYLES GENERATED SUCCESSFULLY")
    print("="*70)
    print("""
Usage in your code:
   from metadata_generator import generate_metadata
   
   metadata = generate_metadata(
       lyrics="your lyrics here",
       style="singing"  # or "robotic", "speech", "rap", "expressive"
   )
    """)
