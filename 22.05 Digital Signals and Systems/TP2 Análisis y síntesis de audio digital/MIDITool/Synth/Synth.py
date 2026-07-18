# Import los tres Synths
from Synth.FMSynth import FMSynth
from Synth.PhysicsModelsSynth import synthetizeInstrumentPM
from Synth.SampleBasedSynth import SampleSynth


inst_dic = {"Guitarra electrica": synthetizeInstrumentPM,
            "Clarinete": FMSynth,
            "Tambor": synthetizeInstrumentPM,
            "Arpa": synthetizeInstrumentPM,
            "Piano": SampleSynth,
            "Fu": SampleSynth,
            "Grito de Agus": SampleSynth, }


class Synth():
    def __init__(self):
        self.instrument = "Guitarra electrica"
        self.volume = 0.5

    def config(self, instrument: str, volume: float):
        self.instrument = instrument
        self.volume = volume

    def synthetize(self, track):
        return inst_dic[self.instrument](track, self.instrument, self.volume)
