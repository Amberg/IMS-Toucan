import argparse
import os
from datetime import datetime
from InferenceInterfaces.ToucanTTSInterface import ToucanTTSInterface
from scipy.io.wavfile import write as write_wav

def main(text, language, utterance_wave_file, output_path):
    # Initialize the TTS engine
    tts = ToucanTTSInterface()

    # Set the language
    tts.set_language(language)

    # Load the utterance wave file
    tts.set_utterance_embedding(utterance_wave_file)

    # Convert text to speech
    wave, mel, durations, pitch = tts(text, return_everything=True)
    
    # Save the output wave file with a timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(output_path, f'output_{timestamp}.wav')
    
    # Use scipy.io.wavfile to write the wave file
    write_wav(output_file, 24000, wave)

    print(f"Output saved to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert text to speech.')
    parser.add_argument('text', type=str, help='Text to convert to speech')
    parser.add_argument('language', type=str, help='Language for the TTS')
    parser.add_argument('utterance_wave_file', type=str, help='Path to the utterance wave file')
    parser.add_argument('output_path', type=str, help='Path to save the output wave file')

    args = parser.parse_args()
    main(args.text, args.language, args.utterance_wave_file, args.output_path)