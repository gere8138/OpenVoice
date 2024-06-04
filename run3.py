# -*- coding: utf-8 -*-
import os
import torch
from openvoice import se_extractor
from openvoice.api import ToneColorConverter

ckpt_converter = 'checkpoints_v2/converter'
device = "cuda:0" if torch.cuda.is_available() else "cpu"
output_dir = 'outputs_v2'

tone_color_converter = ToneColorConverter(f'{ckpt_converter}/config.json', device=device)
tone_color_converter.load_ckpt(f'{ckpt_converter}/checkpoint.pth')

os.makedirs(output_dir, exist_ok=True)

reference_speaker = 'voices/yone_jp.mp3' # This is the voice you want to clone, make folder called voices then write voices/[file name] here
target_se, audio_name = se_extractor.get_se(reference_speaker, tone_color_converter, None, vad=False) #instead of None, write folder file name in processed to skip training period

from melo.api import TTS

inputs = [
    [1,'EN_NEWEST', "Bread is a staple food prepared from a dough of flour usually wheat and water, usually by baking. Throughout recorded history and around the world, it has been an important part of many cultures' diet. It is one of the oldest human-made foods, having been of significance since the dawn of agriculture, and plays an essential role in both religious rituals and secular culture."],
    [2,'JP', "夢ならばどれほどよかったでしょう。未だにあなたのことを夢にみる。忘れた物を取りに帰るように。古びた思い出の埃を払う。戻らない幸せがあることを。最後にあなたが教えてくれた。言えずに隠してた昏い過去も。あなたがいなきゃ永遠に昏いまま。"],
    #[3,'EN_NEWEST', "This portion of the audio is English."],
    #[4, 'JP', "沈むように溶けてゆくように。二人だけの空が広がる夜に。さよならだけだった。その一言で全てが分かった。日が沈み出した空と君の姿。フェンス越しに重なっていた。"]
]

src_path = f'{output_dir}/tmp.wav'

# Speed is adjustable   
speed = 0.9

for input in inputs:
    model = TTS(language=input[1], device=device)
    speaker_ids = model.hps.data.spk2id

    for speaker_key in speaker_ids.keys():
        speaker_id = speaker_ids[speaker_key]
        speaker_key = speaker_key.lower().replace('_', '-')
        
        source_se = torch.load(f'checkpoints_v2/base_speakers/ses/{speaker_key}.pth', map_location=device)
        model.tts_to_file(input[2], speaker_id, src_path, speed=speed)
        save_path = f'{output_dir}/output_v2_{input[0]}.wav'
        # Run the tone color converter
        encode_message = "@MyShell"
        tone_color_converter.convert(
            audio_src_path=src_path, 
            src_se=source_se,
            tgt_se=target_se, 
            output_path=save_path,
            message=encode_message)

from pydub import AudioSegment

final_audio = AudioSegment.silent()

for count in range(len(inputs)):

    count +=1
    cur_clip = AudioSegment.from_wav(f'outputs_v2/output_v2_{count}.wav')

    final_audio = final_audio + cur_clip  

final_audio.export(f'outputs_v2/output_v2_final.wav', format="wav")
