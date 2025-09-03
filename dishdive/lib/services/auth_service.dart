import 'dart:io';
import 'package:dio/dio.dart';
import 'package:dishdive/Utils/api_config.dart';

class AuthService {
  final Dio _dio = Dio();

  // Login method
  Future<Map<String, dynamic>> login(String username, String password) async {
    try {
      final response = await _dio.post(
        ApiConfig.loginEndpoint,
        data: {
          "user_name": username,
          "password_hash": password,
        },
        options: Options(headers: ApiConfig.jsonHeaders),
      );

      if (response.statusCode == 200) {
        return {
          'success': true,
          'data': response.data,
          'message': 'Login successful',
        };
      } else {
        return {
          'success': false,
          'message': 'Login failed with status: ${response.statusCode}',
        };
      }
    } catch (e) {
      String errorMessage = 'Failed to connect to server';
      if (e is DioException) {
        if (e.response?.statusCode == 401) {
          errorMessage = 'Invalid username or password';
        } else if (e.response?.statusCode == 400) {
          errorMessage = 'Please check your credentials';
        }
      }
      return {
        'success': false,
        'message': errorMessage,
      };
    }
  }

  // Register method
  Future<Map<String, dynamic>> register(
      String username, String password, File imageFile) async {
    try {
      // Validate image file
      if (!await imageFile.exists()) {
        return {
          'success': false,
          'message': 'Selected image file not found',
        };
      }

      // Check file size (5MB limit)
      final int fileSizeInBytes = await imageFile.length();
      const int maxSizeInBytes = 5 * 1024 * 1024; // 5MB
      
      if (fileSizeInBytes > maxSizeInBytes) {
        return {
          'success': false,
          'message': 'Image size must be less than 5MB',
        };
      }

      // Check file extension
      final String fileName = imageFile.path.toLowerCase();
      if (!fileName.endsWith('.jpg') && 
          !fileName.endsWith('.jpeg') && 
          !fileName.endsWith('.png') && 
          !fileName.endsWith('.webp')) {
        return {
          'success': false,
          'message': 'Only JPG, PNG, and WebP images are supported',
        };
      }

      print('🔧 DEBUG: Starting registration...');
      print('🔧 DEBUG: Username: $username');
      print('🔧 DEBUG: Image file: ${imageFile.path}');
      print('🔧 DEBUG: File size: ${fileSizeInBytes} bytes');

      var payload = FormData.fromMap({
        "user_name": username,
        "password_hash": password,
        'file': await MultipartFile.fromFile(
          imageFile.path,
          filename: imageFile.path.split('/').last,
        ),
      });

      print('🔧 DEBUG: Payload created, sending to: ${ApiConfig.registerEndpoint}');

      final response = await _dio.post(
        ApiConfig.registerEndpoint,
        data: payload,
        options: Options(
          receiveTimeout: const Duration(seconds: 30), // 30 seconds for upload
          sendTimeout: const Duration(seconds: 30),
          headers: {
            // Don't set Content-Type for multipart - let Dio handle it
          },
        ),
      );

      print('🔧 DEBUG: Response status: ${response.statusCode}');
      print('🔧 DEBUG: Response data: ${response.data}');

      if (response.statusCode == 201) {
        return {
          'success': true,
          'data': response.data,
          'message': 'Registration successful',
        };
      } else {
        return {
          'success': false,
          'message': 'Registration failed with status: ${response.statusCode}',
        };
      }
    } catch (e) {
      print('🔧 DEBUG: Error occurred: $e');
      if (e is DioException) {
        print('🔧 DEBUG: DioException type: ${e.type}');
        print('🔧 DEBUG: Response status: ${e.response?.statusCode}');
        print('🔧 DEBUG: Response data: ${e.response?.data}');
        print('🔧 DEBUG: Request data: ${e.requestOptions.data}');
      }
      
      String errorMessage = 'Failed to connect to server';
      if (e is DioException) {
        if (e.response?.statusCode == 500) {
          errorMessage = 'User might already exist or server error';
        } else if (e.response?.statusCode == 400) {
          // Get more specific error from response
          final responseData = e.response?.data;
          if (responseData is String) {
            errorMessage = responseData;
          } else if (responseData is Map && responseData.containsKey('message')) {
            errorMessage = responseData['message'];
          } else {
            errorMessage = 'Invalid input data or image upload failed';
          }
        } else if (e.type == DioExceptionType.sendTimeout || 
                   e.type == DioExceptionType.receiveTimeout) {
          errorMessage = 'Upload timeout. Please check your connection and try again.';
        } else if (e.type == DioExceptionType.connectionError) {
          errorMessage = 'Connection error. Please check your internet connection.';
        }
      }
      return {
        'success': false,
        'message': errorMessage,
      };
    }
  }

  // Get current user
  Future<Map<String, dynamic>> getCurrentUser(String token) async {
    try {
      final response = await _dio.get(
        ApiConfig.getCurrentUserEndpoint,
        options: Options(headers: ApiConfig.authHeaders(token)),
      );

      if (response.statusCode == 200) {
        return {
          'success': true,
          'data': response.data,
        };
      } else {
        return {
          'success': false,
          'message': 'Failed to get user data',
        };
      }
    } catch (e) {
      return {
        'success': false,
        'message': 'Failed to connect to server',
      };
    }
  }
}
