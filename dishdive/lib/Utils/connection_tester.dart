import 'package:dio/dio.dart';
import 'package:dishdive/Utils/api_config.dart';

class ConnectionTester {
  static Future<void> testBackendConnection() async {
    final dio = Dio();
    
    try {
      print('🧪 Testing backend connection...');
      print('🧪 Base URL: ${ApiConfig.baseUrl}');
      
      // Test basic connectivity
      final response = await dio.get('${ApiConfig.baseUrl}/GetUsers');
      print('✅ Backend is reachable!');
      print('✅ Status: ${response.statusCode}');
      
    } catch (e) {
      print('❌ Backend connection failed!');
      print('❌ Error: $e');
      
      if (e is DioException) {
        print('❌ DioException type: ${e.type}');
        if (e.response != null) {
          print('❌ Response status: ${e.response?.statusCode}');
          print('❌ Response data: ${e.response?.data}');
        }
      }
    }
  }
  
  static Future<void> testRegisterEndpoint() async {
    final dio = Dio();
    
    try {
      print('🧪 Testing register endpoint with simple data...');
      
      // Test with simple form data (no file)
      final response = await dio.post(
        ApiConfig.registerEndpoint,
        data: FormData.fromMap({
          'user_name': 'test_user',
          'password_hash': 'test_password',
        }),
        options: Options(
          validateStatus: (status) => true, // Accept any status code
        ),
      );
      
      print('🧪 Register endpoint response:');
      print('🧪 Status: ${response.statusCode}');
      print('🧪 Data: ${response.data}');
      
    } catch (e) {
      print('❌ Register endpoint test failed!');
      print('❌ Error: $e');
    }
  }
}
