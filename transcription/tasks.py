from celery import shared_task
from concurrent.futures import ThreadPoolExecutor
from pydub import AudioSegment
from django.conf import settings
import os
import time
from transformers import pipeline
from .models import TranscriptionTaskModel
from .diarization_pipeline import diarization_pipeline

whisper_asr = pipeline("automatic-speech-recognition", model="openai/whisper-base", device="cpu", return_timestamps=True)


@shared_task(name = 'get_ensure_wav_format')
def get_ensure_wav_format(audio_file):
    try:
        if audio_file.lower().endswith(".wav"):
            return audio_file, False  # File is already in WAV format
        
        # Convert to WAV format using pydub
        audio = AudioSegment.from_file(audio_file)
        wav_file_path = os.path.splitext(audio_file)[0] + ".wav"
        audio.export(wav_file_path, format="wav")
        print(f"Converted {audio_file} to WAV format as {wav_file_path}")

        # Delete the original file after conversion
        os.remove(audio_file)
        print(f"Deleted the original file: {audio_file}")

        return wav_file_path, True  # Return the WAV file path and flag for deletion
    
    
    except Exception as e:
        print(f"Error converting file to WAV: {e}")
        raise ValueError("Failed to convert audio to WAV format. Ensure the input file is valid and supported.")


@shared_task(name="get_transcription_with_diarization")
def get_transcribe_with_diarization(task_id):
    """
    Transcribe a WAV file with speaker diarization using a ThreadPoolExecutor for parallel processing.
    """
    output_dir = os.path.join(settings.BASE_DIR, "transcription",'media','transacripts')
    os.makedirs(output_dir, exist_ok= True)
    start_time = time.time()

    try:
        # Fetch task details from the database
        transcription_task_model = TranscriptionTaskModel.objects.get(task_id=task_id)
        retrieved_file_path = transcription_task_model.file_path
        print(f"Processing file: {retrieved_file_path}")
        os.makedirs(output_dir, exist_ok=True)

        # Run diarization in a separate thread pool
        with ThreadPoolExecutor(max_workers=4) as executor:
            diarization_future = executor.submit(diarization_pipeline, retrieved_file_path)
            diarization_result = diarization_future.result()  # Wait for diarization to complete
        print("Diarization completed.")

        # Load audio for segmentation
        audio = AudioSegment.from_wav(retrieved_file_path)
        transcription_output = []
        current_speaker = None
        current_transcription = []

        # Process each diarized segment using threading
        def process_segment(turn, speaker):
            segment_audio = audio[turn.start * 1000: turn.end * 1000]
            segment_file = f"temp_segment_{speaker}_{int(turn.start)}.wav"
            segment_audio.export(segment_file, format="wav")
            print(f"Transcribing segment for speaker {speaker}.")
            segment_transcription = whisper_asr(segment_file)
            os.remove(segment_file)
            return speaker, turn.start, segment_transcription["text"]

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(process_segment, turn, speaker)
                for turn, _, speaker in diarization_result.itertracks(yield_label=True)
            ]
            for future in futures:
                speaker, start, text = future.result()
                if current_speaker != speaker:
                    if current_speaker is not None:
                        transcription_output.append(f"{current_speaker} {''.join(current_transcription)}")
                    current_speaker = speaker
                    current_transcription = [f"<SPEAKER {speaker.upper()} {start:.2f}> "]
                current_transcription.append(text)

        transcription_output.append(f"{current_speaker} {''.join(current_transcription)}")
        full_transcription = "\n".join(transcription_output)

        # Save transcription to a file
        transcript_file = os.path.join(output_dir, f"{os.path.basename(retrieved_file_path)}_transcription.txt")
        with open(transcript_file, "w") as f:
            f.write(full_transcription)

        print(f"Transcription saved to {transcript_file}")

        return {"transcription": full_transcription, "file": transcript_file}

    except Exception as e:
        print(f"Error during transcription with diarization: {e}")
        raise

    finally:
        elapsed_time = time.time() - start_time
        print(f"get_transcribe_with_diarization function execution time: {elapsed_time:.4f} seconds")


