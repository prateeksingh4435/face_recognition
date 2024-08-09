import os
import face_recognition
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings
import logging
from .serializers import UserDataSerializer
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import traceback
from .models import UserData

logger = logging.getLogger(__name__)

@api_view(['POST'])
def save_user_data(request):
    try:
        serializer = UserDataSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'User data saved successfully'})
    except Exception as e:
        logger.error(f"Error saving user data: {str(e)}")
        return Response({'error': str(e)}, status=500)

@csrf_exempt
@api_view(['POST'])
def check_image_match(request):
    if 'image' not in request.FILES:
        logger.error('No image file uploaded')
        return JsonResponse({'error': 'No image file uploaded'}, status=400)

    uploaded_image = request.FILES['image']
    
    try:
        unknown_image = face_recognition.load_image_file(uploaded_image)
        unknown_encodings = face_recognition.face_encodings(unknown_image)
    except Exception as e:
        logger.error(f"Error loading or processing uploaded image: {str(e)}")
        logger.error(traceback.format_exc())
        return JsonResponse({'error': 'Error processing uploaded image'}, status=400)

    if len(unknown_encodings) == 0:
        return JsonResponse({'message': 'No faces found in the uploaded image'}, status=400)

    unknown_encoding = unknown_encodings[0]
    matched_image_id = None
    
    user_data_list = UserData.objects.all()
    

    matched = False
    for user_data in user_data_list:
        user_image_path = user_data.image.path
        if not os.path.isfile(user_image_path):
            continue

        try:
            known_image = face_recognition.load_image_file(user_image_path)
            known_encodings = face_recognition.face_encodings(known_image)
        except Exception as e:
            logger.error(f"Error loading or processing user image: {str(e)}")
            logger.error(traceback.format_exc())
            continue

        if len(known_encodings) == 0:
            continue

        known_encoding = known_encodings[0]
        if face_recognition.compare_faces([known_encoding], unknown_encoding)[0]:
            matched = True
            matched_image_id = user_data.id
            break

    if matched:
        return JsonResponse({'Employee_id': matched_image_id })
    else:
        return JsonResponse({'message': 'Image not matched'})

def save_user_view(request):
    return render(request, 'save_user.html')

def check_image_view(request):
    return render(request, 'check_image.html')
