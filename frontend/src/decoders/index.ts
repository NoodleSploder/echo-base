// Every decoder module registers itself (calls `registerDecoder` at
// import time -- see DecoderRegistry.ts) as a side effect of being
// imported here. Adding a new decoder is exactly one new import line;
// ReceiverDecoders never changes. Same self-registration pattern as
// geo/layers/index.ts.
import "./AdsbDecoder";
import "./AisDecoder";
import "./AprsDecoder";
import "./Ft8Decoder";
import "./SameDecoder";
import "./SstvDecoder";
