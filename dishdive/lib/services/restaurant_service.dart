import 'package:dio/dio.dart';
import 'package:dishdive/Utils/api_config.dart';
import 'package:dishdive/models/restaurant_menu_item.dart';

class RestaurantService {
  final Dio _dio = Dio();

  /// Fetches menu items for a specific restaurant
  Future<List<RestaurantMenuItem>> getRestaurantMenu(int restaurantId, int userId, String token) async {
    try {
      final response = await _dio.get(
        ApiConfig.getRestaurantMenuEndpoint(restaurantId),
        queryParameters: {'userID': userId},
        options: Options(
          headers: ApiConfig.authHeaders(token),
        ),
      );

      if (response.statusCode == 200) {
        final List<dynamic> data = response.data;
        return data.map((json) => RestaurantMenuItem.fromJson(json)).toList();
      } else {
        throw Exception('Failed to load restaurant menu: ${response.statusCode}');
      }
    } on DioException catch (e) {
      if (e.response != null) {
        throw Exception('Failed to load restaurant menu: ${e.response?.statusCode} - ${e.response?.data}');
      } else {
        throw Exception('Network error: ${e.message}');
      }
    } catch (e) {
      throw Exception('Unexpected error: $e');
    }
  }

  /// Adds a dish to user's favorites
  Future<bool> addFavorite(int userId, int dishId, String token) async {
    try {
      final response = await _dio.post(
        ApiConfig.addFavoriteEndpoint,
        data: {
          'user_id': userId,
          'dish_id': dishId,
        },
        options: Options(
          headers: ApiConfig.authHeaders(token),
        ),
      );

      return response.statusCode == 200;
    } on DioException catch (e) {
      print('Error adding favorite: ${e.message}');
      return false;
    } catch (e) {
      print('Unexpected error adding favorite: $e');
      return false;
    }
  }

  /// Removes a dish from user's favorites
  Future<bool> removeFavorite(int userId, int dishId, String token) async {
    try {
      final response = await _dio.delete(
        ApiConfig.removeFavoriteEndpoint,
        data: {
          'user_id': userId,
          'dish_id': dishId,
        },
        options: Options(
          headers: ApiConfig.authHeaders(token),
        ),
      );

      return response.statusCode == 200;
    } on DioException catch (e) {
      print('Error removing favorite: ${e.message}');
      return false;
    } catch (e) {
      print('Unexpected error removing favorite: $e');
      return false;
    }
  }
}
