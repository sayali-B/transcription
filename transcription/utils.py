
# from celery import shared_task
# import time
# import datetime
# import os
# from transformers import pipeline  # type: ignore
# from pyannote.audio import Pipeline as DiarizationPipeline  # type: ignore
# from pydub import AudioSegment  # type: ignore

# # Initialize Whisper ASR pipeline
# whisper_asr = pipeline("automatic-speech-recognition", model="openai/whisper-base", device="cpu", return_timestamps=True)

# # Initialize the diarization pipeline
# diarization_pipeline = DiarizationPipeline.from_pretrained("pyannote/speaker-diarization", use_auth_token="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")


# def get_calculate_runtime(func):
#     def wrapper(*args, **kwargs):
#         start_time = time.time()
#         print(f"Starting '{func.__name__}' at {time.ctime(start_time)}")
        
#         # Execute the function
#         result = func(*args, **kwargs)
        
#         end_time = time.time()
#         print(f"Ending '{func.__name__}' at {time.ctime(end_time)}")
        
#         # Calculate and print the runtime
#         runtime = end_time - start_time
#         print(f"Total runtime of '{func.__name__}': {runtime:.2f} seconds")
        
#         return result
#     return wrapper


# # Helper function to format seconds into HH:MM:SS
# def format_time(seconds):
#     return str(datetime.timedelta(seconds=int(seconds)))


# # Function to ensure the audio file is in WAV format
# @get_calculate_runtime
# def get_ensure_wav_format(audio_file):
#     try:
#         if audio_file.lower().endswith(".wav"):
#             return audio_file, False  # File is already in WAV format
        
#         # Convert to WAV format using pydub
#         audio = AudioSegment.from_file(audio_file)
#         wav_file = os.path.splitext(audio_file)[0] + ".wav"
#         audio.export(wav_file, format="wav")
#         print(f"Converted {audio_file} to WAV format as {wav_file}")
#         return wav_file, True  # Return the WAV file path and flag for deletion
#     except Exception as e:
#         print(f"Error converting file to WAV: {e}")
#         raise ValueError("Failed to convert audio to WAV format. Ensure the input file is valid and supported.")


# # Function to transcribe audio with diarization
# @shared_task
# @get_calculate_runtime
# def get_transcribe_with_diarization(audio_file, output_dir):
#     # Ensure the audio is in WAV format
#     audio_file, delete_after_use = get_ensure_wav_format(audio_file)

#     # Perform speaker diarization
#     diarization_result = diarization_pipeline(audio_file)
    
#     # Load the entire audio file
#     audio = AudioSegment.from_wav(audio_file)
    
#     # Initialize the transcription results list
#     transcription_output = []

#     current_speaker = None
#     current_transcription = []
    
#     # Iterate over each speaker segment
#     for turn, _, speaker in diarization_result.itertracks(yield_label=True):
#         # Extract audio segment for the current speaker
#         segment_audio = audio[turn.start * 1000 : turn.end * 1000]  # convert seconds to milliseconds
        
#         # Save segment to a temporary file for processing
#         segment_file = f"temp_segment_{speaker}_{int(turn.start)}.wav"
#         segment_audio.export(segment_file, format="wav")
        
#         # Transcribe the audio segment using Whisper
#         segment_transcription = whisper_asr(segment_file)
        
#         # If the speaker changes, append the current transcription to the result and reset
#         if current_speaker != speaker:
#             if current_speaker is not None:
#                 transcription_output.append(f"{current_speaker} {''.join(current_transcription)}")
#             current_speaker = speaker
#             current_transcription = [f"<SPEAKER {speaker.upper()} {format_time(turn.start)}> "]

#         # Append the transcription text for the current speaker segment
#         current_transcription.append(segment_transcription['text'])
        
#         # Delete the temporary audio file after transcription
#         os.remove(segment_file)

#     # Combine the transcription into a single string
#     full_transcription = "\n".join(transcription_output)
    
#     # Define the output file path, using the audio file's name for the transcript file
#     transcript_filename = os.path.splitext(os.path.basename(audio_file))[0] + "_transcription.txt"
#     output_file_path = os.path.join(output_dir, transcript_filename)
    
#     # Write the transcription to the output file
#     with open(output_file_path, "w") as file:
#         file.write(full_transcription)
   
#     print(f"Transcription saved to: {output_file_path}")
    
#     # Delete the converted audio file if it was created
#     if delete_after_use:
#         os.remove(audio_file)
#         print(f"Deleted temporary converted file: {audio_file}")
    
#     return full_transcription, output_file_path
