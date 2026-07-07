# FT8 test fixture

`191111_110615.wav` is a real, off-air 15-second FT8 recording (12kHz,
mono, 16-bit PCM) captured 2019-11-11, from the MIT-licensed
[kgoba/ft8_lib](https://github.com/kgoba/ft8_lib) test suite
(`test/wav/191111_110615.wav`). `191111_110615.txt` is that same
repository's independently-published ground-truth decode list for this
recording (21 real stations), used here to verify Echo Base's own FT8
decoder against real-world signals rather than only synthetic ones.

Ground-truth line format: `HHMMSS SNR(dB) dt(s) freq(Hz) ~ message`.
