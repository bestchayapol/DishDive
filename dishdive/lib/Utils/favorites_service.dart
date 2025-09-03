import 'package:dio/dio.dart';
import 'package:dishdive/Utils/api_config.dart';

class FavoritesService {
  static Future<bool> addToFavorites(String token, int userId, int dishId) async {
    try {
      Dio dio = Dio();
      final response = await dio.post(
        ApiConfig.addFavoriteEndpoint,
        data: {
          'user_id': userId,
          'dish_id': dishId,
        },
        options: Options(headers: ApiConfig.authHeaders(token)),
      );

      return response.statusCode == 200;
    } catch (e) {
      print('Error adding to favorites: $e');
      return false;
    }
  }

  static Future<bool> removeFromFavorites(String token, int userId, int dishId) async {
    try {
      Dio dio = Dio();
      final response = await dio.delete(
        ApiConfig.removeFavoriteEndpoint,
        data: {
          'user_id': userId,
          'dish_id': dishId,
        },
        options: Options(headers: ApiConfig.authHeaders(token)),
      );

      return response.statusCode == 200;
    } catch (e) {
      print('Error removing from favorites: $e');
      return false;
    }
  }

  static Future<List<Map<String, dynamic>>> getFavorites(String token, int userId) async {
    try {
      Dio dio = Dio();
      final response = await dio.get(
        ApiConfig.getFavoriteDishesEndpoint(userId),
        options: Options(headers: ApiConfig.authHeaders(token)),
      );

      if (response.statusCode == 200) {
        final List<dynamic> favoritesData = response.data;
        return favoritesData.map((dish) => {
          'dish_id': dish['dish_id'],
          'name': dish['dish_name'] ?? 'Unknown Dish',
          'percent': (dish['sentiment_score'] ?? 0.0).round(),
          'tags': dish['cuisine'] ?? 'Unknown',
          'imageUrl': dish['image_link'] ?? '',
          'prominentFlavor': dish['prominent_flavor'],
        }).toList();
      }
      return [];
    } catch (e) {
      print('Error fetching favorites: $e');
      return [];
    }
  }
}
