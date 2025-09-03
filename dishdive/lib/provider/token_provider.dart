import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

class TokenProvider extends ChangeNotifier {
  String? _token;
  int? _userId;

  String? get token => _token;
  int? get userId => _userId;

  // Initialize and load token from SharedPreferences
  Future<void> loadToken() async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    _token = prefs.getString('auth_token');
    _userId = prefs.getInt('user_id');
    notifyListeners();
  }

  // Set token and save to SharedPreferences
  Future<void> setToken(String token, int userId) async {
    _token = token;
    _userId = userId;
    
    SharedPreferences prefs = await SharedPreferences.getInstance();
    await prefs.setString('auth_token', token);
    await prefs.setInt('user_id', userId);
    
    notifyListeners();
  }

  // Clear token and remove from SharedPreferences
  Future<void> clearToken() async {
    _token = null;
    _userId = null;
    
    SharedPreferences prefs = await SharedPreferences.getInstance();
    await prefs.remove('auth_token');
    await prefs.remove('user_id');
    
    notifyListeners();
  }

  // Check if user is authenticated
  bool get isAuthenticated => _token != null && _token!.isNotEmpty;
}
