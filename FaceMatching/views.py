import os
import face_recognition
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings
import logging
from .serializers import UserDataSerializer
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt


logger = logging.getLogger(__name__)

@api_view(['POST'])
def save_user_data(request):
    try:
        serializer = UserDataSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'User data saved successfully'})
    except Exception as e:
        return Response({'error': str(e)}, status=500)
    
    
    
@csrf_exempt
@api_view(['POST'])
def check_image_match(request):
    try:
        if 'image' not in request.FILES:
            return Response({'error': 'No image file uploaded'}, status=400)

        uploaded_image = request.FILES['image']
        unknown_image = face_recognition.load_image_file(uploaded_image)
        
        unknown_encodings = face_recognition.face_encodings(unknown_image)
        if len(unknown_encodings) == 0:
            return Response({'message': 'No faces found in the uploaded image'}, status=400)
        
        unknown_encoding = unknown_encodings[0]
        user_images_path = os.path.join(settings.MEDIA_ROOT, 'user_images')
        if not os.path.exists(user_images_path):
            return Response({'error': 'User images directory not found'}, status=404)

        matched = False
        for image_name in os.listdir(user_images_path):
            user_image_path = os.path.join(user_images_path, image_name)
            if not os.path.isfile(user_image_path):
                continue

            known_image = face_recognition.load_image_file(user_image_path)
            known_encodings = face_recognition.face_encodings(known_image)
            
            if len(known_encodings) == 0:
                continue

            known_encoding = known_encodings[0]
            if face_recognition.compare_faces([known_encoding], unknown_encoding)[0]:
                matched = True
                break
        
        logger.debug(f"Matched: {matched}")

        if matched:
            return Response({'message': 'Image matched'})
        else:
            return Response({'message': 'Image not matched'})

    except Exception as e:
        logger.error(f"Error in image matching: {str(e)}")
        return Response({'error': 'Internal server error'}, status=500)
def save_user_view(request):
    return render(request, 'save_user.html')

def check_image_view(request):
    return render(request, 'check_image.html')