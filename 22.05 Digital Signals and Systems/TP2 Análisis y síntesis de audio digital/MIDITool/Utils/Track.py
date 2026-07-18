from dataclasses import dataclass
from Synth.Synth import Synth
from FX.FXInterface import FXInterface
from mido.midifiles.tracks import MidiTrack


@dataclass
class Track:
    data: list
    enabled: bool
    synth: Synth
    fx: list
