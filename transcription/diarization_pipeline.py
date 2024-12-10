from pyannote.audio import Pipeline   # type: ignore    


def diarization_pipeline(file_path):
    """
    Perform diarization on the given audio file.

    Args:
        file_path (str): Path to the audio file.

    Returns:
        DiarizationResult: The result containing speaker diarization information.
    """
 
 
    pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization", use_auth_token="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")
    diarization = pipeline(file_path)
    return diarization

