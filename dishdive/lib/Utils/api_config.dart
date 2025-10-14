class ApiConfig {
  // Base URL for the backend API. Prefer configuring at run/build time:
  // flutter run --dart-define=BACKEND_BASE=http://dishdive.sit.kmutt.ac.th:3000
  // Defaults to Android emulator loopback if not provided.
  static const String baseUrl = String.fromEnvironment(
    'BACKEND_BASE',
    defaultValue: 'http://10.0.2.2:8080',
  );

  // ================== Authentication Endpoints ==================
  static const String loginEndpoint = '$baseUrl/Login';
  static const String registerEndpoint = '$baseUrl/Register';

  // ================== User Management Endpoints ==================
  static const String getCurrentUserEndpoint = '$baseUrl/GetCurrentUser';
  static const String getUsersEndpoint = '$baseUrl/GetUsers';

  // User Profile Endpoints (require UserID parameter)
  static String getUserByUserIdEndpoint(int userId) =>
      '$baseUrl/GetUserByUserId/$userId';
  static const String getUserByTokenEndpoint = '$baseUrl/GetUserByToken';
  static String getProfileOfCurrentUserByUserIdEndpoint(int userId) =>
      '$baseUrl/GetProfileOfCurrentUserByUserId/$userId';
  static String getEditUserProfileByUserIdEndpoint(int userId) =>
      '$baseUrl/GetEditUserProfileByUserId/$userId';
  static String patchEditUserProfileByUserIdEndpoint(int userId) =>
      '$baseUrl/PatchEditUserProfileByUserId/$userId';

  // ================== Storage Endpoints ==================
  static const String uploadFileEndpoint = '$baseUrl/upload';

  // ================== Food Endpoints ==================
  static const String searchRestaurantsByDishEndpoint =
      '$baseUrl/SearchRestaurantsByDish';
  static const String getRestaurantListEndpoint = '$baseUrl/GetRestaurantList';
  static String getRestaurantMenuEndpoint(int resId) =>
      '$baseUrl/GetRestaurantMenu/$resId';
  static String getRestaurantLocationsEndpoint(int resId) =>
      '$baseUrl/GetRestaurantLocations/$resId';
  static String getDishDetailEndpoint(int dishId) =>
      '$baseUrl/GetDishDetail/$dishId';
  static String getFavoriteDishesEndpoint(int userId) =>
      '$baseUrl/GetFavoriteDishes/$userId';
  static const String addFavoriteEndpoint = '$baseUrl/AddFavorite';
  static const String removeFavoriteEndpoint = '$baseUrl/RemoveFavorite';
  static const String addOrUpdateLocationEndpoint =
      '$baseUrl/AddOrUpdateLocation';

  // ================== Recommendation Endpoints ==================
  // New unified settings endpoints
  static String getUserSettingsEndpoint(int userId) =>
      '$baseUrl/GetUserSettings/$userId';
  static String updateUserSettingsEndpoint(int userId) =>
      '$baseUrl/UpdateUserSettings/$userId';

  static String getDishReviewPageEndpoint(int dishId) =>
      '$baseUrl/GetDishReviewPage/$dishId';
  static const String submitReviewEndpoint = '$baseUrl/SubmitReview';
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
