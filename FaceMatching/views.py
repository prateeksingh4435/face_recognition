from django.shortcuts import render

# Create your views here.
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
import numpy as np
import cv2
from io import BytesIO
from rest_framework import status
from django.core.files.storage import default_storage



logger = logging.getLogger(__name__)

@api_view(['POST'])
def save_user_data(request):
    try:
        logger.info(f"Received data: {request.data}")
        logger.info(f"Received files: {request.FILES}")

        empid = request.data.get('empid')
        if not empid or 'image' not in request.FILES:
            return Response({"success": False, 'message': 'Missing empid or image file'}, status=200)

        serializer = UserDataSerializer(data=request.data)
        if not serializer.is_valid():
            logger.error(f"Serializer errors: {serializer.errors}")
            return Response({"success": False, 'message': serializer.errors}, status=200)

        uploaded_image = request.FILES['image']
        try:
            uploaded_image_file = face_recognition.load_image_file(uploaded_image)
            uploaded_image_encoding = face_recognition.face_encodings(uploaded_image_file)
        except Exception as e:
            logger.error(f"Error loading or processing uploaded image: {str(e)}")
            logger.error(traceback.format_exc())
            return Response({"success": False, 'message': 'Error processing uploaded image'}, status=200)

        if not uploaded_image_encoding:
            return Response({"success": False, 'message': 'No faces found in the uploaded image'}, status=200)

        uploaded_image_encoding = uploaded_image_encoding[0]

        
        user_data = UserData.objects.filter(empid=empid).first()

        if user_data:
            logger.info(f"Found existing user with empid: {empid}")

            user_image_path = user_data.image.path
            if os.path.isfile(user_image_path):
                default_storage.delete(user_image_path)
                logger.info(f"Deleted old image file: {user_image_path}")

          
            if is_image_allocated_to_another_person(uploaded_image_encoding, empid):
                return Response({"success": False, 'message': 'Image is already allocated to another person'}, status=200)

           
            user_data.image = uploaded_image
            user_data.save()
            return Response({"success": True, 'message': 'User data updated successfully'}, status=200)

        else:
            logger.info(f"Creating new user with empid: {empid}")

           
            if is_image_allocated_to_another_person(uploaded_image_encoding, empid):
                return Response({"success": False, 'message': 'Image is already allocated to another person'}, status=200)

           
            serializer.save()
            return Response({"success": True, 'message': 'User data saved successfully'}, status=200)

    except Exception as e:
        logger.error(f"Error saving user data: {str(e)}")
        logger.error(traceback.format_exc())
        return Response({"success": False, 'message': 'An error occurred'}, status=200)

def is_image_allocated_to_another_person(uploaded_image_encoding, current_empid):
   
    user_data_list = UserData.objects.exclude(empid=current_empid)
    for user in user_data_list:
        user_image_path = user.image.path
        if not os.path.isfile(user_image_path):
            continue

        try:
            known_image_file = face_recognition.load_image_file(user_image_path)
            known_image_encoding = face_recognition.face_encodings(known_image_file)
        except Exception as e:
            logger.error(f"Error loading or processing user image: {str(e)}")
            logger.error(traceback.format_exc())
            continue

        if not known_image_encoding:
            continue

        known_image_encoding = known_image_encoding[0]
        results = face_recognition.compare_faces([known_image_encoding], uploaded_image_encoding)

        if results[0]:
            return True  
    return False 
    
 
@csrf_exempt
@api_view(['POST'])
def check_image_match(request):
    
    if 'image' not in request.FILES:
        logger.error('No image file uploaded')
        return JsonResponse({"success": False ,'message': 'No image file uploaded'},status=200)

    uploaded_image = request.FILES['image']

    try:
        unknown_image = face_recognition.load_image_file(uploaded_image)
        unknown_encodings = face_recognition.face_encodings(unknown_image)
       
        
        
    except Exception as e:
        logger.error(f"Error loading or processing uploaded image: {str(e)}")
        logger.error(traceback.format_exc())
        return JsonResponse({"success": False,'message': 'Error processing uploaded image'}, status=200)

    if len(unknown_encodings) == 0:
        logger.warning('No faces found in the uploaded image')
        return JsonResponse({"success": False,'message': 'No faces found in the uploaded image'}, status=200)

    unknown_encoding = unknown_encodings[0]
    print(unknown_encoding)
    matched_image_id = None
    matched = False

    user_data_list = UserData.objects.all()
    
    logger.info(f"Total user images to check: {len(user_data_list)}")

    for user_data in user_data_list:
        user_image_path = user_data.image.path
        if not os.path.isfile(user_image_path):
            logger.warning(f"Image file not found: {user_image_path}")
            continue

        try:
            known_image = face_recognition.load_image_file(user_image_path)
            known_encodings = face_recognition.face_encodings(known_image)
        except Exception as e:
            logger.error(f"Error loading or processing user image: {str(e)}")
            logger.error(traceback.format_exc())
            continue

        if len(known_encodings) == 0:
            logger.warning(f"No faces found in user image: {user_image_path}")
            continue

        known_encoding = known_encodings[0]
        results = face_recognition.compare_faces([known_encoding], unknown_encoding)

        if results[0]:
            matched = True
            matched_image_id = user_data.empid
            logger.info(f"Match found with employee ID: {matched_image_id}")
            break

    if matched:
        return JsonResponse({"success": True,'employeeId': matched_image_id},status=200)
    else:
        logger.info('No match found for the uploaded image')
        return JsonResponse({"success": False ,'message': 'Image not matched'},status=200)


@api_view(['PATCH'])
def update_user_image(request):
    try:
        logger.info(f"Received data: {request.data}")
        logger.info(f"Received files: {request.FILES}")

        empid = request.data.get('empid')
        if not empid:
            return Response({"success": False, 'message': 'Missing empid'}, status=status.HTTP_200_OK)

        if 'image' not in request.FILES:
            return Response({"success": False, 'message': 'Missing image file'}, status=status.HTTP_200_OK)

        uploaded_image = request.FILES['image']

        try:
            uploaded_image_file = face_recognition.load_image_file(uploaded_image)
            uploaded_image_encoding = face_recognition.face_encodings(uploaded_image_file)
        except Exception as e:
            logger.error(f"Error loading or processing uploaded image: {str(e)}")
            logger.error(traceback.format_exc())
            return Response({"success": False, 'message': 'Error processing uploaded image'}, status=status.HTTP_200_OK)

        if not uploaded_image_encoding:
            return Response({"success": False, 'message': 'No faces found in the uploaded image'}, status=status.HTTP_200_OK)

        uploaded_image_encoding = uploaded_image_encoding[0]

        try:
            existing_user = UserData.objects.get(empid=empid)
            existing_image_path = existing_user.image.path

          
            if os.path.isfile(existing_image_path):
                default_storage.delete(existing_image_path)
                logger.info(f"Deleted old image file: {existing_image_path}")

           
            user_data_list = UserData.objects.exclude(empid=empid)
            for user_data in user_data_list:
                user_image_path = user_data.image.path
                if not os.path.isfile(user_image_path):
                    continue

                try:
                    known_image_file = face_recognition.load_image_file(user_image_path)
                    known_image_encoding = face_recognition.face_encodings(known_image_file)
                except Exception as e:
                    logger.error(f"Error loading or processing user image: {str(e)}")
                    logger.error(traceback.format_exc())
                    continue

                if not known_image_encoding:
                    continue

                known_image_encoding = known_image_encoding[0]
                results = face_recognition.compare_faces([known_image_encoding], uploaded_image_encoding)

                if results[0]:
                    return Response({"success": False, 'message': 'Image is already allocated to another employee ID'}, status=status.HTTP_200_OK)

        
            existing_user.image = uploaded_image
            existing_user.save()
            return Response({"success": True, 'message': 'User image updated successfully'}, status=status.HTTP_200_OK)

        except UserData.DoesNotExist:
            return Response({"success": False, 'message': 'Employee ID does not exist'}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error updating user image: {str(e)}")
        return Response({"success": False, 'message': 'An error occurred'}, status=status.HTTP_200_OK)
    


def save_user_view(request):
    return render(request, 'save_user.html')

def check_image_view(request):
    return render(request, 'check_image.html')
