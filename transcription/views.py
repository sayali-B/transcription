import os
from celery.result import AsyncResult
from rest_framework.response import Response
from django.conf import settings
from .tasks import get_ensure_wav_format, get_transcribe_with_diarization
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import TranscriptionTaskModel
from django.http import JsonResponse
from django.conf import settings
from transcription.models import TranscriptionTaskModel
from transcription.tasks import get_ensure_wav_format, get_transcribe_with_diarization
import os


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def transcribe_audio(request):
    """
    Handles the request to start a transcription task. 
    Accepts the audio file path as input, converts it to WAV if necessary,
    saves task details in the database, and triggers the transcription process.
    """
    try:
        print(request.data)
        # Ensure file_path is provided in the request
        audio_file = request.FILES.get("audio_file")
        
        if audio_file:
            upload_directory = os.path.join(settings.BASE_DIR,'transcription', 'media','uploads')
            os.makedirs(upload_directory, exist_ok=True)
            file_path = os.path.join(upload_directory, audio_file.name)

            
            # Write the file to the disk
            with open(file_path, 'wb+') as destination:
                for chunk in audio_file.chunks():
                    destination.write(chunk)

        if not file_path:
            return Response(
                {"error": "No audio file provided. Please upload an audio file."},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = get_ensure_wav_format.delay(file_path)
        wav_file_path, flag_for_deletion = result.get()

        if wav_file_path:
            transcription_task_model = TranscriptionTaskModel.objects.create(
                task_id = result.task_id,
                file_path = wav_file_path,
                audio_file_name = audio_file.name,
                status = "SAVED"
            )


        # Trigger the transcription with diarization task
        get_transcribe_with_diarization.delay(str(result.task_id))

        return JsonResponse({
            "message": "Transcription task started.",
            "task_id": str(result.task_id),
            "converted_file_path": wav_file_path,
            "status": str(result.status)
        }, status=200)

    except Exception as e:
        print(f"Error in start_transcription: {e}")
        return JsonResponse({"error": str(e)}, status=500)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_task_status(request, task_id):
    """
    Check the status of a transcription task and return the transcription result if available.
    """
    try:
        task_result = AsyncResult(task_id)

        # Determine the task's current state
        if task_result.state == "PENDING":
            response_status = "Pending"
            result_data = None
        elif task_result.state == "SUCCESS":
            response_status = "Completed"
            # Retrieve the transcription result from the completed task
            task_output = task_result.result  # Expected to be a dictionary with keys "transcription" and "file"

            result_data = {
                "transcription": task_output.get("transcription", "").splitlines(),
                "file": task_output.get("file")
            }
        elif task_result.state == "FAILURE":
            response_status = "Failed"
            result_data = str(task_result.result)  # Return error details if available
        else:
            response_status = task_result.state
            result_data = None

        return Response({
            "task_id": task_id,
            "status": response_status,
            "result": result_data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        print(f"Error in check_task_status: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
