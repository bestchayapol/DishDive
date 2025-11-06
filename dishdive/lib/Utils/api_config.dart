import 'package:flutter/foundation.dart'
    show kIsWeb, kReleaseMode, defaultTargetPlatform, TargetPlatform;

class ApiConfig {
  // Base URL for the backend API. Prefer configuring at run/build time:
  // flutter run --dart-define=BACKEND_BASE=http://dishdive.sit.kmutt.ac.th:3000
  static const _env = String.fromEnvironment('BACKEND_BASE');

  // Change this to your deployed URL
  static const _prod = 'http://dishdive.sit.kmutt.ac.th:3000';

  static String get baseUrl {
    if (_env.isNotEmpty) return _env;
    if (kReleaseMode) return _prod; // APK default
    if (kIsWeb) return 'http://localhost:8080';
    if (defaultTargetPlatform == TargetPlatform.android)
      return 'http://10.0.2.2:8080';
    return 'http://localhost:8080';
  }

  // ================== Authentication Endpoints ==================
  static String get loginEndpoint => '$baseUrl/Login';
  static String get registerEndpoint => '$baseUrl/Register';

  // ================== User Management Endpoints ==================
  static String get getCurrentUserEndpoint => '$baseUrl/GetCurrentUser';
  static String get getUsersEndpoint => '$baseUrl/GetUsers';

  // User Profile Endpoints (require UserID parameter)
  static String getUserByUserIdEndpoint(int userId) =>
      '$baseUrl/GetUserByUserId/$userId';
  static String get getUserByTokenEndpoint => '$baseUrl/GetUserByToken';
  static String getProfileOfCurrentUserByUserIdEndpoint(int userId) =>
      '$baseUrl/GetProfileOfCurrentUserByUserId/$userId';
  static String getEditUserProfileByUserIdEndpoint(int userId) =>
      '$baseUrl/GetEditUserProfileByUserId/$userId';
  static String patchEditUserProfileByUserIdEndpoint(int userId) =>
      '$baseUrl/PatchEditUserProfileByUserId/$userId';

  // ================== Storage Endpoints ==================
  static String get uploadFileEndpoint => '$baseUrl/upload';

  // ================== Food Endpoints ==================
  static String get searchRestaurantsByDishEndpoint =>
      '$baseUrl/SearchRestaurantsByDish';
  static String get getRestaurantListEndpoint => '$baseUrl/GetRestaurantList';
  static String getRestaurantMenuEndpoint(int resId) =>
      '$baseUrl/GetRestaurantMenu/$resId';
  static String getRestaurantLocationsEndpoint(int resId) =>
      '$baseUrl/GetRestaurantLocations/$resId';
  static String getDishDetailEndpoint(int dishId) =>
      '$baseUrl/GetDishDetail/$dishId';
  static String getFavoriteDishesEndpoint(int userId) =>
      '$baseUrl/GetFavoriteDishes/$userId';
  static String get addFavoriteEndpoint => '$baseUrl/AddFavorite';
  static String get removeFavoriteEndpoint => '$baseUrl/RemoveFavorite';
  static String get addOrUpdateLocationEndpoint =>
      '$baseUrl/AddOrUpdateLocation';

  // ================== Recommendation Endpoints ==================
  // New unified settings endpoints
  static String getUserSettingsEndpoint(int userId) =>
      '$baseUrl/GetUserSettings/$userId';
  static String updateUserSettingsEndpoint(int userId) =>
      '$baseUrl/UpdateUserSettings/$userId';

  static String getDishReviewPageEndpoint(int dishId) =>
      '$baseUrl/GetDishReviewPage/$dishId';
  static String get submitReviewEndpoint => '$baseUrl/SubmitReview';
  static String getRecommendedDishesEndpoint(int userId) =>
      '$baseUrl/GetRecommendedDishes/$userId';

  // ================== Headers ==================
  static Map<String, String> jsonHeaders = {'Content-Type': 'application/json'};

  static Map<String, String> authHeaders(String token) => {
    'Authorization': 'Bearer $token',
    'Content-Type': 'application/json',
  };

  static Map<String, String> multipartHeaders(String token) => {
    'Authorization': 'Bearer $token',
  };

  // ================== HTTP Methods Helper ==================
  static const String get = 'GET';
  static const String post = 'POST';
  static const String patch = 'PATCH';
  static const String delete = 'DELETE';

  // ================== Environment Configuration ==================
  // Kept for reference; prefer using BACKEND_BASE. These aren’t used when baseUrl is provided via dart-define.
  static const bool isDevelopment = true;
  static const String developmentUrl = 'http://10.0.2.2:8080';
  static const String productionUrl =
      'https://api.dishdive.com'; // Replace with actual production URL
  static String get environmentUrl =>
      isDevelopment ? developmentUrl : productionUrl;
}
